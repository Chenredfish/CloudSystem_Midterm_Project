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

### 節點同步 API（內部，無 auth）

| Method | Path | 說明 |
|--------|------|------|
| POST | `/sync/block` | 接收其他節點推送的區塊更新 |
| GET | `/sync/blocks` | 提供本節點完整區塊資料（供比對用） |
| POST | `/nodes/notify` | 接收新 peer 加入通知，更新本節點記憶體 peer 清單 |
| POST | `/nodes/welcome` | 接收完整 peer 清單（專供新加入節點初始化連線用） |

### 節點管理 API（管理員）

| Method | Path | 說明 | 權限 |
|--------|------|------|------|
| GET | `/api/nodes` | 列出已知節點、健康狀態、各節點區塊數 | 管理員 |
| POST | `/api/nodes/approve` | 批准新節點加入，觸發廣播與 peer 清單交換 | 管理員 |

### 帳戶管理 API（管理員）

| Method | Path | 說明 | 權限 |
|--------|------|------|------|
| GET | `/api/admin/accounts` | 所有帳本帳戶：餘額、密碼狀態（啟用/休眠）、凍結狀態 | 管理員 |
| POST | `/api/admin/account/password` | 設定或重設帳本帳戶密碼（空字串 = 重置為休眠） | 管理員 |
| POST | `/api/admin/freeze` | 凍結指定帳本帳戶（無法轉出） | 管理員 |
| POST | `/api/admin/unfreeze` | 解凍指定帳本帳戶 | 管理員 |
| GET | `/api/admin/audit` | 取得最近操作記錄（時間、操作者、動作、結果） | 管理員 |

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
- [x] `scripts/seed.py`（產生 100 筆 / 清空重建，透過本地 Flask API 執行以確保 peer 同步）
- [x] `scripts/tamper.py`（竄改指定節點指定區塊）
- [x] Logger 設定（`logging` 模組，不同等級 color coding）
- [x] Error message 補全（餘額不足、帳戶不存在、鏈結錯誤）

### Phase 6 — 加分功能實作

#### F1：動態節點加入
- [ ] 後端：記憶體 `KNOWN_PEERS` 清單（初始值來自 `PEERS` 環境變數）
- [ ] 後端：`GET /api/nodes`（列出 peer + 逐一 health check）
- [ ] 後端：`POST /api/nodes/approve`（加入 peer → 廣播 `/nodes/notify` 給所有已知節點 → 傳完整 peer 清單給新節點 `/nodes/welcome` → 觸發新節點 `GET /sync/blocks` 同步鏈）
- [ ] 後端：`POST /nodes/notify`（接收新 peer 通知，更新本節點 `KNOWN_PEERS`）
- [ ] 後端：`POST /nodes/welcome`（接收完整 peer 清單，初始化 `KNOWN_PEERS` 並立即同步區塊鏈）
- [ ] 前端：Admin「節點管理」頁面（節點卡片 + 健康燈號 + 區塊數 + 批准輸入框）
- [ ] `push_block_to_peers` 改用動態 `KNOWN_PEERS`（而非固定 `PEERS` 環境變數）

#### F2-密碼：帳戶密碼系統
- [ ] 後端：記憶體 `ACCOUNT_PASSWORDS`（dict）+ `FROZEN_ACCOUNTS`（set）
- [ ] 後端：`POST /api/admin/account/password`（設定/重設密碼，密碼以 SHA256 儲存）
- [ ] 後端：修改 `transfer` 端點——依序檢查凍結 → admin 免驗 → 休眠攔截 → 密碼比對
- [ ] 前端：`Transfer.jsx` 新增「帳戶密碼」輸入欄位
- [ ] 前端：Admin 帳戶管理頁面新增「設定密碼」表單

#### F2-B：帳戶管理
- [ ] 後端：`GET /api/admin/accounts`（掃描所有區塊取得帳戶清單，附加密碼狀態與凍結狀態）
- [ ] 後端：`POST /api/admin/freeze` + `POST /api/admin/unfreeze`
- [ ] 前端：Admin 帳戶管理頁面（表格：帳戶名、餘額、狀態 badge、操作按鈕）

#### F2-C：Audit Log
- [ ] 後端：`AUDIT_LOG = deque(maxlen=200)`，定義 `audit(action, actor, detail, result)` helper
- [ ] 後端：在 login、logout、transfer、verify、approve node、set password、freeze/unfreeze 各處插入 audit 記錄
- [ ] 後端：`GET /api/admin/audit`（回傳 audit buffer，管理員限定）
- [ ] 前端：Admin「操作記錄」頁面（時間線列表，顯示時間、操作者、動作、結果）

