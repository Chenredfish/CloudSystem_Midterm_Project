#!/usr/bin/env python3
"""Usage: python app_transaction.py <sender> <receiver> <amount>"""
import sys
import requests

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

s = requests.Session()
s.post(
    "http://localhost:5000/api/login",
    json={"username": "admin", "password": "admin123"},
    timeout=5,
)
r = s.post(
    "http://localhost:5000/api/transfer",
    json={"sender": sender, "receiver": receiver, "amount": amount},
    timeout=10,
)
result = r.json()

if result.get("success"):
    status = "（新區塊已建立）" if result.get("new_block_created") else ""
    print(f"轉帳成功：{result['transaction']}  →  Block #{result['block_num']}{status}")
else:
    print(f"轉帳失敗：{result.get('message', r.text)}")
    sys.exit(1)
