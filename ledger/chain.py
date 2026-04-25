from .block import get_all_blocks, compute_hash, _ledger_path


def verify_chain(base=None) -> dict:
    """
    Verify full chain integrity: hash correctness + sequential linking.
    Returns {"valid": bool, "block_count": int, "errors": list[str]}
    """
    base = base or _ledger_path()
    blocks = get_all_blocks(base)

    if not blocks:
        return {"valid": False, "block_count": 0, "errors": ["帳本為空"]}

    errors = []
    for i, block in enumerate(blocks):
        num = block["block_num"]

        # Recompute hash and compare with stored value
        expected_hash = compute_hash(block["prev_hash"], block["transactions"])
        if expected_hash != block["hash"]:
            errors.append(
                f"Block {num}: 雜湊值不符 "
                f"（預期 {expected_hash[:16]}... 實際 {(block['hash'] or '')[:16]}...）"
            )

        # Verify chain linkage
        if i == 0:
            if block["prev_hash"] != "0" * 64:
                errors.append(f"Block {num}: 創世區塊前一雜湊應為 64 個 0")
        else:
            prev = blocks[i - 1]
            expected_prev = compute_hash(prev["prev_hash"], prev["transactions"])
            if block["prev_hash"] != expected_prev:
                errors.append(
                    f"Block {num}: prev_hash 與 Block {num - 1} 的雜湊不符"
                )

    return {
        "valid": len(errors) == 0,
        "block_count": len(blocks),
        "errors": errors,
    }
