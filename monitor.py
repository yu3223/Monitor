import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz
from linebot import LineBotApi
from linebot.models import TextSendMessage

# 讀取 Secrets
CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
USER_ID = os.getenv('LINE_USER_ID')

def get_mops_data(market_type):
    url = "https://mopsov.twse.com.tw/mops/web/ajax_t35sc09"
    
    # --- 測試用：固定日期為 115/04/13 ---
    test_year = "115"
    test_month = "04"
    test_day = "13"
    # -------------------------------
    
    payload = {
        'step': '1',
        'firstin': '1',
        'off': '1',
        'TYPEK': market_type, 
        'year': test_year,
        'month': test_month,
        'day': test_day
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    try:
        res = requests.post(url, data=payload, headers=headers, timeout=30)
        res.encoding = 'utf-8'
        
        # 1. 先判斷是否有「查無所需資料」
        if "查無所需資料" in res.text:
            return "查無所需資料"
            
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 2. 尋找含有「公司代號」的資料表格
        target_table = None
        for table in soup.find_all('table', {'class': 'hasBorder'}):
            if "公司代號" in table.text:
                target_table = table
                break
        
        if not target_table:
            return "查無所需資料"
            
        rows = target_table.find_all('tr')[1:] 
        results = []
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 2:
                code = cols[0].get_text(strip=True)
                name = cols[1].get_text(strip=True)
                # 確保是 4 碼以上的純數字代號
                if code.isdigit() and len(code) >= 4:
                    results.append(f"{code} {name}")
        
        return results if results else "查無所需資料"

    except Exception as e:
        return f"偵測出錯: {e}"

def main():
    # 這裡顯示的時間依然可以用當前時間，或是也手動改成測試時間
    tw_tz = pytz.timezone('Asia/Taipei')
    now = datetime.now(tw_tz)
    
    # 測試時把顯示標題也改一下，方便辨認
    date_display = "115-04-13 (測試資料)"
    time_display = now.strftime('%H:%M')
    
    sij_res = get_mops_data('sij') # 上市
    otc_res = get_mops_data('otc') # 上櫃
    
    def format_msg(data):
        if isinstance(data, list):
            count = len(data)
            content = ", ".join(data)
            if len(content) > 2000:
                content = content[:2000] + "...(略)"
            return f"偵測到[{count}]筆資料\n({content})"
        return data

    final_msg = (
        f"[{date_display}][{time_display}]\n"
        f"上市:{format_msg(sij_res)}\n"
        f"上櫃:{format_msg(otc_res)}"
    )
    
    if len(final_msg) > 5000:
        final_msg = final_msg[:4990] + "..."
    
    try:
        line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
        line_bot_api.push_message(USER_ID, TextSendMessage(text=final_msg))
        print("✅ 測試訊息發送成功")
    except Exception as e:
        print(f"❌ LINE發送失敗: {e}")

if __name__ == "__main__":
    main()