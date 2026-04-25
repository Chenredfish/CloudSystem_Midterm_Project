import os
from .block import append_transaction_raw, get_all_blocks, get_block_count, init_ledger, _ledger_path


def get_balance(account: str, base=None):
    """
    Scan all blocks and compute balance.
    Returns int balance, or None if account has never appeared in any transaction.
    """
    base = base or _ledger_path()
    blocks = get_all_blocks(base)
    received = 0
    sent = 0
    found = False

    for block in blocks:
        for tx in block["transactions"]:
            parts = [p.strip() for p in tx.split(",")]
            if len(parts) != 3:
                continue
            sender, receiver, amount_str = parts
            try:
                amount = int(amount_str)
            except ValueError:
                continue
            if receiver == account:
                received += amount
                found = True
            if sender == account:
                sent += amount
                found = True

    return (received - sent) if found else None


def account_exists(account: str, base=None) -> bool:
    return get_balance(account, base) is not None


def transfer(sender: str, receiver: str, amount: int, base=None) -> dict:
    """
    Execute a transfer with file-lock protection.
    Returns {"success": bool, "message": str, "block_num": int|None, ...}
    """
    base = base or _ledger_path()
    os.makedirs(base, exist_ok=True)
    lock_path = os.path.join(base, ".lock")

    import fcntl  # POSIX only; available in Docker (Linux)

    with open(lock_path, "w") as lock_f:
        fcntl.flock(lock_f, fcntl.LOCK_EX)
        try:
            if get_block_count(base) == 0:
                init_ledger(base)

            if amount <= 0:
                return {"success": False, "message": "金額必須大於 0", "block_num": None}

            sender_balance = get_balance(sender, base)
            if sender_balance is None:
                return {"success": False, "message": f"帳戶不存在: {sender}", "block_num": None}
            if sender_balance < amount:
                return {
                    "success": False,
                    "message": f"餘額不足（{sender} 目前餘額: {sender_balance}）",
                    "block_num": None,
                }

            tx_str = f"{sender}, {receiver}, {amount}"
            block_num, new_block = append_transaction_raw(tx_str, base)
            return {
                "success": True,
                "message": "轉帳成功",
                "block_num": block_num,
                "new_block_created": new_block,
                "transaction": tx_str,
            }
        finally:
            fcntl.flock(lock_f, fcntl.LOCK_UN)
