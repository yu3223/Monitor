import os
import requests
from datetime import datetime
import pytz
from linebot import LineBotApi
from linebot.models import TextSendMessage

# 讀取 Secrets
CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
USER_ID = os.getenv('LINE_USER_ID')

def check_mops_data(market_type):
    url = "https://mopsov.twse.com.tw/mops/web/ajax_t35sc09"
    
    # --- 測試期建議先手動固定日期，測完再改回 ---
    test_year = "115"
    test_month = "4"
    test_day = "13"
    
    payload = {
        'encodeURIComponent': '1',
        'step': '1',
        'firstin': '1',
        'off': '1',
        'TYPEK': market_type, 
        'year': test_year,
        'month': test_month,
        'day': test_day,
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': 'https://mopsov.twse.com.tw/mops/web/t35sc09',
        'X-Requested-With': 'XMLHttpRequest',
    }

    try:
        res = requests.post(url, data=payload, headers=headers, timeout=30)
        res.encoding = 'utf-8'
        html_content = res.text
        
        # --- 核心邏輯：偵測「另存 CSV」按鈕文字 ---
        if "另存 CSV" in html_content or "另存CSV" in html_content:
            return "偵測到有新資料！"
        else:
            return "查無所需資料"

    except Exception as e:
        return f"偵測出錯: {e}"

def main():
    tw_tz = pytz.timezone('Asia/Taipei')
    now = datetime.now(tw_tz)
    
    # 標題日期
    date_display = "115-04-13 (測試中)"
    time_display = now.strftime('%H:%M')
    
    sij_res = check_mops_data('sij') # 上市
    otc_res = check_mops_data('otc') # 上櫃
    
    final_msg = (
        f"[{date_display}][{time_display}]\n"
        f"上市: {sij_res}\n"
        f"上櫃: {otc_res}"
    )
    
    # 發送通知
    try:
        line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
        line_bot_api.push_message(USER_ID, TextSendMessage(text=final_msg))
        print("✅ 偵測任務完成")
    except Exception as e:
        print(f"❌ LINE發送失敗: {e}")

if __name__ == "__main__":
    main()