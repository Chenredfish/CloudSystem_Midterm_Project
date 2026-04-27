# AI 使用紀錄

本文件記錄本專題開發過程中與 AI 工具的完整協作歷程。

**使用工具：** Claude Code（model: claude-sonnet-4-6，Anthropic）
**使用方式：** VS Code 擴充套件內的互動式對話，AI 直接讀寫專案檔案、執行 git commit

---

## 第一階段：初始設計決策（2026-04-24）

**對話主題：** 從零開始確認系統設計方向

**討論內容：**
學生帶著助教發的作業規格（README.md 原始版），與 AI 逐題討論每個設計選項：
- 語言選擇（Python 3 vs 其他）
- 容器管理方式（docker-compose vs 手動 docker run）
- 帳本掛載方式：三個方案中選「各自獨立 named volume」，理由是做真正的分散式同步才有說服力
- 並發保護：選 `fcntl.flock`，AI 說明這是 POSIX 業界標準
- 創世區塊 prev_hash 填 64 個 0
- 餘額計算：每次掃描全部區塊（Bitcoin UTXO 思路），學生確認這是正統做法
- 決定三個進階功能全做（分散式同步 + GUI + 跨節點驗證）

**AI 輸出：**
- 填寫 README.md 設計選單（checkbox 形式），記錄所有已確認選項
- 初始 code 骨架（`fbeb699`）

**相關 commits：** `bc60c4c`、`fbeb699`、`a0de20e`

---

## 第二階段：Phase 1 & 2 實作（2026-04-25 上午）

**對話主題：** 帳本核心 + Flask API + Docker 骨架

**討論內容：**
- 制定 PLAN.md 分階段計畫，明確每個 Phase 的交付物
- 確認區塊格式（Previous block / Hashcode / Next block 欄位）
- 確認 angel 初始化方式：在第一個區塊寫入 `genesis, angel, 999999`
- 確認最後未滿區塊的 Next block 填 `None`
- 確認 checkChain 獎勵機制：通過後 angel 轉 10 元給執行者

**AI 輸出：**
- `ledger/block.py`：區塊讀寫、SHA256、創世區塊建立
- `ledger/transaction.py`：轉帳邏輯、餘額掃描、`fcntl.flock`
- `ledger/chain.py`：完整性驗證
- `app.py`：Flask API（/api/transfer、/api/balance、/api/blocks）
- `/sync/block`、`/sync/blocks`：節點間同步端點
- 多數決修復邏輯（使用 computed hash，可偵測「交易被改但 hash 未更新」的竄改）
- `docker-compose.yml`（三節點獨立 volume，ports 5001/5002/5003）
- `Dockerfile`
- `PLAN.md` 初版

**相關 commits：** `ed917cd`、`e01f48f`、`054a6d9`

---

## 第三階段：Phase 3 React 前端（2026-04-25 下午 – 2026-04-26 上午）

**對話主題：** 前端架構與所有頁面實作

**討論內容：**
- 確認前端技術棧：React + Material UI（熟悉技術，demo 視覺效果好）
- 確認 build 整合方式：`npm run build` 靜態產物由 Flask serve（不另開 container）
- 確認需要的頁面與各頁面功能範圍
- 確認 login / session 機制（輕量 Flask session，hardcode 兩組帳密）
- 確認 admin / user 角色差異（管理員多看到 Verify repair、未來的節點管理等）

**AI 輸出：**
- `frontend/src/pages/Login.jsx`
- `frontend/src/pages/Dashboard.jsx`（區塊列表 + 交易展開）
- `frontend/src/pages/Transfer.jsx`
- `frontend/src/pages/Balance.jsx`
- `frontend/src/pages/Verify.jsx`（驗證 + compare + repair，admin 限定部分）
- `frontend/src/App.js`（BrowserRouter + Drawer 導覽 + auth state）
- Multi-stage Dockerfile（Stage 1: `node` npm build；Stage 2: `python` copy build）
- CORS 設定、`/api/me` 端點

**相關 commits：** `83b2d26`、`86605d8`、`973b34c`、`9aa9145`、`7fe12e3`

---

## 第四階段：Phase 4 工具腳本 + 加分功能設計決策（2026-04-26 晚上）

**對話主題：** CLI 腳本實作、logging、加分功能設計討論

**討論內容：**

*CLI 腳本：*
- 確認四支腳本的介面規格（引數格式、輸出格式）
- 學生要求 `app_checkChain.py` 接受帳戶名稱作為領獎帳戶

*加分功能 F1（動態節點加入）設計討論：*
- 學生希望模擬「節點運營者啟動新節點」情境，而非在 docker-compose 預先定義
- 討論 peer 清單的儲存方式：記憶體（重啟歸零）vs 持久化
- 確認設計：記憶體暫存，理由是「鏈靠區塊持久化，peer 清單是動態網路拓撲」
- 確認三步驟加入流程：新節點 → admin 核准 → 廣播 + 全量同步