### Phase 5 — 收尾 + Demo 準備
- [ ] Demo 步驟文件（README 更新，含 node4 加入流程指令）
- [ ] 架構圖（含動態節點加入示意）
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

> 以下兩個功能為期中加分項目的確定設計規格，已根據設計問答討論完成決策。

---

### 功能 F1：動態新增節點（節點運營者模型）

**核心概念**：docker-compose.yml 代表**現有網路基礎設施**，不是所有可能節點的清單。新節點由「節點運營者」自行啟動，管理員負責審核並批准其加入網路。這對應 Hyperledger Fabric 等聯盟鏈的節點准入機制。

#### 決定：Peer 清單儲存方式
**記憶體暫存**（不持久化）。每次啟動容器都是全新的節點，這才符合區塊鏈的語義：鏈的資料靠區塊檔案持久化，Peer 清單則是動態建立的網路拓撲。若要保留舊節點的連線關係，重啟舊容器即可（而非從 peers.json 讀回）。

#### 決定：加入流程（三步驟）

**步驟一：節點運營者自行啟動節點**

代表「新組織在自己的伺服器上安裝並啟動節點軟體」。Demo 時在 terminal 手動執行：

```bash
docker run -d \
  --name node4 \
  --network cloudsystem_midterm_project_ledger_net \
  -p 5004:5000 \
  -v client4_data:/storage \
  -e NODE_ID=node4 \
  -e LEDGER_PATH=/storage \
  -e PEERS="" \
  cloudsystem_midterm_project-node1
```

此時 node4 已啟動，但與現有網路完全隔離——它沒有任何 peer，也沒有區塊資料。

**步驟二：管理員在 Web UI 批准加入**

管理員進入 node1 介面（http://localhost:5001）的「節點管理」頁面，輸入 `http://node4:5000`，點「批准加入」。

後端執行三件事：
1. 將 node4 加入自身記憶體的 peer 清單
2. 廣播給 node2、node3：「node4 已加入，請更新你們的 peer 清單」
3. 傳送目前所有 peer 位址給 node4，讓 node4 也認識整個網路

**步驟三：node4 自動同步區塊鏈**

node4 收到通知後，立即向 node1 發送 `GET /sync/blocks`，拉取完整區塊鏈。同步完成後，node4 開始正常接收交易和區塊推送。

```bash
# 驗證 node4 已加入並同步完成
curl http://localhost:5004/health
# → {"status": "ok", "node": "node4", "block_count": 21}

curl http://localhost:5001/api/nodes
# → {"nodes": ["http://node2:5000", "http://node3:5000", "http://node4:5000"]}
```

#### 新增 API

| Method | Path | 說明 | 權限 |
|--------|------|------|------|
| GET | `/api/nodes` | 列出目前已知的所有節點及其健康狀態 | 管理員 |
| POST | `/api/nodes/approve` | 批准新節點加入，觸發廣播與同步 | 管理員 |
| POST | `/nodes/notify` | 內部端點：接收新 peer 通知（節點間使用） | 無 auth |
| POST | `/nodes/welcome` | 內部端點：接收完整 peer 清單（給新加入節點用） | 無 auth |

#### 前端新增
- Admin 側欄新增「節點管理」頁面
- 顯示所有已知節點、各節點健康狀態（綠/紅燈）、區塊數量
- 輸入欄位 + 「批准加入」按鈕

---

### 功能 F2：強化 Admin 與一般用戶的差異

#### 決定：帳本帳戶控制權限（帳戶密碼模型）

採用**方案三：帳戶密碼**，以密碼替代私鑰的概念。每個帳本帳戶有一組獨立密碼，由 Admin 設定後發給帳戶持有人；轉帳時需提供寄款帳戶的密碼，否則拒絕。

**核心規則：**
- 每個帳本帳戶的密碼**獨立且互不共用**（alice 的密碼只能用於 alice 帳戶）
- 沒有密碼的帳戶為**休眠（Dormant）狀態**：只能收款，無法轉出
- Admin 免密碼驗證，可從任意帳戶轉帳（管理員特權）
- 凍結帳戶無法轉出（即使有正確密碼）

**隱式帳戶建立的處理：**
維持現有設計，轉帳到不存在的帳戶會自動建立該帳戶，但新帳戶自動進入休眠狀態。垃圾帳戶攻擊因此失效——就算建立了 1000 個休眠帳戶，Admin 不發密碼就沒人能動用它們，鏈式洗錢在第一跳也會被阻斷。

