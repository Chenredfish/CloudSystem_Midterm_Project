#!/usr/bin/env python3
"""Usage: python app_checkMoney.py <account>"""
import sys
from ledger import get_balance

if len(sys.argv) != 2:
    print("Usage: python app_checkMoney.py <account>")
    sys.exit(1)

account = sys.argv[1]
balance = get_balance(account)

if balance is None:
    print(f"帳戶不存在: {account}")
    sys.exit(1)

print(f"{account} 的餘額: {balance}")
