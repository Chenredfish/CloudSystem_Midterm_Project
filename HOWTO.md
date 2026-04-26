# 操作手冊 — 分散式共享帳本系統

## 前置需求

- Docker Desktop 已安裝並**開啟運行**
- 不需要安裝 Python 或 Node.js（全部在容器內）

---

## 第一步：建立並啟動系統

### 首次啟動 / 程式碼有修改後

每次修改了 Python 程式（`app.py`、CLI 腳本、`ledger/`）或 Dockerfile，都必須重新 build image，舊容器不會自動更新：

```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

> **注意**：`docker-compose down` 只會刪除容器，不會刪除資料（volume 保留）。
> 若需要清空所有帳本資料，改用 `docker-compose down -v`。

### 日常重新啟動（程式沒有修改）

```bash
docker-compose up -d
```

這會同時啟動三個節點：

| 節點 | 網址 | 儲存位置 |
|------|------|----------|
| node1 | http://localhost:5001 | Docker volume `client1_data` |
| node2 | http://localhost:5002 | Docker volume `client2_data` |
| node3 | http://localhost:5003 | Docker volume `client3_data` |

確認容器都在跑：

```bash
docker ps
```

看到三個容器 `node1`、`node2`、`node3` 都是 `Up` 狀態即可。

---

## 第二步：確認系統健康

```bash
curl http://localhost:5001/health
curl http://localhost:5002/health
curl http://localhost:5003/health
```

正常回應：
```json
{"status": "ok", "node": "node1", "block_count": 1}
```

---

## 第三步：使用網頁介面

用瀏覽器開啟任一節點的網址，例如 **http://localhost:5001**

### 登入帳號

| 帳號 | 密碼 | 權限 |
|------|------|------|
| `admin` | `admin123` | 全功能（含跨節點比對/修復）|
| `user` | `user123` | 查詢 + 轉帳 |

### 網頁功能說明

登入後左側有四個頁面：

**帳本總覽**
- 顯示所有區塊，最新的在最上面並預設展開
- 每個區塊可以展開看到所有交易紀錄與 prev_hash
- 右上角「重新整理」按鈕重新載入

**執行轉帳**
- 填入付款方、收款方、金額，按「確認轉帳」
- 成功後顯示區塊編號，若剛好湊滿 5 筆會提示「新區塊已建立」

**餘額查詢**
- 輸入帳戶名稱按「查詢」
- 顯示目前餘額

**驗證 / 修復**
- **執行驗證**（所有人可用）：驗證本節點所有區塊的 SHA256 是否正確；通過會自動發放 10 元獎勵給目前登入的帳號
- **比對所有節點**（admin 限定）：向 node2、node3 取得區塊資料，比對 hash 是否一致，列出差異
- **執行修復**（admin 限定）：以多數決（2/3 節點一致）覆蓋本節點不一致的區塊

---

## 第四步：使用 CLI 指令

所有 CLI 操作都透過 `docker exec` 在容器內執行：

### 查詢帳戶餘額

```bash
docker exec node1 python app_checkMoney.py angel
docker exec node1 python app_checkMoney.py alice
```

### 查詢交易紀錄

```bash
docker exec node1 python app_checkLog.py angel
docker exec node1 python app_checkLog.py alice
```

輸出會顯示每筆交易的區塊編號與角色（付款 / 收款 / 自轉）。

### 執行轉帳

```bash
docker exec node1 python app_transaction.py angel alice 100
docker exec node1 python app_transaction.py alice bob 50
```

格式：`app_transaction.py <付款方> <收款方> <金額>`

### 驗證帳本完整性 + 領獎勵

```bash
docker exec node1 python app_checkChain.py alice
```

格式：`app_checkChain.py <要領獎勵的帳戶名稱>`

- 鏈結完整 → 印出 OK，angel 轉 10 元給指定帳戶
- 鏈結損壞 → 列出錯誤的區塊編號與原因，退出碼 1

---

## Demo 流程（對應評分項目）

### 基礎功能部分（給助教看）

**步驟 1：確認三個節點都在運行**

```bash
docker ps
```

**步驟 2：展示初始帳本狀態**

```bash
docker exec node1 python app_checkMoney.py angel
```

或開啟 http://localhost:5001 → 帳本總覽，展示現有區塊。

**步驟 3：執行 6 次轉帳，觸發新區塊產生**

每塊放 5 筆，第 5、10 筆交易時會自動建立新區塊：

```bash
docker exec node1 python app_transaction.py angel alice 100
docker exec node1 python app_transaction.py angel bob 100
docker exec node1 python app_transaction.py angel carol 100
docker exec node1 python app_transaction.py alice bob 30
docker exec node1 python app_transaction.py bob carol 20
# ↑ 前 5 筆湊滿 → 新區塊產生
docker exec node1 python app_transaction.py carol alice 10
# ↑ 第 6 筆，放入新區塊
```

**步驟 4：查詢帳戶餘額**

```bash
docker exec node1 python app_checkMoney.py alice
```

**步驟 5：驗證帳本 + 領獎勵**

```bash
docker exec node1 python app_checkChain.py alice
```

輸出：
```
OK（共 N 個區塊，所有雜湊值正確）
獎勵：angel → alice 10 元  （Block #N）
```

**步驟 6：人為竄改 + 偵測錯誤**

先找到區塊檔案的位置，進入容器：

```bash
docker exec -it node1 bash
ls /storage/
```

直接修改其中一個區塊（例如改金額）：

```bash
# 在容器內
sed -i 's/angel, alice, 100/angel, alice, 999/' /storage/block_0001.txt
exit
```

再次執行驗證：

```bash
docker exec node1 python app_checkChain.py alice
```

輸出會顯示 hash 不符的區塊編號，退出碼 1。

---

### 進階功能部分（給老師看）

**進階功能 1：圖形化介面**

開啟 http://localhost:5001，用 `admin` 登入，展示所有頁面操作。

**進階功能 2：分散式同步**

在 node1 執行轉帳，同時在 node2 查帳本，確認區塊已同步：

```bash
# 在 node1 轉帳
docker exec node1 python app_transaction.py angel dave 200

