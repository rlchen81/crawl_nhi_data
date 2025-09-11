from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pathlib import Path
from datetime import datetime
import requests
import zipfile
import io
import csv
import json

def main():   
    options = webdriver.ChromeOptions()
    options.add_argument('--headless') # 不開啟視窗執行
    driver = webdriver.Chrome(options=options)

    info_path = Path('info.json')
    info = {}
    if info_path.exists():
        try:
            with open(info_path, 'r', encoding='utf-8') as f:
                info = json.load(f)
        except Exception:
            info = {}

    try:
        driver.get('https://www.nhi.gov.tw/ch/lp-2466-1.html')

        year = datetime.now().year - 1911
        month = datetime.now().month
        search_keyword = f'健保用藥品項{year}年{month}月查詢檔'

        # 取得下載頁連結的HTML節點
        url_elem = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, f"//a[span[@class='title' and contains(text(), '{search_keyword}')]]")
            )
        )
        download_page_url = url_elem.get_attribute('href')
        
        # 前往下載頁
        driver.get(download_page_url)

        # 取得頁面上的發布日期
        pub_date_elem = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//section[@class='pubInfo']//dt[text()='發布日期']/following-sibling::dd/time")
            )
        )
        pub_date = pub_date_elem.text

        # 取得頁面上的更新日期
        update_date_elem = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//section[@class='pubInfo']//dt[text()='更新日期']/following-sibling::dd/time")
            )
        )
        update_date = update_date_elem.text

        # 比對 JSON 的更新日期 (如果更新日期為空值，或比對更新日期相同，就不爬取檔案)
        last_update_date = info.get('update_date')
        if (not update_date or update_date == last_update_date) and Path('data.csv').exists():
            return      

        # 取得 zip 檔案名稱
        file_elem = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, f'a[title="{search_keyword}: txt檔案.zip"]')
            )
        )
        zip_filename = file_elem.get_attribute('download') or file_elem.get_attribute('href').split('/')[-1]

        # 下載並解壓縮
        fileUrl = file_elem.get_attribute('href')
        response = requests.get(fileUrl, timeout=30)
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            file_list = z.namelist()
            with open(f'data.csv', mode='w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                for filename in file_list:
                    if filename.endswith('.TXT'):
                        with z.open(filename) as f:
                            content = f.read().decode('big5', errors='ignore')
                            lines = content.splitlines()
                            for line in lines:
                                row = line.strip().split()
                                if 'a1' in row and '9991231' in row and '0.00' not in row:
                                    writer.writerow(row)
        print("所有.txt內容已匯入 data.csv")

        # 檔案資訊、發佈日期、更新日期寫入 info.json
        info = {
            'title': search_keyword,
            'zip_filename': zip_filename,
            'pub_date': pub_date,
            'update_date': update_date
        }
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(info, f, ensure_ascii=False, indent=2)

    except Exception as e:
        print("發生錯誤：", e)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()