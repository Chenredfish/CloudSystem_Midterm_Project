# 分散式共享帳本系統

> 雲端系統期中專題 | 2026 Spring

以 Docker 容器技術實作具備區塊鏈概念的**分散式帳本系統**，三個獨立節點各自持有完整帳本副本，透過 HTTP 協議即時同步，並提供 CLI 腳本與 React Web UI 兩種操作介面。

---

## 評分對應

| 項目 | 配分 | 對應功能 |
|------|------|---------|
| 執行 6 次轉帳（觸發新區塊） | 20% | `app_transaction.py` / 網頁「執行轉帳」 |
| 查詢帳戶餘額 | 10% | `app_checkMoney.py` / 網頁「餘額查詢」 |
| 帳本完整性驗證 + angel 獎勵 | 20% | `app_checkChain.py` / 網頁「驗證/修復」 |
| 竄改後偵測錯誤 | 10% | `scripts/tamper.py` + 驗證 |
| 進階功能（分散式同步 + GUI + 跨節點驗證）| 40% | 三項全做，見下方 |

---

## 系統架構

```
[docker-compose]
  ├── node1 (host port 5001)
  ├── node2 (host port 5002)
  └── node3 (host port 5003)
        各 node 內部結構：
          ├── Flask API      帳本讀寫 + 節點間同步 + 靜態檔案 serve
          ├── React + MUI    前端 build 產物，Flask 直接 serve
          └── Named Volume   client1_data / client2_data / client3_data
                             （三個 volume 物理隔離，資料不共享）

節點間同步：寫入後 POST /sync/block 推送給所有已知 peer
```

---

## 功能清單

### 基礎功能（CLI 腳本）

| 腳本 | 用途 |
|------|------|
| `app_checkMoney.py <帳戶>` | 查詢餘額（掃描全部區塊計算） |
| `app_checkLog.py <帳戶>` | 列出所有交易歷史 |
| `app_transaction.py <付款> <收款> <金額>` | 執行轉帳，寫入區塊並推送 peer |
| `app_checkChain.py <帳戶>` | 驗證鏈完整性；通過則 angel 轉 10 元給指定帳戶 |

### 進階功能（加分項目）

| 功能 | 說明 |
|------|------|
| **真分散式同步** | 三節點各自 named volume，HTTP 推送，先到先得衝突策略 |
| **React Web GUI** | 登入頁 + 帳本總覽 / 轉帳 / 餘額 / 驗證修復，角色分流（admin / user）|
| **跨節點完整性驗證** | 比對所有節點 hash，多數決（2/3）自動修復少數派節點 |
| **動態節點加入（F1）** | 運行中新增 node4，管理員核准後自動廣播並同步完整鏈 |
| **帳戶管理系統（F2）** | 密碼 / 凍結 / 稽核日誌，密碼本節點驗證，凍結全網同步 |

---

## 技術選型

| 項目 | 選擇 | 理由 |
|------|------|------|
| 語言 | Python 3 + React | 熟悉技術，React + MUI 前端效果佳 |
| 容器 | docker-compose 一鍵啟動 | demo 穩定，助教易重現 |
| 帳本儲存 | 各自獨立 named volume | 真分散，物理隔離不共用 |
| 並發保護 | `fcntl.flock` 檔案鎖 | POSIX 標準，業界實踐 |
| 區塊格式 | 純文字 `.txt`，5 筆一塊 | 符合規格，人眼可讀 |
| 餘額計算 | 每次掃描全部區塊 | Bitcoin UTXO 掃描思路，正統做法 |
| Hash | SHA256 | 業界標準 |
| 同步衝突 | 先到先得（HTTP 409） | 邏輯清晰，符合帳本語義 |
| 跨節點修復 | 多數決（computed hash） | 可偵測「交易被竄改但 hash 未更新」 |
| 帳戶密碼同步 | 密碼只在被設定節點驗證，凍結廣播全網 | Entry-node verification，對應 Hyperledger Fabric MSP |

---

## 快速啟動

### 首次啟動 / 修改程式碼後

