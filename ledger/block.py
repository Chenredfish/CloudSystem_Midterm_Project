import os
import hashlib
import glob

TRANSACTIONS_PER_BLOCK = 5


def _ledger_path():
    return os.environ.get("LEDGER_PATH", "/storage")


def _block_path(block_num, base=None):
    base = base or _ledger_path()
    return os.path.join(base, f"block_{block_num:04d}.txt")


def compute_hash(prev_hash: str, transactions: list) -> str:
    content = prev_hash + "\n" + "\n".join(transactions)
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def parse_block_file(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()
    result = {"prev_hash": None, "transactions": [], "next_hash": None, "hash": None}
    for line in lines:
        if line.startswith("Previous block: "):
            result["prev_hash"] = line[16:]
        elif line.startswith("Next block: "):
            val = line[12:]
            result["next_hash"] = None if val == "None" else val
        elif line.startswith("Hashcode: "):
            result["hash"] = line[10:]
        elif line.strip():
            result["transactions"].append(line.strip())
    return result


def write_block_file(block_num: int, prev_hash: str, transactions: list, next_hash=None, base=None) -> str:
    base = base or _ledger_path()
    os.makedirs(base, exist_ok=True)
    hash_val = compute_hash(prev_hash, transactions)
    lines = [f"Previous block: {prev_hash}"]
    lines.extend(transactions)
    lines.append(f"Next block: {next_hash or 'None'}")
    lines.append(f"Hashcode: {hash_val}")
    with open(_block_path(block_num, base), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return hash_val


def init_ledger(base=None):
    base = base or _ledger_path()
    os.makedirs(base, exist_ok=True)
    if not os.path.exists(_block_path(1, base)):
        write_block_file(1, "0" * 64, ["genesis, angel, 999999"], base=base)


def get_block_count(base=None) -> int:
    base = base or _ledger_path()
    files = glob.glob(os.path.join(base, "block_*.txt"))
    return len(files)


def read_block(block_num: int, base=None):
    base = base or _ledger_path()
    path = _block_path(block_num, base)
    if not os.path.exists(path):
        return None
    b = parse_block_file(path)
    b["block_num"] = block_num
    return b


def get_all_blocks(base=None) -> list:
    base = base or _ledger_path()
    count = get_block_count(base)
    blocks = []
    for i in range(1, count + 1):
        b = read_block(i, base)
        if b:
            blocks.append(b)
    return blocks


def _update_next_pointer(block_num: int, next_hash: str, base=None):
    base = base or _ledger_path()
    b = read_block(block_num, base)
    if b:
        write_block_file(block_num, b["prev_hash"], b["transactions"], next_hash=next_hash, base=base)


def append_transaction_raw(tx_str: str, base=None) -> tuple:
    """
    Add transaction to the open block. Create new block if current is full.
    Returns (block_num, new_block_created).
    Caller must hold the file lock before calling this.
    """
    base = base or _ledger_path()
    count = get_block_count(base)
    if count == 0:
        init_ledger(base)
        count = 1

    latest = read_block(count, base)
    if len(latest["transactions"]) < TRANSACTIONS_PER_BLOCK:
        latest["transactions"].append(tx_str)
        write_block_file(count, latest["prev_hash"], latest["transactions"], next_hash=latest["next_hash"], base=base)
        return count, False
    else:
        sealed_hash = latest["hash"]
        new_num = count + 1
        new_hash = write_block_file(new_num, sealed_hash, [tx_str], base=base)
        _update_next_pointer(count, new_hash, base)
        return new_num, True