```python
# app.py 記憶體結構（重啟後清空，符合「新容器 = 新開始」的設計）
ACCOUNT_PASSWORDS = {}    # {"alice": "hashed_pw", "bob": "hashed_pw"}
FROZEN_ACCOUNTS   = set() # {"carol"}
```

**Transfer 驗證流程：**
```
1. 寄款帳戶是否凍結？      → 是 → 拒絕（帳戶已凍結）
2. 登入身份是 admin？      → 是 → 跳過密碼驗證，直接執行
3. 帳戶是否有密碼（啟用）？ → 否 → 拒絕（帳戶未啟用，請聯繫管理員）
4. 密碼是否符合？          → 否 → 拒絕（密碼錯誤）
5. 餘額是否足夠？          → 否 → 拒絕（餘額不足）
6. 執行轉帳 ✅
```

**對應真實區塊鏈的概念：**
密碼對應私鑰，Admin 是「憑證發行機構（CA）」，休眠帳戶對應「無人持有私鑰的地址」。可在 demo 中說明此設計對應 Hyperledger Fabric 的 MSP（成員服務提供者）角色。

新增 API：

| Method | Path | 說明 | 權限 |
|--------|------|------|------|
| POST | `/api/admin/account/password` | 設定或重設某帳本帳戶的密碼（空字串 = 重置為休眠） | 管理員 |

#### 決定：管理員獨有功能（A + B + C 全做）

**A. 節點管理**（與 F1 整合）
- 查看所有已知節點、健康狀態燈號、區塊數量
- 批准新節點加入網路

**B. 帳戶管理**
- 全帳戶餘額 + 狀態總覽（休眠 / 啟用 / 凍結）
- 設定/重設帳戶密碼（開戶 / 帳戶交接）
- 凍結/解凍帳戶

新增 API：

| Method | Path | 說明 | 權限 |
|--------|------|------|------|
| GET | `/api/admin/accounts` | 所有帳本帳戶：餘額、密碼狀態（啟用/休眠）、凍結狀態 | 管理員 |
| POST | `/api/admin/freeze` | 凍結指定帳本帳戶 | 管理員 |
| POST | `/api/admin/unfreeze` | 解凍指定帳本帳戶 | 管理員 |

**C. Audit Log**
- 記錄登入/登出、轉帳、驗證、密碼設定、凍結/解凍等所有操作，含時間戳與操作者
- in-memory circular buffer（最近 200 筆），重啟後清空
- 管理員可在 UI 查看完整操作歷史，一般用戶不可見

新增 API：

| Method | Path | 說明 | 權限 |
|--------|------|------|------|
| GET | `/api/admin/audit` | 取得最近操作記錄（時間、操作者、動作、結果） | 管理員 |

#### 決定：Verify 獎勵機制

保留現有「驗證成功得 10 元」機制，對應 Proof-of-Work 礦工獎勵概念。後續可擴充：成功同步新節點獎勵、第 N 筆交易里程碑獎勵等。

---

### 實作優先序

| 優先 | 項目 | 預估工作量 |
|------|------|-----------|
| 1 | F1 後端：PEERS 清單 + `/api/nodes` + `/api/nodes/approve` + 廣播/同步邏輯 | 中 |
| 2 | F1 前端：Admin 節點管理頁面（清單 + 健康燈號 + 批准輸入框） | 小 |
| 3 | F2-密碼 後端：`ACCOUNT_PASSWORDS` + transfer 密碼驗證 + 休眠/凍結邏輯 | 中 |
| 4 | F2-密碼 前端：Transfer 加密碼欄位、Admin 密碼設定 UI | 小 |
| 5 | F2-B 後端：`/api/admin/accounts` + freeze/unfreeze API | 小 |
| 6 | F2-B 前端：Admin 帳戶管理頁面（總覽 + 操作按鈕） | 小 |
| 7 | F2-C 後端：audit buffer + 記錄插入點 + `/api/admin/audit` | 小 |
| 8 | F2-C 前端：Audit Log 頁面（時間線列表） | 小 |

---

## 備註

- 中文帳戶名稱（測試人頭1...）：所有檔案讀寫用 `encoding="utf-8"`
- B1 並發鎖說明：`fcntl.flock` 是 POSIX 標準，業界通用，可在 demo 說明
- B5 餘額掃描說明：同 Bitcoin UTXO 掃描思路，100 筆交易足夠快
- C1c-2 修復展示：tamper 後先展示不一致狀態，再觸發 repair，讓修復過程可見
