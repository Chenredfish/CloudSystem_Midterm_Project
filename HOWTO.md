# 操作手冊 — 分散式共享帳本系統

## 前置需求

- Docker Desktop 已安裝並**開啟運行**
- 不需要安裝 Python 或 Node.js（全部在容器內）

---

## 第一步：建立並啟動系統

### 首次啟動 / 程式碼有修改後

每次修改了 Python 程式（`app.py`、CLI 腳本、`ledger/`、`scripts/`）或 Dockerfile，都必須重新 build image：

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

進入 node1 容器：

```bash
docker exec -it node1 bash
```

在容器內確認 Flask 服務正常：

```bash
curl http://localhost:5000/health
```

正常回應：
```json
{"status": "ok", "node": "node1", "block_count": 1}
```

離開容器：

```bash
exit
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

所有 CLI 操作都在容器內執行。先進入容器：

```bash
docker exec -it node1 bash
```

以下指令皆在容器內輸入，完成後輸入 `exit` 離開。

---

### 產生測試資料（seed.py）

清空帳本並產生 100 筆交易、20 個區塊：

```bash
python scripts/seed.py
```

只查看目前狀態（不修改資料）：

```bash
python scripts/seed.py --status
```

seed.py 建立的帳戶與初始資金：

| 帳戶 | 來源 |
|------|------|
| angel | 創世區塊（999,999 元）|
| alice | angel 轉入 100,000 元 |
| bob | angel 轉入 80,000 元 |
| carol | angel 轉入 60,000 元 |
| dave | angel 轉入 40,000 元 |

之後 alice、bob、carol、dave 彼此循環轉帳，產生滿 20 個區塊。

---

### 竄改區塊（tamper.py）

查看指定區塊的交易內容：

```bash
python scripts/tamper.py 2
```

竄改 block 2 的第 0 筆交易，把金額改為 1（Hashcode 不更新）：

```bash
python scripts/tamper.py 2 0 1
```

格式：`tamper.py <區塊編號> <交易索引> <新金額>`

竄改後執行 verify 時，系統會偵測到該區塊的 hash 不符。

---

### 查詢帳戶餘額

```bash
python app_checkMoney.py angel
python app_checkMoney.py alice
```

### 查詢交易紀錄

```bash
python app_checkLog.py alice
```

輸出會顯示每筆交易的區塊編號與角色（付款 / 收款 / 自轉）。

### 執行轉帳

```bash
python app_transaction.py angel alice 100
python app_transaction.py alice bob 50
```

格式：`app_transaction.py <付款方> <收款方> <金額>`

### 驗證帳本完整性 + 領獎勵

```bash
python app_checkChain.py alice
```

格式：`app_checkChain.py <要領獎勵的帳戶名稱>`

- 鏈結完整 → 印出 OK，angel 轉 10 元給指定帳戶
- 鏈結損壞 → 列出錯誤的區塊編號與原因，退出碼 1

---

## Demo 流程（對應評分項目）

---

### 基礎功能部分（給助教看）

所有操作在 node1 容器內進行。

---

**步驟 1：確認三個節點都在運行**

```bash
docker ps
```

看到 `node1`、`node2`、`node3` 都是 `Up` 狀態後，進入 node1：

```bash
docker exec -it node1 bash
```

---

**步驟 2：產生測試資料（100 筆交易 / 20 個區塊）**

```bash
python scripts/seed.py
```

輸出會逐筆列出交易，並標示每個新區塊的建立時機。完成後確認：

```bash
python scripts/seed.py --status
```

輸出：`目前狀態：20 個區塊，100 筆交易`

---

**步驟 3：展示帳本的實際儲存方式**

```bash
ls /storage/
```

可看到 `block_0001.txt` 到 `block_0020.txt` 共 20 個檔案。

```bash
cat /storage/block_0001.txt
```

預期輸出（創世區塊）：
```
Previous block: 0000000000000000000000000000000000000000000000000000000000000000
genesis, angel, 999999
angel, alice, 100000
angel, bob, 80000
angel, carol, 60000
angel, dave, 40000
Next block: <block_0002 的 hash>
Hashcode: <64碼 SHA256>
```

說明：每個區塊是一個 `.txt` 純文字檔，`Previous block` 就是前一塊的 SHA256，這就是「鏈」的連接方式。

---

**步驟 4：查詢帳戶餘額**

```bash
python app_checkMoney.py alice
```

---

**步驟 5：執行 6 次轉帳，觸發第 21 個區塊產生**

seed.py 跑完後 block 20 已滿，第一筆新轉帳就會建立 block 21：

```bash
python app_transaction.py alice bob 500
```

輸出顯示「（新區塊已建立）Block #21」後，繼續執行 5 筆：

```bash
python app_transaction.py bob carol 400
python app_transaction.py carol dave 300
python app_transaction.py dave alice 200
python app_transaction.py alice carol 100
python app_transaction.py bob dave 50
```

確認目前狀態：

```bash
python scripts/seed.py --status
```

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

確認 10 元已入帳：

```bash
python app_checkMoney.py alice
```

---

**步驟 7：人為竄改區塊，展示偵測機制**

先看 block 2 的內容：

```bash
python scripts/tamper.py 2
```

執行竄改（第 0 筆交易金額改為 1）：

```bash
python scripts/tamper.py 2 0 1
```

再次驗證，系統偵測到 hash 不符：

```bash
python app_checkChain.py alice
```

輸出會列出損壞的區塊編號與原因，程式以退出碼 1 結束。

離開容器：

```bash
exit
```

---

### 進階功能部分（給老師看）

進階功能全程透過網頁介面展示，開啟瀏覽器後以 `admin` / `admin123` 登入。

---

**進階功能 1：圖形化介面展示**

開啟 **http://localhost:5001**，依序展示：

- **帳本總覽**：展開區塊查看交易紀錄與 prev_hash 連接
- **執行轉帳**：輸入付款方、收款方、金額，展示即時回應
- **餘額查詢**：查詢任一帳戶
- **驗證 / 修復**：執行驗證，展示通過後的 10 元獎勵

---

**進階功能 2：分散式同步（三節點各自獨立儲存）**

先在終端確認三個節點的 volume 是分開的：

```bash
docker volume inspect client1_data
docker volume inspect client2_data
```

兩個 volume 的 `Mountpoint` 路徑不同，代表資料沒有共用。

展示同步效果：開兩個瀏覽器分頁：

| 分頁 | 網址 |
|------|------|
| 分頁 A | http://localhost:5001 |
| 分頁 B | http://localhost:5002 |

在分頁 A（node1）執行一筆轉帳 → 切換到分頁 B（node2），按「重新整理」→ 可看到相同的新區塊已同步出現。

---

**進階功能 3：跨節點完整性驗證 + 多數決修復**

**準備：先重置乾淨狀態**

進入 node1 容器，重新 seed：

```bash
docker exec -it node1 bash
```

```bash
python scripts/seed.py
```

```bash
exit
```

**第一步：竄改 node1 的區塊**

```bash
docker exec -it node1 bash
```

```bash
python scripts/tamper.py 2 0 1
```

```bash
exit
```

**第二步：在網頁介面展示比對與修復**

開啟 **http://localhost:5001**，以 `admin` 登入，進入「驗證 / 修復」：

1. 按「執行驗證」→ 顯示失敗，列出損壞的區塊編號
2. 按「比對所有節點」→ 顯示 node1 的 block hash 與 node2/node3 不同
3. 按「執行修復」→ 顯示「已修復區塊：2」
4. 再按「執行驗證」→ 顯示通過，並收到 10 元獎勵

**第三步：確認修復結果**

```bash
docker exec -it node1 bash
```

```bash
python scripts/tamper.py 2
```

第 0 筆交易金額應已還原，向老師說明此為多數決（2/3 節點一致）覆蓋的結果。

```bash
exit
```

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

有舊容器還在跑：
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

帳戶是透過交易紀錄自動建立的，確認付款方曾收過錢（有餘額）才能付款。系統初始只有 `angel` 有錢。建議先執行 `seed.py` 建立測試帳戶。

**Q：容器內找不到 scripts/seed.py**

容器跑的是舊 image，新腳本還沒打包進去：
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

**Q：seed.py 執行到一半失敗**

通常是餘額不足，先完全重置再重新 seed：
```bash
docker-compose down -v
docker-compose up -d
docker exec -it node1 bash
python scripts/seed.py
exit
```
