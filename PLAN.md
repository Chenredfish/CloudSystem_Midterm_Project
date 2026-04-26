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

## 加分功能設計決議

> 以下兩個功能為期中加分項目的候選擴充，記錄設計問題、各選項說明與推薦方向。

---

### 功能 F1：動態新增節點

**背景**：目前節點清單（PEERS）寫死在 docker-compose.yml，啟動後不可更動。真實區塊鏈（Bitcoin、Hyperledger）都支援節點動態加入，這是分散式帳本的核心特性之一。

#### Q1. 新節點加入的操作入口

| 選項 | 說明 | 推薦 |
|------|------|------|
| (A) Admin Web UI 點按鈕 | 管理員在前端輸入新節點 URL，後端廣播給所有現有節點 | ✅ |
| (B) CLI 指令 `python add_node.py <url>` | 操作感強，但 demo 時需要切 terminal | |
| (C) 新容器啟動時自動向 bootstrap 節點報到 | 最貼近真實區塊鏈，但新增一個 `/nodes/join` endpoint | ✅ |

**推薦**：(A)+(C) 組合——新容器啟動時 POST `/nodes/join` 自動報到，管理員也可在 UI 手動新增。這樣 demo 時可以展示「容器啟動 → 自動加入網路」的完整流程。

#### Q2. Peer 清單是否需要持久化

| 選項 | 說明 | 推薦 |
|------|------|------|
| 記憶體暫存 | 重啟後清空，實作最簡單 | demo 夠用 |
| volume 內 `peers.json` | 重啟後保留，更貼近真實系統 | ✅ 推薦 |

**推薦**：寫入 `/storage/peers.json`，與區塊檔案放在同一個 volume。實作成本低（10 行），但展示價值高。

#### Q3. 新節點加入後要展示的流程深度

| 選項 | 說明 | 推薦 |
|------|------|------|
| (A) 只展示新節點出現在清單中 | 工作量最小 | |
| (B) 展示「加入 → 自動拉取完整鏈 → 開始參與讀寫」 | 最有說服力，完整展示去中心化概念 | ✅ |

**推薦**：(B)。新節點啟動時若 peers.json 或啟動參數有 bootstrap 節點，自動 GET `/sync/blocks` 從其拉取完整鏈，再開始正常服務。這個流程在 demo 中可以清楚說明「區塊鏈如何讓新成員快速追上」。

#### Q4. docker-compose.yml 處理方式

**推薦**：預先定義 `node4`（port 5004）但不啟動。Demo 時執行 `docker-compose up -d node4`，node4 自動報到並同步。這樣不需要即時改 compose 檔，操作乾淨。

```
# docker-compose.yml 預留欄位（node4 預設不啟動）
node4:
  build: .
  container_name: node4
  ports:
    - "5004:5000"
  volumes:
    - client4_data:/storage
  environment:
    - LEDGER_PATH=/storage
    - NODE_ID=node4
    - BOOTSTRAP=http://node1:5000   # 啟動時自動向 node1 報到
  networks:
    - ledger_net
  profiles:
    - extra   # docker-compose --profile extra up node4 才會啟動
```

#### 實作摘要（若決定做）

- 後端新增 `GET /api/nodes`（列出已知節點）、`POST /api/nodes/join`（管理員新增）
- 啟動時若有 `BOOTSTRAP` env var，自動 POST 到 bootstrap 節點的 `/nodes/join`
- bootstrap 節點收到後廣播給所有已知 peers，讓全網都知道新節點
- 新節點同時從 bootstrap 抓取完整區塊鏈（`GET /sync/blocks`）
- 前端 Admin 頁面新增「節點管理」分頁

---

### 功能 F2：強化 Admin 與一般用戶的差異

**背景**：目前 admin 獨有功能只有 compare/repair（系統維護操作），日常使用感受不到差異。在私有鏈／聯盟鏈中，管理員負責系統治理，一般用戶只負責交易，兩者角色應有明顯界線。

#### Q5. 帳戶所有權（安全性問題）

目前任何登入用戶都可以從任意帳戶轉帳（如 `user` 登入可轉走 `angel` 的錢），這在真實系統中是安全漏洞。

| 選項 | 說明 | 推薦 |
|------|------|------|
| (A) 維持現狀 | Demo 方便，可用任意帳戶名做示範 | ✅ demo 優先 |
| (B) 登入帳號與帳本帳戶綁定 | `user` 只能從 `user` 帳戶轉出，更安全 | 若有時間再做 |

**推薦**：Demo 優先選 (A)，但在報告或口頭說明時主動提及這個設計取捨，展示你意識到這個問題，加分效果更好。

#### Q6. Admin 獨有功能方向

| 選項 | 說明 | 與 F1 的關聯 | 推薦 |
|------|------|-------------|------|
| (A) 節點管理（查看/新增節點、節點健康狀態） | 最有「系統管理員」感，與 F1 天然整合 | 直接複用 F1 的 `/api/nodes` | ✅ |
| (B) 帳戶管理（凍結帳戶、全帳戶餘額總覽） | 展示帳本治理權，無需 F1 | 獨立實作 | 次選 |
| (C) Audit Log（誰登入、誰做了什麼操作） | 展示稽核能力，與 logging 模組整合 | 獨立實作 | 補充項 |
| (D) 只強化 UI 視覺差異（管理員 badge、更多選單） | 工作量最小 | 無需後端改動 | 保底 |

**推薦**：若做 F1，(A) 幾乎免費附贈。若不做 F1，選 (B) 或 (C) 其一，效果都比 (D) 好。

#### Q7. Verify 獎勵機制（任何用戶驗證成功得 10 元）

這個設計對應真實區塊鏈的「礦工獎勵」概念，是很好的教學點。

**推薦：保留**。可在報告中說明「這模擬了 Proof-of-Work 的礦工報酬機制，驗證鏈完整性的用戶得到獎勵」，把它變成加分論述點而非缺陷。

---

### 建議實作優先序

| 優先 | 項目 | 說明 |
|------|------|------|
| 1 | F2-(A) UI 視覺分層（保底） | 不需改後端，1-2 小時完成 |
| 2 | F1 動態節點加入 | 展示價值最高，建議做到「加入+同步」流程 |
| 3 | F2-(A) 節點管理頁面 | 搭配 F1 幾乎是免費附贈的 UI |
| 4 | F2-(B) 帳戶凍結/總覽 | 若 F1 沒時間做，用這個替代 |
| 5 | F2-(C) Audit Log | 有 `logging` 模組基礎，整合成本低 |

---

## 備註

- 中文帳戶名稱（測試人頭1...）：所有檔案讀寫用 `encoding="utf-8"`
- B1 並發鎖說明：`fcntl.flock` 是 POSIX 標準，業界通用，可在 demo 說明
- B5 餘額掃描說明：同 Bitcoin UTXO 掃描思路，100 筆交易足夠快
- C1c-2 修復展示：tamper 後先展示不一致狀態，再觸發 repair，讓修復過程可見
