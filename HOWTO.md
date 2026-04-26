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

> 所有操作都透過 `docker exec -it <節點> bash` 進入容器內部執行，
> 讓助教直接看到容器裡的檔案結構與程式行為。

---

### 基礎功能部分（給助教看）

---

**步驟 1：確認三個節點都在運行**

```bash
docker ps
```

看到 `node1`、`node2`、`node3` 都是 `Up` 狀態。

---

**步驟 2：進入 node1，展示帳本的實際儲存方式**

```bash
docker exec -it node1 bash
```

進入容器後，依序執行：

```bash
# 確認目前位置（應在 /app）
pwd

# 列出程式檔案
ls

# 查看帳本儲存在哪裡
ls /storage/

# 印出第一個區塊的原始內容，讓助教看到純文字格式
cat /storage/block_0001.txt
```

預期輸出（創世區塊）：
```
Previous block: 0000000000000000000000000000000000000000000000000000000000000000
genesis, angel, 999999
Next block: None
Hashcode: a3f2c1...（64碼 SHA256）
```

這裡可以向助教說明：每個區塊是一個 `.txt` 純文字檔，`Previous block` 就是前一塊的 SHA256，這就是「鏈」的連接方式。

---

**步驟 3：查詢 angel 的初始餘額**

繼續在容器內：

```bash
python app_checkMoney.py angel
```

輸出：
```
angel 的餘額: 999999
```

---

**步驟 4：執行 6 次轉帳，觸發新區塊產生**

每塊最多 5 筆，第 5 筆填滿後系統自動建立新區塊：

```bash
python app_transaction.py angel alice 100
python app_transaction.py angel bob 100
python app_transaction.py angel carol 100
python app_transaction.py alice bob 30
python app_transaction.py bob carol 20
```

第 5 筆執行後，確認新區塊已產生：

```bash
ls /storage/
cat /storage/block_0002.txt
```

繼續第 6 筆：

```bash
python app_transaction.py carol alice 10
```

---

**步驟 5：查詢帳戶餘額與交易紀錄**

```bash
python app_checkMoney.py alice

python app_checkLog.py alice
```

交易紀錄輸出會顯示每筆交易的區塊編號、付款 / 收款角色。

---

**步驟 6：驗證帳本完整性 + 領獎勵**

```bash
python app_checkChain.py alice
```

輸出：
```
OK（共 N 個區塊，所有雜湊值正確）
獎勵：angel → alice 10 元  （Block #N）
```

驗證完後再查一次餘額，確認 10 元已入帳：

```bash
python app_checkMoney.py alice
```

---

**步驟 7：人為竄改區塊，展示偵測機制**

先看目前 block_0001.txt 的內容：

```bash
cat /storage/block_0001.txt
```

直接用文字指令竄改金額（把 100 改成 999）：

```bash
sed -i 's/angel, alice, 100/angel, alice, 999/' /storage/block_0001.txt
```

確認竄改成功：

```bash
cat /storage/block_0001.txt
```

再次驗證，系統應該偵測到 hash 不符：

```bash
python app_checkChain.py alice
```

輸出會列出損壞的區塊編號和錯誤原因，程式以退出碼 1 結束。

離開容器：

```bash
exit
```

---

### 進階功能部分（給老師看）

---

**進階功能 1：圖形化介面**

開啟瀏覽器 http://localhost:5001，用 `admin` / `admin123` 登入，
依序展示帳本總覽、執行轉帳、餘額查詢、驗證頁面。

---

**進階功能 2：分散式同步（三節點各自獨立儲存）**

先展示三個節點的 volume 是獨立的：

```bash
docker volume inspect client1_data
docker volume inspect client2_data
```

兩個 volume 的 `Mountpoint` 路徑不同，代表資料沒有共用。

再展示同步效果。開兩個 terminal，分別進入不同容器：

**Terminal A（node1）：**
```bash
docker exec -it node1 bash
python app_transaction.py angel dave 500
ls /storage/
```

**Terminal B（node2）：**
```bash
docker exec -it node2 bash
ls /storage/
python app_checkLog.py dave
```

node2 的 `/storage/` 應該已經同步到這筆交易，且 `dave` 的紀錄也查得到。

---

**進階功能 3：跨節點完整性驗證 + 多數決修復**

**第一步：竄改 node1 的區塊**

```bash
docker exec -it node1 bash
sed -i 's/angel, dave, 500/angel, dave, 1/' /storage/block_0002.txt
cat /storage/block_0002.txt
exit
```

**第二步：用網頁介面展示比對與修復**

開啟 http://localhost:5001，以 `admin` 登入，進入「驗證 / 修復」：

1. 按「執行驗證」→ 顯示失敗，列出損壞的區塊
2. 按「比對所有節點」→ 顯示 node1 的 block hash 與 node2/node3 不同
3. 按「執行修復」→ 顯示「已修復區塊：2」
4. 再按「執行驗證」→ 顯示通過

**第三步：回到容器確認修復結果**

```bash
docker exec -it node1 bash
cat /storage/block_0002.txt
```

金額應該已被還原為 `500`，hash 也恢復正確。

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