```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### 日常重新啟動

```bash
docker-compose up -d
docker ps
```

看到 `node1`、`node2`、`node3` 都是 `Up` 即可。

### 載入測試資料

```bash
docker exec -it node1 bash
python scripts/seed.py
exit
```

產生 100 筆交易、20 個區塊，帳戶：angel、alice、bob、carol、dave。

---

## 網頁介面

| 節點 | 網址 |
|------|------|
| node1 | http://localhost:5001 |
| node2 | http://localhost:5002 |
| node3 | http://localhost:5003 |

### 登入帳號

| 帳號 | 密碼 | 權限 |
|------|------|------|
| `admin` | `admin123` | 全功能（跨節點比對/修復/帳戶管理） |
| `user` | `user123` | 查詢 + 轉帳（需帳本帳戶密碼） |

---

## 帳本帳戶說明

帳本帳戶（alice、bob 等）與 Web 登入帳號（admin、user）是**兩套獨立系統**：

- Web 登入帳號：控制介面權限（admin / user）
- 帳本帳戶：帳本上的資金地址，由管理員設定密碼後才能付款（休眠帳戶只能收款）
- Admin 轉帳不需要帳本帳戶密碼，可操作任意帳戶

---

## 加分功能摘要

### F1：動態節點加入

新節點無需修改 docker-compose.yml，由節點運營者自行啟動後，管理員在 Web UI 核准加入，系統自動廣播並同步完整鏈。詳見 [HOWTO.md](HOWTO.md#進階功能-4動態節點加入節點運營者模式)。

### F2：帳戶管理系統

- **密碼管理**：SHA-256 儲存，在設定節點本地驗證（Entry-node model）
- **凍結 / 解凍**：廣播至所有節點，任一節點都拒絕凍結帳戶的付款
- **稽核日誌**：記錄認證、轉帳、鏈操作、節點事件等 20 種系統事件，持久化至 volume（重啟後恢復）

---

## 區塊格式

```
Previous block: <64碼 SHA256 或 64 個 0（創世區塊）>
<付款方>, <收款方>, <金額>
<付款方>, <收款方>, <金額>
...（最多 5 筆）
Next block: <下一區塊 hash，最後一塊填 None>
Hashcode: <本塊 SHA256>
```

---

## 檔案結構

```
CloudSystem_Midterm_Project/
├── docker-compose.yml          三節點定義，ports 5001/5002/5003
├── Dockerfile                  multi-stage：npm build → Python image
├── requirements.txt
├── app.py                      Flask API + sync server + React serve
├── app_checkMoney.py           CLI：查餘額
├── app_checkLog.py             CLI：查交易記錄
├── app_transaction.py          CLI：執行轉帳
├── app_checkChain.py           CLI：驗證完整性 + 領獎勵
├── ledger/
│   ├── block.py                區塊讀寫、SHA256、創世區塊
│   ├── transaction.py          轉帳邏輯、餘額掃描、fcntl.flock
│   └── chain.py                完整性驗證
├── scripts/
│   ├── seed.py                 產生測試資料 / 清空重建
│   └── tamper.py               模擬竄改（demo 用）
├── frontend/
│   ├── src/pages/              Login / Dashboard / Transfer / Balance /
│   │                           Verify / Nodes / Accounts / AuditLog
│   └── build/                  npm run build 產物（Flask serve）
├── README.md                   本文件
├── HOWTO.md                    詳細操作手冊與 demo 流程
├── PLAN.md                     技術決策文件與分階段計畫
└── AI_USAGE.md                 AI 使用紀錄
```

---

## 相關文件

| 文件 | 內容 |
|------|------|
| [HOWTO.md](HOWTO.md) | 詳細操作手冊：啟動、CLI、網頁介面、完整 demo 流程（助教版 + 老師版）|
| [PLAN.md](PLAN.md) | 技術選型決策、API 設計、分階段實作紀錄、F1/F2 設計理由 |
| [AI_USAGE.md](AI_USAGE.md) | 完整 AI 協作紀錄（開發過程中每個對話階段的討論摘要）|

---

## AI 使用說明

本專題全程使用 **Claude Code**（claude-sonnet-4-6，Anthropic）作為 AI 協作工具。
詳細的逐階段對話紀錄見 [AI_USAGE.md](AI_USAGE.md)。

**使用範疇摘要：**
- Phase 1–4：帳本核心、Flask API、React 前端、CLI 腳本的架構設計與實作
- F1：動態節點加入的設計方案討論與後端/前端實作
- F2：帳戶管理系統的分散式設計哲學討論（密碼本地化 vs 凍結全網同步）、完整實作
- 全程：文件撰寫（PLAN.md、HOWTO.md 各節）、bug 排查、git commit 管理

**AI 未介入的部分：**
- 題目理解與功能優先序判斷（由學生決定）
- 最終設計決策（AI 提供選項與分析，學生做決定）
- Demo 現場操作
