## 健保用藥品項自動爬取程式

本專案使用 Selenium 自動下載健保署網站的用藥品項資料，並將資料整理成 CSV 檔案，且自動記錄檔案資訊於 info.json，方便日後比對更新日期。

### 主要功能

- 自動下載最新用藥品項查詢 ZIP 檔
- 解壓縮並合併所有 TXT 檔案為 CSV
- 產生 info.json 記錄 zip 檔名、發布日期、更新日期
- 依 info.json 的更新日期判斷是否需要重新爬取檔案

### 執行方式

1. 安裝 Python 3、Chrome、ChromeDriver
2. 安裝必要套件：
   ```bash
   pip install selenium requests
   ```
3. 執行主程式：
   ```bash
   python main.py
   ```

### 注意事項

- info.json 會自動產生與更新，請勿手動修改
- 請確認網路連線正常

## 資料來源

- [健保用藥品項查詢](https://www.nhi.gov.tw/ch/lp-2466-1.html)