*加分功能 F2（帳戶管理）設計討論：*
- 比較三種方案：ACL 清單、私鑰、帳戶密碼
- 選定「帳戶密碼」方案，類比 Hyperledger Fabric MSP 角色
- 確認休眠帳戶（無密碼）只能收款不能付款
- 確認 admin 免密碼驗證（緊急情況下需要能操作任意帳戶）
- 確認凍結機制：即使有密碼也無法付款

**AI 輸出：**
- `app_checkMoney.py`、`app_checkLog.py`、`app_transaction.py`、`app_checkChain.py`
- `scripts/seed.py`（可清空重建，產生 100 筆 / 20 個區塊）
- `scripts/tamper.py`（竄改指定區塊的指定交易）
- Color-coded logging（`_ColorFormatter`）
- PLAN.md 加分功能設計決議章節（F1、F2 完整規格）
- HOWTO.md 初版 demo 流程

**相關 commits：** `24424a6`、`9c4875a`、`0f4646f`、`6cf498f`、`3854946`、`0e2f783`、`34d89d0`、`a7a2d20`

---

## 第五階段：Phase 4 修復 + F1 動態節點實作（2026-04-27 上午）

**對話主題：** bug 修復 + F1 完整後端/前端

**討論內容與問題排查：**
- 學生發現：seed.py 直接呼叫 ledger 模組寫區塊後，block 沒有 push 給 peer nodes
- 分析原因：直接寫帳本繞過了 Flask 的 `push_block_to_peers`
- 解決方案：seed.py 改成透過 Flask HTTP API 呼叫（`POST /api/transfer`），讓 push 自然發生
- 修復 block sync 的 next_hash 更新邏輯（peer 收到同一個 block 的更新版本時要接受）
- 修復 Dockerfile 沒有安裝 `curl`（container 內 health check 用到）
- 修正 HOWTO.md 的 curl 指令：說明容器內部用 5000，host 用 5001/5002/5003

**F1 實作：**
- `KNOWN_PEERS` in-memory list（初始值來自環境變數 `PEERS`）
- `GET /api/nodes`：列出所有 peer + health check
- `POST /api/nodes/approve`：核准加入 → 廣播 `/nodes/notify` → 傳 peer 清單給新節點 `/nodes/welcome`
- `POST /nodes/notify`：接收新 peer 通知，更新本節點 KNOWN_PEERS
- `POST /nodes/welcome`：接收完整 peer 清單，初始化並觸發 full sync
- `GET /api/nodes` 前端：Nodes.jsx，節點卡片 + 健康燈號 + 待審核橘色區塊

**相關 commits：** `25c1414`、`def7487`、`0212857`、`a603670`、`744b356`、`8fc1c5e`、`09d36f1`、`b6fd691`、`e5425e1`、`c6da120`

---

## 第六階段：F2 帳戶管理系統完整實作（2026-04-27 下午）

**對話主題：** F2 後端 + 前端 + 分散式設計問題排查

**實作過程：**
AI 以 git 可回溯為原則，每完成一個獨立單元就 commit：
1. `9899342`：F2 基礎設施（ACCOUNT_PASSWORDS、FROZEN_ACCOUNTS、AUDIT_LOG、audit()、account_state.json 讀寫）
2. `a019d35`：後端 API（/api/admin/accounts、/api/admin/account/password、freeze、unfreeze、audit）
3. `9264d45`：Transfer.jsx 加入密碼欄位（non-admin 才顯示）
4. `fd001d6`：Accounts.jsx（帳戶管理表格、設密碼 Dialog、凍結按鈕）
5. `f3f6464`：AuditLog.jsx + App.js 更新（新增路由與導覽項目）
6. `19a99e4`：HOWTO.md 加入進階功能 5、6 demo 步驟

**問題排查：**
- 學生回報：以 admin 登入後所有功能都回傳「需要管理員權限」
- 診斷過程：在容器內用 curl 直接測試 → 後端正常，問題在前端
- 根本原因：瀏覽器有 Docker rebuild 前的舊 session cookie，角色資訊已過期
- 解決方法：清除 localhost:5001 的 cookie 後重新登入

**重大設計問題發現與解決：**

*問題 1：帳號密碼不跨節點*
學生提出：如果 Admin 只在 node1 設定 alice 的密碼，alice 連到 node2 就無法轉帳，這是嚴重問題嗎？

*問題 2：廣播密碼 hash 的安全疑慮*
初稿方案是把密碼 hash 廣播給所有節點。學生指出：「這樣任何一個節點被入侵就等同於所有用戶的密碼都洩漏，分散式帳本的保護性質消失」。

*設計討論（對話過程）：*
- AI 提出三種方案：（1）密碼廣播，（2）只同步凍結，（3）完全不同步
- 學生追問：為什麼 Hyperledger Fabric 是 entry-node model？用白話解釋
- AI 解釋：每個組織節點自己驗自己的用戶，peer 信任背書不要求重看憑證；就像海關只驗自己國家的護照，不要求其他國也驗一遍
- 學生確認選擇方案 2（密碼本地，凍結廣播）

