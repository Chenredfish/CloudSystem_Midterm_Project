import os
import logging
from flask import Flask, jsonify

from ledger import init_ledger, get_all_blocks, get_balance, verify_chain

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

NODE_ID = os.environ.get("NODE_ID", "unknown")


@app.route("/health")
def health():
    return jsonify({"status": "ok", "node": NODE_ID})


@app.route("/api/blocks")
def api_blocks():
    blocks = get_all_blocks()
    return jsonify(blocks)


@app.route("/api/balance/<account>")
def api_balance(account):
    balance = get_balance(account)
    if balance is None:
        return jsonify({"error": f"帳戶不存在: {account}"}), 404
    return jsonify({"account": account, "balance": balance})


@app.route("/api/chain/verify")
def api_verify():
    result = verify_chain()
    return jsonify(result)


if __name__ == "__main__":
    logger.info(f"Node {NODE_ID} starting, ledger path: {os.environ.get('LEDGER_PATH', '/storage')}")
    init_ledger()
    logger.info("Ledger initialized")
    app.run(host="0.0.0.0", port=5000)
