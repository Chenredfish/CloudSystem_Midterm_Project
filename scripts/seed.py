#!/usr/bin/env python3
"""
seed.py — 清空帳本並產生 100 筆測試交易（20 個區塊）

轉帳透過本地 Flask API 執行，自動同步至所有 peer 節點。

Usage:
  docker exec -it node1 bash
  python scripts/seed.py           # 清空重建
  python scripts/seed.py --status  # 只顯示目前狀態
"""
import os
import sys
import glob

import requests as req

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ledger.block import _ledger_path, get_block_count, get_all_blocks, init_ledger

# ── 交易計畫 ────────────────────────────────────────────────────────────────
# Block 1 已有 genesis（1 筆），尚有 4 個空位 → INITIAL 補滿
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
    # 直接建立本節點的創世區塊（不透過 API，因為沒有對應端點）
    init_ledger()
    print("初始化完成（創世區塊已建立）\n")
    print(f"{'序號':>4}  {'寄款':6}  {'收款':6}  {'金額':>8}   區塊")
    print("─" * 48)

    # 透過本地 Flask API 執行轉帳，讓 Flask 負責 peer 同步與所有驗證層
    s = req.Session()
    login_r = s.post(
        "http://localhost:5000/api/login",
        json={"username": "admin", "password": "admin123"},
        timeout=5,
    )
    if login_r.status_code != 200:
        print("無法登入 Flask（確認容器內 Flask 是否在 5000 port 正常運行）")
        sys.exit(1)

    for i, (sender, receiver, amount) in enumerate(PLANNED, start=1):
        r = s.post(
            "http://localhost:5000/api/transfer",
            json={"sender": sender, "receiver": receiver, "amount": amount},
            timeout=10,
        )
        result = r.json()
        if result.get("success"):
            tag = " ←新區塊" if result.get("new_block_created") else ""
            print(f"  {i:3d}  {sender:6s}  {receiver:6s}  {amount:>8,}   #{result['block_num']}{tag}")
        else:
            print(f"  {i:3d}  ✗ {sender} → {receiver}: {result.get('message', r.text)}")
            sys.exit(1)

    tx = count_tx()
    blocks = get_block_count()
    print("─" * 48)
    print(f"完成：共 {tx} 筆交易，{blocks} 個區塊")


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
