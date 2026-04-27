#!/usr/bin/env python3
"""
seed.py — 清空帳本並產生 100 筆測試交易（20 個區塊），完成後同步至所有 peer 節點

Usage:
  docker exec node1 python scripts/seed.py           # 清空重建並同步
  docker exec node1 python scripts/seed.py --status  # 只顯示目前狀態
"""
import os
import sys
import glob

import requests as req

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ledger.block import _ledger_path, get_block_count, get_all_blocks, init_ledger
from ledger.transaction import transfer

# ── 交易計畫 ────────────────────────────────────────────────────────────────
# Block 1 已有 genesis（1 筆），尚有 4 個空位 → Phase 1 補滿
INITIAL = [
    ("angel", "alice",  100_000),
    ("angel", "bob",     80_000),
    ("angel", "carol",   60_000),
    ("angel", "dave",    40_000),
]

# Blocks 2–20：每輪 5 筆 × 19 輪 = 95 筆
CYCLE = [
    ("alice", "bob",   1_000),
    ("bob",   "carol",   800),
    ("carol", "dave",    600),
    ("dave",  "alice",   400),
    ("alice", "carol",   200),
]

PLANNED = INITIAL + CYCLE * 19  # 4 + 95 = 99 筆（加上 genesis 共 100）


def count_tx() -> int:
    return sum(len(b["transactions"]) for b in get_all_blocks())


def clear():
    base = _ledger_path()
    files = sorted(glob.glob(os.path.join(base, "block_*.txt")))
    lock = os.path.join(base, ".lock")
    for f in files:
        os.remove(f)
    if os.path.exists(lock):
        os.remove(lock)
    print(f"清空 {len(files)} 個區塊檔案")


def seed():
    init_ledger()
    print("初始化完成（創世區塊已建立）\n")
    print(f"{'序號':>4}  {'寄款':6}  {'收款':6}  {'金額':>8}   區塊")
    print("─" * 48)

    for i, (sender, receiver, amount) in enumerate(PLANNED, start=1):
        result = transfer(sender, receiver, amount)
        if result["success"]:
            tag = " ←新區塊" if result.get("new_block_created") else ""
            print(f"  {i:3d}  {sender:6s}  {receiver:6s}  {amount:>8,}   #{result['block_num']}{tag}")
        else:
            print(f"  {i:3d}  ✗ {sender} → {receiver}: {result['message']}")
            sys.exit(1)

    tx = count_tx()
    blocks = get_block_count()
    print("─" * 48)
    print(f"完成：共 {tx} 筆交易，{blocks} 個區塊")


def sync_to_peers():
    """
    seed.py 直接寫檔，不經過 Flask，不會觸發 push_block_to_peers。
    此函式在 seed 完成後，手動把所有區塊推送給各 peer，
    確保三節點狀態一致，避免 compare/repair 出現錯誤的多數決結果。
    """
    peers = [p.strip() for p in os.environ.get("PEERS", "").split(",") if p.strip()]
    if not peers:
        print("\n（未設定 PEERS，跳過同步）")
        return

    blocks = get_all_blocks()
    print(f"\n同步 {len(blocks)} 個區塊至 {len(peers)} 個節點...")

    for peer in peers:
        ok = skipped = failed = 0
        for block in blocks:
            try:
                r = req.post(f"{peer}/sync/block", json=block, timeout=5)
                if r.status_code == 200:
                    ok += 1
                else:
                    # 409 conflict 或其他非 200 視為跳過（不中斷）
                    skipped += 1
            except Exception:
                failed += 1

        if failed == 0:
            print(f"  ✓ {peer}：{ok} 個更新，{skipped} 個跳過")
        else:
            print(f"  △ {peer}：{ok} 個更新，{skipped} 個跳過，{failed} 個失敗")

    print("同步完成")


def status():
    blocks = get_block_count()
    tx = count_tx()
    print(f"目前狀態：{blocks} 個區塊，{tx} 筆交易")


if __name__ == "__main__":
    if "--status" in sys.argv:
        status()
    else:
        print("=== 清空並重建帳本 ===")
        clear()
        seed()
        sync_to_peers()
