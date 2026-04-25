import os
import threading
import logging
from functools import wraps

import requests
from flask import Flask, jsonify, request, session

from ledger import (
    init_ledger, get_all_blocks, read_block, get_block_count,
    transfer, get_balance, verify_chain, compute_hash,
)
from ledger.block import write_block_file

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")

NODE_ID = os.environ.get("NODE_ID", "unknown")
PEERS = [p.strip() for p in os.environ.get("PEERS", "").split(",") if p.strip()]

# ---------------------------------------------------------------------------
# Hardcoded users  (admin: full access, user: transfer/query only)
# ---------------------------------------------------------------------------
USERS = {
    "admin": {"password": "admin123", "role": "admin"},
    "user":  {"password": "user123",  "role": "user"},
}

# ---------------------------------------------------------------------------
# Auth decorators
# ---------------------------------------------------------------------------
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "username" not in session:
            return jsonify({"error": "請先登入"}), 401
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "username" not in session:
            return jsonify({"error": "請先登入"}), 401
        if session.get("role") != "admin":
            return jsonify({"error": "需要管理員權限"}), 403
        return f(*args, **kwargs)
    return decorated

# ---------------------------------------------------------------------------
# Sync helper
# ---------------------------------------------------------------------------
def push_block_to_peers(block: dict):
    """Push one block to all peers (runs in background thread)."""
    for peer in PEERS:
        try:
            r = requests.post(f"{peer}/sync/block", json=block, timeout=3)
            if r.status_code == 409:
                logger.warning(f"Sync conflict with {peer} at block {block['block_num']}")
            else:
                logger.info(f"Synced block {block['block_num']} to {peer} → {r.status_code}")
        except Exception as e:
            logger.error(f"Sync to {peer} failed: {e}")


def async_push(block_num: int, also_prev: bool = False):
    """Fire-and-forget push of block(s) to peers."""
    block = read_block(block_num)
    if block:
        threading.Thread(target=push_block_to_peers, args=(block,), daemon=True).start()
    if also_prev and block_num > 1:
        prev = read_block(block_num - 1)
        if prev:
            threading.Thread(target=push_block_to_peers, args=(prev,), daemon=True).start()

# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------
@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.json or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")
    user = USERS.get(username)
    if not user or user["password"] != password:
        return jsonify({"error": "帳號或密碼錯誤"}), 401
    session["username"] = username
    session["role"] = user["role"]
    logger.info(f"Login: {username}")
    return jsonify({"message": "登入成功", "role": user["role"], "username": username})


@app.route("/api/logout", methods=["POST"])
@login_required
def api_logout():
    username = session.pop("username", None)
    session.pop("role", None)
    logger.info(f"Logout: {username}")
    return jsonify({"message": "已登出"})


@app.route("/api/me")
@login_required
def api_me():
    return jsonify({"username": session["username"], "role": session["role"]})

# ---------------------------------------------------------------------------
# Ledger routes
# ---------------------------------------------------------------------------
@app.route("/api/blocks")
@login_required
def api_blocks():
    return jsonify(get_all_blocks())


@app.route("/api/balance/<account>")
@login_required
def api_balance(account):
    balance = get_balance(account)
    if balance is None:
        return jsonify({"error": f"帳戶不存在: {account}"}), 404
    return jsonify({"account": account, "balance": balance})


@app.route("/api/transfer", methods=["POST"])
@login_required
def api_transfer():
    data = request.json or {}
    sender   = data.get("sender",   "").strip()
    receiver = data.get("receiver", "").strip()
    try:
        amount = int(data.get("amount", 0))
    except (ValueError, TypeError):
        return jsonify({"error": "金額格式錯誤"}), 400

    if not sender or not receiver:
        return jsonify({"error": "sender 和 receiver 不能為空"}), 400

    result = transfer(sender, receiver, amount)
    if result["success"]:
        async_push(result["block_num"], also_prev=result.get("new_block_created", False))
        return jsonify(result), 200
    return jsonify(result), 400

# ---------------------------------------------------------------------------
# Chain routes
# ---------------------------------------------------------------------------
@app.route("/api/chain/verify")
@login_required
def api_verify():
    result = verify_chain()
    if result["valid"]:
        username = session["username"]
        reward = transfer("angel", username, 10)
        result["reward"] = reward
        if reward["success"]:
            logger.info(f"checkChain reward: angel → {username} 10")
            async_push(reward["block_num"], also_prev=reward.get("new_block_created", False))
    return jsonify(result)


