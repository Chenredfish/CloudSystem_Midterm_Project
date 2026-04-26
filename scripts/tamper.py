#!/usr/bin/env python3
"""
tamper.py — 竄改指定區塊的指定交易金額（demo 示範用）

竄改後 Hashcode 不更新，執行 verify 時系統將偵測到雜湊不符。

Usage:
  docker exec node1 python scripts/tamper.py <block_num> <tx_index> <new_amount>

  block_num  : 要竄改的區塊編號（從 1 開始）
  tx_index   : 要竄改的交易索引（從 0 開始，0 = 第一筆）
  new_amount : 竄改後的金額

Example:
  docker exec node1 python scripts/tamper.py 2 0 1
  → 將 block 2 的第 1 筆交易金額改為 1，Hashcode 保持舊值
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ledger.block import _ledger_path, _block_path, read_block


def show_block(block_num: int):
    base = _ledger_path()
    block = read_block(block_num, base)
    if block is None:
        print(f"找不到 Block {block_num}")
        return
    print(f"\nBlock {block_num} 目前內容：")
    for i, tx in enumerate(block["transactions"]):
        print(f"  [{i}] {tx}")
    print(f"  Hashcode: {(block['hash'] or '')[:24]}...")


def tamper(block_num: int, tx_index: int, new_amount: int):
    base = _ledger_path()
    path = _block_path(block_num, base)

    if not os.path.exists(path):
        print(f"錯誤：找不到 Block {block_num}（{path}）")
        sys.exit(1)

    block = read_block(block_num, base)
    txs = block["transactions"]

    if tx_index >= len(txs):
        print(f"錯誤：Block {block_num} 只有 {len(txs)} 筆交易（索引 0–{len(txs)-1}）")
        sys.exit(1)

    original = txs[tx_index]
    parts = [p.strip() for p in original.split(",")]
    if len(parts) != 3:
        print(f"錯誤：交易格式不正確：{original!r}")
        sys.exit(1)

    sender, receiver, _ = parts
    tampered = f"{sender}, {receiver}, {new_amount}"

    # 直接替換檔案內容，不更新 Hashcode
    with open(path, encoding="utf-8") as f:
        content = f.read()

    if original not in content:
        print(f"錯誤：在檔案中找不到交易字串 {original!r}")
        sys.exit(1)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content.replace(original, tampered, 1))

    print(f"竄改 Block {block_num}，第 {tx_index} 筆交易：")
    print(f"  原始 → {original}")
    print(f"  竄改 → {tampered}")
    print(f"  Hashcode 未更新：執行 verify 時將偵測到雜湊不符")


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1].lstrip("-").isdigit():
        show_block(int(sys.argv[1]))
        sys.exit(0)

    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(1)

    try:
        block_num  = int(sys.argv[1])
        tx_index   = int(sys.argv[2])
        new_amount = int(sys.argv[3])
    except ValueError:
        print("錯誤：block_num、tx_index、new_amount 都必須是整數")
        sys.exit(1)

    if block_num < 1 or tx_index < 0 or new_amount < 0:
        print("錯誤：block_num >= 1，tx_index >= 0，new_amount >= 0")
        sys.exit(1)

    show_block(block_num)
    print()
    tamper(block_num, tx_index, new_amount)
