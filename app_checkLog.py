#!/usr/bin/env python3
"""Usage: python app_checkLog.py <account>"""
import sys
from ledger import get_log

if len(sys.argv) != 2:
    print("Usage: python app_checkLog.py <account>")
    sys.exit(1)

account = sys.argv[1]
log = get_log(account)

if not log:
    print(f"帳戶 {account} 無任何交易紀錄")
    sys.exit(0)

print(f"帳戶 {account} 的交易紀錄（共 {len(log)} 筆）：")
print("-" * 50)
for entry in log:
    role_label = {"sender": "付款", "receiver": "收款", "both": "自轉"}.get(entry["role"], "")
    print(f"  Block #{entry['block_num']:04d}  [{role_label}]  {entry['transaction']}")
