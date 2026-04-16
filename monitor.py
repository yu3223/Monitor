import os
import requests
import time
import urllib3
from bs4 import BeautifulSoup
from datetime import datetime
import pytz
from linebot import LineBotApi
from linebot.models import TextSendMessage

# 忽略不安全連線警告
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
        # 使用 verify=False 繞過 SSL 驗證問題
        res = requests.post(url, data=payload, headers=headers, timeout=30, verify=False)
        res.encoding = 'utf-8'
        
        # 1. 檢查是否有「查無所需資料」
        if "查無所需資料" in res.text:
            return []

        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 2. 定位正確的資料表格
        table = soup.find('table', {'class': 'hasBorder'})
        if not table:
            return []

        target_date = f"{year}/{str(month).zfill(2)}/{str(day).zfill(2)}"
        final_results = []
        
        rows = table.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            if len(cols) > 3:
                # 檢查第四欄的董事會決議日期 (格式如 115/04/15)
                row_date = cols[3].text.strip()
                if row_date == target_date:
                    code = cols[1].text.strip()
                    name = cols[2].text.strip()
                    final_results.append(f"{code} {name}")
        
        # 去除重複項並回傳
        return list(dict.fromkeys(final_results))

    except Exception as e:
        print(f"[{market_type}] 偵測連線出錯: {e}")
        return []

def main():
    # --- 測試日期設定為 115/04/15 ---
    t_year, t_month, t_day = 115, 4, 15
    
    # 執行爬取
    sii_list = check_mops_strictly(t_year, t_month, t_day, 'sii')
    time.sleep(3) # 禮貌延遲，避免被 MOPS 封鎖
    otc_list = check_mops_strictly(t_year, t_month, t_day, 'otc')
    
    # 組合訊息：有資料就列出名稱，沒資料就顯示「查無所需資料」
    sii_display = ", ".join(sii_list) if sii_list else "查無所需資料"
    otc_display = ", ".join(otc_list) if otc_list else "查無所需資料"
    
    # 取得當前執行時間 (台灣時間)
    tw_tz = pytz.timezone('Asia/Taipei')
    now_dt = datetime.now(tw_tz)
    time_display = now_dt.strftime('%H:%M')
    
    final_msg = (
        f"\n[{t_year}/{t_month}/{t_day}][{time_display}]\n"
        f"上市: {sii_display}\n"
        f"上櫃: {otc_display}"
    )
    
    # --- 無論有無資料，一律發送 LINE 通知 ---
    try:
        line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
        line_bot_api.push_message(USER_ID, TextSendMessage(text=final_msg))
        print(f"✅ 任務完成：{t_year}/{t_month}/{t_day} 的結果已發送至 LINE。")
    except Exception as e:
        print(f"❌ LINE 發送失敗: {e}")

if __name__ == "__main__":
    main()