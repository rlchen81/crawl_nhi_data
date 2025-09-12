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

        # data.csv 存在 且 更新日期沒變動，就不爬取檔案
        last_update_date = info.get('update_date')
        if (not update_date or update_date == last_update_date) and Path('data.csv').exists():
            return      

        # 取得 zip 檔案名稱
        file_elem = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, f'a[title="{search_keyword}: txt檔案.zip"]')
            )
        )
        zip_file_name = file_elem.get_attribute('download') or file_elem.get_attribute('href').split('/')[-1]

        # 下載並解壓縮
        file_url = file_elem.get_attribute('href')
        response = requests.get(file_url, timeout=30)
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            file_list = z.namelist()
            # 欄位起末位置（Python index, 0-based, end exclusive）
            col_positions = [
                (0,2),(2,13),(13,16),(16,27),(27,37),(37,45),(45,53),(53,174),
                (174,182),(182,235),(235,292),(292,305),(305,357),(357,444),(444,603),
                (603,624),(624,766),(766,768),(768,770),(770,899),(899,1200),(1200,1256),
                (1256,1269),(1269,1321),(1321,1378),(1378,1390),(1390,1442),(1442,1499),
                (1499,1511),(1511,1563),(1563,1620),(1620,1632),(1632,1684),(1684,1741),
                (1741,1753),(1753,1805),(1805,1848),(1848,1857),(1857,1859)
            ]
            col_names = [
                'New_mark','口服錠註記','單/複方註記','藥品代碼','藥價參考金額','藥價參考日期','藥價參考截止日期','藥品英文名稱',
                '藥品規格量','藥品規格單位','成份名稱','成份含量','成份含量單位','藥品劑型','空白',
                '藥商名稱','空白','藥品分類','品質分類碼','藥品中文名稱','分類分組名稱','(複方一)成份名稱',
                '(複方一)藥品成份含量','(複方一)藥品成份含量單位','(複方二)成份名稱','(複方二)藥品成份含量','(複方二)藥品成份含量單位',
                '(複方三)成份名稱','(複方三)藥品成份含量','(複方三)藥品成份含量單位','(複方四)成份名稱','(複方四)藥品成份含量',
                '(複方四)藥品成份含量單位','(複方五)成份名稱','(複方五)藥品成份含量','(複方五)藥品成份含量單位',
                '製造廠名稱','ATC CODE','未生產或未輸入達五年'
            ]
            def split_by_positions(line, positions):
                return [line[start:end].strip() for start, end in positions]

            with open(f'data.csv', mode='w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(col_names[:13])  # 只取前13個欄位名稱
                for file in file_list:
                    if file.endswith('.TXT'):
                        with z.open(file) as f:
                            content = f.read().decode('big5', errors='ignore')
                            lines = content.splitlines()
                            for line in lines:
                                row = split_by_positions(line, col_positions[:13]) # 只取前13個欄位資料
                                # 只保留 口服錠註記 為 'a1'、藥價參考截止日期 為 '9991231'，且藥價參考金額 不為 '0.00' 的資料
                                if 'a1' in row[1] and '9991231' in row[6] and '0.00' not in row[4]:
                                    writer.writerow(row)
        print("所有.txt內容已匯入 data.csv")

        # 檔案資訊、發佈日期、更新日期寫入 info.json
        info = {
            'title': search_keyword,
            'zip_file_name': zip_file_name,
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