@app.route("/api/chain/compare", methods=["POST"])
@admin_required
def api_compare():
    local_blocks = get_all_blocks()
    # Use COMPUTED hash so tampering (changed transactions, stale stored hash) is detected
    local_map = {
        b["block_num"]: compute_hash(b["prev_hash"], b["transactions"])
        for b in local_blocks
    }

    peer_data = {}
    for peer in PEERS:
        try:
            r = requests.get(f"{peer}/sync/blocks", timeout=5)
            peer_data[peer] = {
                b["block_num"]: compute_hash(b["prev_hash"], b["transactions"])
                for b in r.json()
            }
        except Exception as e:
            logger.error(f"Compare: can't reach {peer}: {e}")
            peer_data[peer] = None

    all_nums = set(local_map.keys())
    for d in peer_data.values():
        if d:
            all_nums |= set(d.keys())

    diffs = []
    for num in sorted(all_nums):
        local_hash = local_map.get(num)
        peer_hashes = {
            peer: (d.get(num) if d else None)
            for peer, d in peer_data.items()
        }
        all_hashes = [local_hash] + list(peer_hashes.values())
        non_null = {h for h in all_hashes if h}
        if len(non_null) > 1 or None in all_hashes:
            diffs.append({
                "block_num":   num,
                "local_hash":  local_hash,
                "peer_hashes": peer_hashes,
            })

    return jsonify({
        "consistent":  len(diffs) == 0,
        "block_count": len(local_blocks),
        "diffs":       diffs,
    })


@app.route("/api/chain/repair", methods=["POST"])
@admin_required
def api_repair():
    local_blocks = get_all_blocks()
    all_chains = {"local": {b["block_num"]: b for b in local_blocks}}

    for peer in PEERS:
        try:
            r = requests.get(f"{peer}/sync/blocks", timeout=5)
            all_chains[peer] = {b["block_num"]: b for b in r.json()}
        except Exception as e:
            logger.error(f"Repair: can't reach {peer}: {e}")

    if len(all_chains) < 2:
        return jsonify({"error": "需要至少 2 個節點才能進行多數決"}), 503

    all_nums: set = set()
    for d in all_chains.values():
        all_nums |= set(d.keys())

    repaired = []
    for num in sorted(all_nums):
        # Key: use COMPUTED hash from transactions (detects tampered data)
        versions: dict = {}
        for node, chain in all_chains.items():
            if num not in chain:
                continue
            b = chain[num]
            h = compute_hash(b["prev_hash"], b["transactions"])
            if h not in versions:
                versions[h] = {"count": 0, "block": b, "nodes": []}
            versions[h]["count"] += 1
            versions[h]["nodes"].append(node)

        if not versions:
            continue

        majority = max(versions.values(), key=lambda x: x["count"])
        local_block = all_chains["local"].get(num)
        local_computed = compute_hash(local_block["prev_hash"], local_block["transactions"]) if local_block else None

        majority_hash = compute_hash(majority["block"]["prev_hash"], majority["block"]["transactions"])
        if majority["count"] >= 2 and local_computed != majority_hash:
            b = majority["block"]
            write_block_file(b["block_num"], b["prev_hash"], b["transactions"], b.get("next_hash"))
            repaired.append(num)
            logger.warning(f"Repaired block {num} from majority {majority['nodes']}")

    return jsonify({"repaired_blocks": repaired, "repaired_count": len(repaired)})

# ---------------------------------------------------------------------------
# Internal sync routes (node-to-node, no auth)
# ---------------------------------------------------------------------------
@app.route("/sync/block", methods=["POST"])
def sync_block():
    data = request.json or {}
    block_num    = data.get("block_num")
    prev_hash    = data.get("prev_hash")
    transactions = data.get("transactions", [])
    next_hash    = data.get("next_hash")
    recv_hash    = data.get("hash")

    if not block_num or not prev_hash:
        return jsonify({"error": "缺少必要欄位"}), 400

    # Verify received block's hash
    if compute_hash(prev_hash, transactions) != recv_hash:
        return jsonify({"error": "區塊雜湊驗證失敗"}), 400

    existing = read_block(block_num)
    if existing:
        if existing["hash"] == recv_hash:
            return jsonify({"status": "already_exists"}), 200
        # Same chain position but received has more transactions → accept update
        if (existing["prev_hash"] == prev_hash
                and len(transactions) > len(existing["transactions"])):
            write_block_file(block_num, prev_hash, transactions, next_hash)
            logger.info(f"Updated block {block_num} from peer (extended)")
            return jsonify({"status": "updated"}), 200
        return jsonify({"status": "conflict", "local_hash": existing["hash"]}), 409

    write_block_file(block_num, prev_hash, transactions, next_hash)
    logger.info(f"Accepted block {block_num} from peer")
    return jsonify({"status": "ok"}), 200


@app.route("/sync/blocks")
def sync_blocks():
    return jsonify(get_all_blocks())

# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
@app.route("/health")
def health():
    return jsonify({
        "status":      "ok",
        "node":        NODE_ID,
        "block_count": get_block_count(),
    })

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logger.info(f"Node {NODE_ID} starting | ledger: {os.environ.get('LEDGER_PATH', '/storage')} | peers: {PEERS}")
    init_ledger()
    logger.info("Ledger initialized")
    app.run(host="0.0.0.0", port=5000)
