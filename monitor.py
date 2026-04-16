import os
import requests
import time
import urllib3
from bs4 import BeautifulSoup
from datetime import datetime
import pytz
from linebot import LineBotApi
from linebot.models import TextSendMessage

# 忽略 SSL 警告 (GitHub Actions 環境有時也需要)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 從 GitHub Secrets 讀取設定
CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
USER_ID = os.getenv('LINE_USER_ID')

def check_mops_strictly(year, month, day, market_type):
    """嚴格檢查日期並回傳公司清單"""
    url = "https://mopsov.twse.com.tw/mops/web/ajax_t35sc09"
    
    payload = {
        'step': '1',
        'firstin': '1',
        'off': '1',
        'queryName': 'day',
        'inpuType': 'day',
        'TYPEK': market_type, 
        'year': str(year),
        'month': str(month).zfill(2),
        'day': str(day).zfill(2),
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://mopsov.twse.com.tw/mops/web/t35sc09',
    }

    try:
        # 使用 verify=False 確保連線不會因為 SSL 憑證報錯
        res = requests.post(url, data=payload, headers=headers, timeout=30, verify=False)
        res.encoding = 'utf-8'
        
        if "查無所需資料" in res.text:
            return []

        soup = BeautifulSoup(res.text, 'html.parser')
        table = soup.find('table', {'class': 'hasBorder'})
        if not table:
            return []

        target_date = f"{year}/{str(month).zfill(2)}/{str(day).zfill(2)}"
        final_results = []
        
        rows = table.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            if len(cols) > 3:
                # 檢查第四欄的董事會決議日期
                row_date = cols[3].text.strip()
                if row_date == target_date:
                    code = cols[1].text.strip()
                    name = cols[2].text.strip()
                    final_results.append(f"{code} {name}")
        
        # 去除重複項
        return list(dict.fromkeys(final_results))

    except Exception as e:
        print(f"[{market_type}] 偵測出錯: {e}")
        return []

def main():
    # --- 依需求固定測試日期 ---
    test_year, test_month, test_day = 115, 4, 14
    
    # 抓取資料
    sii_list = check_mops_strictly(test_year, test_month, test_day, 'sii')
    time.sleep(3) # 避免請求過快
    otc_list = check_mops_strictly(test_year, test_month, test_day, 'otc')
    
    # 處理顯示邏輯
    sii_display = ", ".join(sii_list) if sii_list else "查無所需資料"
    otc_display = ", ".join(otc_list) if otc_list else "查無所需資料"
    
    tw_tz = pytz.timezone('Asia/Taipei')
    now = datetime.now(tw_tz)
    time_display = now.strftime('%H:%M')
    
    final_msg = (
        f"[{test_year}/{test_month}/{test_day}][{time_display}]\n"
        f"上市: {sii_display}\n"
        f"上櫃: {otc_display}"
    )
    
    # 只要其中一個有資料就發送通知 (或是你想每次都發也可以)
    if sii_list or otc_list:
        try:
            line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
            line_bot_api.push_message(USER_ID, TextSendMessage(text=final_msg))
            print("✅ 發現資料，LINE 通知已發送")
        except Exception as e:
            print(f"❌ LINE發送失敗: {e}")
    else:
        print(f"ℹ️ {test_year}/{test_month}/{test_day} 查無資料，不發送通知。")

if __name__ == "__main__":
    main()