#!/usr/bin/env python3
"""Usage: python app_checkChain.py <reward_account>
Verifies the entire chain. If valid, angel transfers 10 to reward_account.
"""
import sys
import requests
from ledger import verify_chain

if len(sys.argv) != 2:
    print("Usage: python app_checkChain.py <reward_account>")
    sys.exit(1)

reward_account = sys.argv[1]

result = verify_chain()

if result["valid"]:
    print(f"OK（共 {result['block_count']} 個區塊，所有雜湊值正確）")
    s = requests.Session()
    s.post(
        "http://localhost:5000/api/login",
        json={"username": "admin", "password": "admin123"},
        timeout=5,
    )
    r = s.post(
        "http://localhost:5000/api/transfer",
        json={"sender": "angel", "receiver": reward_account, "amount": 10},
        timeout=5,
    )
    reward = r.json()
    if reward.get("success"):
        print(f"獎勵：angel → {reward_account} 10 元（Block #{reward['block_num']}）")
    else:
        print(f"獎勵發放失敗：{reward.get('message', r.text)}")
else:
    print(f"帳本鏈受損，發現 {len(result['errors'])} 個錯誤：")
    for err in result["errors"]:
        print(f"  {err}")
    sys.exit(1)
