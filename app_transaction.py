#!/usr/bin/env python3
"""Usage: python app_transaction.py <sender> <receiver> <amount>"""
import sys
from ledger import transfer, init_ledger, get_block_count

if len(sys.argv) != 4:
    print("Usage: python app_transaction.py <sender> <receiver> <amount>")
    sys.exit(1)

sender   = sys.argv[1]
receiver = sys.argv[2]
try:
    amount = int(sys.argv[3])
except ValueError:
    print("金額必須為整數")
    sys.exit(1)

if get_block_count() == 0:
    init_ledger()

result = transfer(sender, receiver, amount)

if result["success"]:
    status = "（新區塊已建立）" if result.get("new_block_created") else ""
    print(f"轉帳成功：{result['transaction']}  →  Block #{result['block_num']}{status}")
else:
    print(f"轉帳失敗：{result['message']}")
    sys.exit(1)