# 在 node2 查看（應該也有這筆交易）
docker exec node2 python app_checkLog.py dave
```

或打開兩個瀏覽器分頁，一個開 localhost:5001、一個開 localhost:5002，在 5001 轉帳後，重新整理 5002 的帳本總覽，會看到同一筆交易。

**進階功能 3：跨節點完整性驗證 + 多數決修復**

1. 竄改 node1 的某個區塊（步驟 6 的方式）
2. 用瀏覽器開啟 http://localhost:5001，以 `admin` 登入
3. 進入「驗證 / 修復」→「比對所有節點」，可以看到 node1 和 node2/node3 有 hash 差異
4. 按「執行修復」，node1 的損壞區塊會被 node2/node3 的多數決版本覆蓋
5. 再次「執行驗證」，顯示通過

---

## 停止系統

```bash
docker-compose stop
```

保留資料（volume 不刪除）。若要完全重置：

```bash
docker-compose down -v
```

`-v` 會一併刪除所有 volume（所有帳本資料歸零）。

---

## 常見問題

**Q：啟動時報錯 `port is already in use`**

有舊容器還在跑，執行：
```bash
docker-compose stop
docker-compose up -d
```

**Q：網頁開啟後顯示空白或 404**

React build 可能沒有在 image 內，重新 build：
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

**Q：轉帳失敗「帳戶不存在」**

帳戶是透過交易紀錄自動建立的（不需要事先註冊）。確認付款方曾經收過錢（有餘額）才能付款。系統初始只有 `angel` 有錢（創世區塊給了 999999 元）。

**Q：CLI 指令報錯 `can't open file '/app/app_checkMoney.py': No such file or directory`**

容器跑的是舊 image，新腳本還沒打包進去。需要重新 build：
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

**Q：CLI 指令報錯 `No module named 'ledger'`**

確認是在 `node1`/`node2`/`node3` 容器內執行，而不是在本機直接跑。
