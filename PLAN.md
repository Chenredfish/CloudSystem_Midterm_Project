# 專案執行計畫

**Deadline:** 2026-04-29（現場 demo + 上傳 e-learning）

---

## 最終系統架構

```
[docker-compose]
  ├── node1 (port 5001)  ──┐
  ├── node2 (port 5002)  ──┼──  HTTP /sync  互推區塊
  └── node3 (port 5003)  ──┘
       每個 node:
         ├── Flask API  (帳本讀寫 + 節點間同步 + React 靜態 serve)
         ├── React + Material UI  (build 完放在 /static)
         └── named volume  (獨立帳本 client1_data / 2 / 3)
```

---

## 確認的技術決策

| 項目 | 決策 |
|------|------|
| 語言 | Python 3 + React |
| 容器 | docker-compose，各節點獨立 named volume |
| 儲存路徑 | 環境變數 `LEDGER_PATH`，預設 `/storage` |
| 並發保護 | `fcntl.flock` 檔案鎖 |
| 創世區塊前一雜湊 | 64 個 0 |
| 最後區塊 Next block | `None` |
| angel 初始化 | `genesis, angel, 999999` 寫入第一個區塊 |
| 餘額計算 | 每次掃描所有區塊（正統做法） |
| checkChain 獎勵 | 呼叫 app_transaction.py |
| 同步機制 | 寫入後 POST /sync/block 推給其他兩節點 |
| 衝突策略 | 先到先得，HTTP 409 讓後來者重試 |
| 跨節點修復 | 多數決（2/3 一致覆蓋少數節點） |
| 前端 | React + Material UI，npm run build 由 Flask serve |
| Auth | 輕量 session，管理員 / 普通用戶兩種角色 |

---

## 檔案結構

```
CloudSystem_Midterm_Project/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── app.py                  # Flask 主程式：API + sync server + serve React build
├── ledger/
│   ├── __init__.py
│   ├── block.py            # 區塊讀寫、SHA256、創世區塊
│   ├── transaction.py      # 轉帳驗證、餘額計算、fcntl 鎖
│   └── chain.py            # 完整性驗證、多數決修復
├── scripts/
│   ├── seed.py             # 產生測試資料 / 清空重建
│   └── tamper.py           # demo 用：竄改指定節點的區塊
├── frontend/               # React 專案根目錄
│   ├── package.json
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Login.jsx
│   │   │   ├── Dashboard.jsx   # 區塊列表 + 近期交易
│   │   │   ├── Transfer.jsx    # 轉帳表單
│   │   │   ├── Balance.jsx     # 餘額查詢
│   │   │   └── Verify.jsx      # 驗證 + 修復（管理員限定）
│   │   └── App.jsx
│   └── build/              # npm run build 輸出，Flask 從這裡 serve
└── README.md
```

---

## API 設計

### 帳本 API（對外）

| Method | Path | 說明 | 權限 |
|--------|------|------|------|
| POST | `/api/login` | 登入，回傳 session | 無 |
| POST | `/api/logout` | 登出 | 登入後 |
| GET | `/api/blocks` | 取得所有區塊內容 | 普通用戶 |
| GET | `/api/balance/<account>` | 查詢餘額 | 普通用戶 |
| POST | `/api/transfer` | 執行轉帳 | 普通用戶 |
| GET | `/api/chain/verify` | 驗證本節點帳本完整性 | 普通用戶 |
| POST | `/api/chain/compare` | 跨節點比對 | 管理員 |
| POST | `/api/chain/repair` | 多數決修復 | 管理員 |

### 節點同步 API（內部）

| Method | Path | 說明 |
|--------|------|------|
| POST | `/sync/block` | 接收其他節點推送的區塊更新 |
| GET | `/sync/blocks` | 提供本節點完整區塊資料（供比對用） |

---

## 分階段執行計畫

### Phase 1 — 帳本核心 + Docker 骨架
- [x] `ledger/block.py`：區塊讀寫、SHA256、創世區塊建立
- [x] `ledger/transaction.py`：轉帳邏輯、餘額掃描、`fcntl.flock`
- [x] `ledger/chain.py`：完整性驗證
- [x] `Dockerfile`
- [x] `docker-compose.yml`（三節點獨立 volume，ports 5001/5002/5003）
- [x] 驗證：三個 container 各自寫各自的帳本，互不干擾

### Phase 2 — Flask API + 節點間同步
- [x] `app.py` 基礎路由（/api/transfer、/api/balance、/api/blocks）
- [x] `/sync/block`、`/sync/blocks` 端點
- [x] 寫入後自動推送給其他兩節點的邏輯
- [x] `/api/chain/verify`、`/api/chain/compare`、`/api/chain/repair`
- [x] 多數決修復邏輯（使用 computed hash，可偵測竄改內容但未改 Hashcode 的情境）
- [x] 輕量 session auth（hardcode 兩組帳密：admin/admin123、user/user123）

### Phase 3 — React 前端
- [x] create-react-app + Material UI 安裝
- [x] Login 頁面
- [x] Dashboard（區塊列表 + 近期交易）
- [x] Transfer 表單
- [x] Balance 查詢
- [x] Verify / Repair 頁面（管理員限定）
- [x] `npm run build` 輸出整合進 Flask（multi-stage Dockerfile）

### Phase 4 — 工具腳本 + 細節
- [ ] `scripts/seed.py`（產生 100 筆 / 清空重建）
- [ ] `scripts/tamper.py`（竄改指定節點指定區塊）
- [ ] Logger 設定（`logging` 模組，不同等級 color coding）
- [ ] Error message 補全（餘額不足、帳戶不存在、鏈結錯誤）

### Phase 5 — 收尾 + Demo 準備
- [ ] Demo 步驟文件（README 更新）
- [ ] 架構圖
- [ ] 完整 demo 流程演練

---

## Demo 流程（正式版）

### 段落一：基礎功能（給助教）
1. `docker-compose up` 啟動，`docker ps` 展示三節點
2. `seed.py` 展示已有 100 筆交易 / 20 個區塊
3. 執行 6 次轉帳 → 新區塊（第 21 個）自動產生
4. 查詢一個帳戶餘額
5. `app_checkChain.py`（或 Web UI 按鈕）→ 完整性通過 → angel 給 10 元
6. `tamper.py` 竄改 → 再次驗證 → 偵測到錯誤

### 段落二：進階功能（給老師）
7. 展示三節點各自獨立帳本（`docker exec node1 ls /storage`）
8. 在 node1 執行轉帳 → node2、node3 自動同步（即時展示）
9. `tamper.py` 竄改 node1 → 跨節點比對 → 多數決修復 → node1 帳本還原
10. React Web UI 走一遍所有功能

---

## 備註

- 中文帳戶名稱（測試人頭1...）：所有檔案讀寫用 `encoding="utf-8"`
- B1 並發鎖說明：`fcntl.flock` 是 POSIX 標準，業界通用，可在 demo 說明
- B5 餘額掃描說明：同 Bitcoin UTXO 掃描思路，100 筆交易足夠快
- C1c-2 修復展示：tamper 後先展示不一致狀態，再觸發 repair，讓修復過程可見