**AI 輸出：**
- `c34cad4`：實作跨節點 freeze 廣播 + account_state.json 持久化
- `02cd8bd`：重構，明確分離密碼（本地）與凍結（全網），並補充 docstring 說明設計原因
- PLAN.md 新增「F2 帳戶狀態的跨節點同步策略」設計決議章節（含 Hyperledger Fabric MSP 類比）
- HOWTO.md 補充密碼節點本地化警告與建議使用情境

**相關 commits：** `9899342`、`a019d35`、`9264d45`、`fd001d6`、`f3f6464`、`19a99e4`、`c34cad4`、`02cd8bd`

---

## 第七階段：持久化補完 + 稽核日誌擴充（2026-04-27 晚上）

**對話主題：** 資料持久化設計審查 + 稽核日誌全面擴充

**討論內容：**

*儲存機制總覽討論：*
學生詢問「哪些資料在哪些情況下會消失」，AI 整理出以下表格：

| 資料 | 儲存 | docker stop | docker-compose down -v |
|------|------|-------------|------------------------|
| 區塊鏈帳本 | volume | 保留 | 消失 |
| 帳戶密碼 | 記憶體 + JSON | 保留 | 消失 |
| 凍結清單 | 記憶體 + JSON | 保留 | 消失 |
| 稽核日誌 | 記憶體 only | **消失** | 消失 |
| PENDING_NODES | 記憶體 only | **消失** | 消失 |
| KNOWN_PEERS | 記憶體 only | 歸零（從 env 恢復） | 歸零 |

學生決定：PENDING_NODES 和 AUDIT_LOG 應持久化（不能因重啟就消失）。
KNOWN_PEERS：學生確認「即使重啟後歸零也沒問題，需要時自然會被刷新」，維持記憶體設計。

*稽核日誌擴充：*
學生認為稽核日誌記錄的事件太少（原本只有 5 種），希望涵蓋「所有程式內部的錯誤通知」。

**AI 輸出：**
- `76b2152`：PENDING_NODES 和 AUDIT_LOG 持久化至 account_state.json
- `fda8e7b`：稽核日誌擴充至 20 種事件（login、transfer 各種拒絕原因、verify/compare/repair chain、block sync 衝突/失敗、節點加入/核准、full sync 成功/失敗等）
- `8ca3bea`：PLAN.md 更新（F2 全部勾選完成，稽核日誌事件表補完）

**相關 commits：** `76b2152`、`fda8e7b`、`8ca3bea`

---

## 第八階段：Phase 5 收尾文件（2026-04-27 晚上）

**對話主題：** README 重寫、AI 使用紀錄、demo 流程整理

**討論內容：**
- 學生確認不需要架構圖（移除 Phase 5 的架構圖任務）
- 討論現有 README.md（是設計問卷格式）需要改為正式專題說明文件
- 學生指出 AI 使用紀錄需要涵蓋所有對話，建議從 git log 重建

**AI 輸出：**
- `README.md`：完整重寫為正式專題說明文件（系統架構、功能清單、技術選型、快速啟動）
- `AI_USAGE.md`：本文件（依 git 時間線重建所有 7 個對話階段）
- `HOWTO.md`：更新稽核日誌說明（現已持久化）
- `PLAN.md`：移除架構圖需求，Phase 5 標記完成

---

## 總結

| 統計項目 | 數值 |
|----------|------|
| 開發天數 | 4 天（2026-04-24 到 2026-04-27）|
| Git commits | 42 個 |
| AI 協作對話階段 | 8 個 |
| AI 主導實作的程式碼 | app.py、ledger/、frontend/src/ 全部頁面、所有 CLI 腳本、docker-compose.yml |
| 學生主導的決策 | 功能範圍選擇、設計方案取捨、安全性疑慮提出、demo 策略 |

**AI 協作的核心價值（此專題中）：**
1. 快速將設計決策轉化為可運行程式碼
2. 在分散式系統設計上提供業界參考（Hyperledger Fabric、Bitcoin UTXO）
3. 協助維持 git 歷史可讀性（每個功能單元一個 commit）
4. 文件與程式碼同步更新（PLAN / HOWTO 隨實作更新）

**學生在協作中提出的關鍵問題（推動設計進化）：**
- 「seed.py 執行後為什麼其他節點沒有資料？」→ 發現直接寫帳本繞過了 push
- 「其他節點怎麼知道密碼？」→ 引發分散式帳本密碼同步設計討論
- 「把密碼廣播給所有節點，這不就讓分散式帳本失去保護性質了嗎？」→ 推動 entry-node verification 設計
- 「哪些資料在哪些情況下會消失？」→ 觸發完整持久化補完
