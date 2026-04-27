import os
import threading
import logging
from functools import wraps

import requests
from flask import Flask, jsonify, request, session, send_from_directory
from flask_cors import CORS

from ledger import (
    init_ledger, get_all_blocks, read_block, get_block_count,
    transfer, get_balance, get_log, verify_chain, compute_hash,
)
from ledger.block import write_block_file

# ---------------------------------------------------------------------------
# Logging（color-coded by level）
# ---------------------------------------------------------------------------
class _ColorFormatter(logging.Formatter):
    _C = {
        logging.DEBUG:    "\033[36m",    # cyan
        logging.INFO:     "\033[32m",    # green
        logging.WARNING:  "\033[33m",    # yellow
        logging.ERROR:    "\033[31m",    # red
        logging.CRITICAL: "\033[35;1m",  # bold magenta
    }
    _R = "\033[0m"

    def format(self, record):
        return f"{self._C.get(record.levelno, '')}{super().format(record)}{self._R}"


_handler = logging.StreamHandler()
_handler.setFormatter(_ColorFormatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
logging.getLogger().addHandler(_handler)
logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = Flask(__name__, static_folder=None)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")
CORS(app, supports_credentials=True)

NODE_ID = os.environ.get("NODE_ID", "unknown")
PEERS = [p.strip() for p in os.environ.get("PEERS", "").split(",") if p.strip()]
KNOWN_PEERS: list = list(PEERS)   # mutable in-memory; grows dynamically via F1 approve flow
_peers_lock = threading.Lock()


def get_peers() -> list:
    with _peers_lock:
        return list(KNOWN_PEERS)

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
    for peer in get_peers():
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


@app.route("/api/logs/<account>")
@login_required
def api_logs(account):
    log = get_log(account)
    if not log and get_balance(account) is None:
        return jsonify({"error": f"帳戶不存在: {account}"}), 404
    return jsonify({"account": account, "count": len(log), "logs": log})


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
        return jsonify({"error": "轉出帳戶與收款帳戶不能為空"}), 400
    if sender == receiver:
        return jsonify({"error": "轉出帳戶與收款帳戶不能相同"}), 400

    # ── Phase 6 F2 validation placeholder ───────────────────────────────────
    # IMPORTANT: admin check MUST come first — it bypasses both freeze and
    # password checks. Do NOT access data["password"] before this block.
    #
    # if session.get("role") != "admin":
    #     if sender in FROZEN_ACCOUNTS:
    #         return jsonify({"error": "帳戶已凍結"}), 400
    #     if sender not in ACCOUNT_PASSWORDS:
    #         return jsonify({"error": "帳戶未啟用，請聯繫管理員"}), 400
    #     pw_hash = hashlib.sha256(data.get("password", "").encode()).hexdigest()
    #     if pw_hash != ACCOUNT_PASSWORDS[sender]:
    #         return jsonify({"error": "密碼錯誤"}), 400
    # ────────────────────────────────────────────────────────────────────────

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

    peers = get_peers()
    if not peers:
        return jsonify({"error": "此節點未設定任何 peer，無法進行跨節點比對"}), 503

    peer_data = {}
    unreachable = []
    for peer in peers:
        try:
            r = requests.get(f"{peer}/sync/blocks", timeout=5)
            peer_data[peer] = {
                b["block_num"]: compute_hash(b["prev_hash"], b["transactions"])
                for b in r.json()
            }
        except Exception as e:
            logger.error(f"Compare: can't reach {peer}: {e}")
            peer_data[peer] = None
            unreachable.append(peer)

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
        "unreachable": unreachable,
    })


@app.route("/api/chain/repair", methods=["POST"])
@admin_required
def api_repair():
    local_blocks = get_all_blocks()
    all_chains = {"local": {b["block_num"]: b for b in local_blocks}}
    peers = get_peers()

    for peer in peers:
        try:
            r = requests.get(f"{peer}/sync/blocks", timeout=5)
            all_chains[peer] = {b["block_num"]: b for b in r.json()}
        except Exception as e:
            logger.error(f"Repair: can't reach {peer}: {e}")

    if not peers:
        return jsonify({"error": "此節點未設定任何 peer，無法進行多數決修復"}), 503
    if len(all_chains) < 2:
        reachable = len(all_chains) - 1  # minus local
        return jsonify({
            "error": f"需要至少 2 個節點才能進行多數決（目前只有 {reachable} 個 peer 可連線）"
        }), 503

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
# F1 — Dynamic node management
# ---------------------------------------------------------------------------
@app.route("/api/nodes")
@admin_required
def api_nodes():
    """Return known peers with live health info."""
    nodes_info = []
    for peer in get_peers():
        try:
            r = requests.get(f"{peer}/health", timeout=2)
            d = r.json()
            nodes_info.append({
                "url": peer, "status": "online",
                "node": d.get("node"), "block_count": d.get("block_count"),
            })
        except Exception:
            nodes_info.append({"url": peer, "status": "offline", "node": None, "block_count": None})
    return jsonify({"nodes": nodes_info})


