# 香港名稱搜尋（放債人 / 慈善團體）

純前端靜態網頁 + **GitHub Actions 自動更新**官方名單。  

## 功能

- 輸入一個名稱，即時對照：
  - [放債人牌照持牌人名單](https://www.cr.gov.hk/en/statistics/docs/ml_licensees1.pdf)
  - [稅務條例第 88 條慈善機構名單](https://www.ird.gov.hk/chi/pdf/s88list_emb.pdf)
- 結果標示「放債人」／「慈善團體」
- **每日自動更新**（也可手動觸發）

## 快速部署（GitHub Pages）

1. 在 GitHub 開一個 **新的公開 Repository**（例如 `hk-name-search`）
2. 把本資料夾全部檔案 push 上去：

```bash
cd hk_name_search_static
git init
git add .
git commit -m "initial: HK name search"
git branch -M main
git remote add origin https://github.com/你的帳號/hk-name-search.git
git push -u origin main
```

3. 到 Repo → **Settings → Pages**  
   - Source: **Deploy from a branch**  
   - Branch: `main` / folder: `/ (root)`  
   - Save

4. 約一兩分鐘後開啟：  
   `https://你的帳號.github.io/hk-name-search/`

## 自動更新原理

| 項目 | 說明 |
|------|------|
| 工具 | GitHub Actions（公開 repo 免費） |
| 時間 | 每日香港時間上午 09:00（UTC 01:00；可改 `.github/workflows/update-lists.yml`） |
| 步驟 | 下載兩份 PDF → `pdftotext` 轉文字 → 寫入 `data/` → 有變更就 commit + push |
| 手動更新 | Repo → Actions → **Auto-update HK name lists** → Run workflow |

首次部署後，建議先到 Actions 手動跑一次，確認通過。

## 本機更新資料

需要：`python3`、`pdftotext`（poppler-utils）

```bash
# Ubuntu / Debian
sudo apt install poppler-utils

python3 scripts/update_data.py
```

會更新 `data/ml_full.txt`、`data/charity_full.txt`、`data/names.json`。

## 目錄結構

```
hk_name_search_static/
├── index.html                 # 搜尋介面
├── data/
│   ├── names.json             # 結構化名稱 + 更新日期
│   ├── ml_full.txt            # 放債人全文（搜尋用）
│   └── charity_full.txt       # 慈善團體全文（搜尋用）
├── scripts/
│   └── update_data.py         # 下載 PDF 並產生 data/
├── .github/workflows/
│   └── update-lists.yml       # 自動更新排程
└── README.md
```

## 注意

- 僅供參考，請以官方最新公佈名單為準
- 搜尋為「包含」比對，可能有部分字串相同的情況
- 公開 repo 的 Actions 分鐘數對個人用途通常足夠