@app.route("/api/nodes/approve", methods=["POST"])
@admin_required
def api_nodes_approve():
    """Admin approves a new node URL; broadcasts to peers and welcomes the new node."""
    data = request.json or {}
    new_url = data.get("url", "").strip().rstrip("/")
    if not new_url:
        return jsonify({"error": "缺少節點 URL"}), 400

    with _peers_lock:
        if new_url in KNOWN_PEERS:
            return jsonify({"error": "該節點已在 peer 名單中"}), 409
        KNOWN_PEERS.append(new_url)
        current_peers = list(KNOWN_PEERS)

    # Broadcast new node to all existing peers
    for peer in current_peers:
        if peer == new_url:
            continue
        try:
            requests.post(f"{peer}/nodes/notify", json={"url": new_url}, timeout=3)
        except Exception as e:
            logger.warning(f"Notify {peer} of new node failed: {e}")

    # Send complete peer list + self URL to new node so it can sync
    self_url = f"http://{NODE_ID}:5000"
    welcome_peers = [p for p in current_peers if p != new_url] + [self_url]
    try:
        requests.post(f"{new_url}/nodes/welcome", json={"peers": welcome_peers}, timeout=10)
    except Exception as e:
        logger.error(f"Welcome to {new_url} failed: {e}")
        return jsonify({"error": f"節點 {new_url} 無法連線", "detail": str(e)}), 503

    logger.info(f"Approved new node: {new_url}")
    return jsonify({"status": "ok", "url": new_url, "known_peers": current_peers})


@app.route("/nodes/notify", methods=["POST"])
def nodes_notify():
    """Internal broadcast: a peer was added; update local KNOWN_PEERS."""
    data = request.json or {}
    url = data.get("url", "").strip().rstrip("/")
    if not url:
        return jsonify({"error": "缺少 url"}), 400
    with _peers_lock:
        if url not in KNOWN_PEERS:
            KNOWN_PEERS.append(url)
    logger.info(f"Peer added via notify: {url}")
    return jsonify({"status": "ok"})


@app.route("/nodes/welcome", methods=["POST"])
def nodes_welcome():
    """New node receives full peer list; initialises KNOWN_PEERS and syncs chain."""
    data = request.json or {}
    peers = data.get("peers", [])
    self_url = f"http://{NODE_ID}:5000"

    with _peers_lock:
        KNOWN_PEERS.clear()
        for p in peers:
            p = p.strip().rstrip("/")
            if p and p != self_url and p not in KNOWN_PEERS:
                KNOWN_PEERS.append(p)

    logger.info(f"Welcome received; peers now: {get_peers()}")

    def _full_sync():
        for peer in get_peers():
            try:
                r = requests.get(f"{peer}/sync/blocks", timeout=10)
                blocks = sorted(r.json(), key=lambda b: b["block_num"])
                for b in blocks:
                    if not read_block(b["block_num"]):
                        write_block_file(
                            b["block_num"], b["prev_hash"],
                            b["transactions"], b.get("next_hash"),
                        )
                logger.info(f"Full sync from {peer}: {len(blocks)} blocks written")
                return
            except Exception as e:
                logger.error(f"Full sync from {peer} failed: {e}")

    threading.Thread(target=_full_sync, daemon=True).start()
    return jsonify({"status": "ok", "peers": get_peers()})

# ---------------------------------------------------------------------------
# React static serve (activated after npm run build)
# ---------------------------------------------------------------------------
_REACT_BUILD = os.path.join(os.path.dirname(__file__), "frontend", "build")

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_react(path):
    if path.startswith("api/") or path.startswith("sync/") or path.startswith("nodes/") or path == "health":
        return jsonify({"error": "Not found"}), 404
    if os.path.exists(_REACT_BUILD):
        target = os.path.join(_REACT_BUILD, path)
        if path and os.path.exists(target):
            return send_from_directory(_REACT_BUILD, path)
        return send_from_directory(_REACT_BUILD, "index.html")
    return jsonify({"error": "Frontend not built"}), 404

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
