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
    
    tw_tz = pytz.timezone('Asia/Taipei')
    now = datetime.now(tw_tz)
    roc_year = now.year - 1911
    
    payload = {
        'step': '1',
        'firstin': '1',
        'off': '1',
        'TYPEK': market_type, 
        'year': str(roc_year),
        'month': now.strftime('%m'),
        'day': now.strftime('%d')
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    try:
        res = requests.post(url, data=payload, headers=headers, timeout=30)
        res.encoding = 'utf-8'
        
        # --- 步驟 A: 檢查是否有「查無所需資料」 ---
        if "查無所需資料" in res.text:
            return "查無所需資料"
            
        # --- 步驟 B: 如果沒出現該關鍵字，才開始解析表格 ---
        soup = BeautifulSoup(res.text, 'html.parser')
        target_table = None
        
        # 尋找含有「公司代號」文字的資料表格
        for table in soup.find_all('table', {'class': 'hasBorder'}):
            if "公司代號" in table.text:
                target_table = table
                break
        
        if not target_table:
            return "查無所需資料"
            
        rows = target_table.find_all('tr')[1:] # 跳過標題列
        results = []
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 2:
                # 取得公司代號與名稱
                code = cols[0].get_text(strip=True)
                name = cols[1].get_text(strip=True)
                
                # 確保抓到的是真正的公司代號 (純數字且長度 >= 4)
                if code.isdigit() and len(code) >= 4:
                    results.append(f"{code} {name}")
        
        return results if results else "查無所需資料"

    except Exception as e:
        return f"偵測出錯: {e}"

def main():
    tw_tz = pytz.timezone('Asia/Taipei')
    now = datetime.now(tw_tz)
    date_display = now.strftime('%Y-%m-%d')
    time_display = now.strftime('%H:%M')
    
    sij_res = get_mops_data('sij') # 上市
    otc_res = get_mops_data('otc') # 上櫃
    
    def format_msg(data):
        if isinstance(data, list):
            count = len(data)
            content = ", ".join(data)
            # 限制長度避免 LINE 噴錯 (5000字上限)
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
        print("✅ 訊息發送成功")
    except Exception as e:
        print(f"❌ LINE發送失敗: {e}")

if __name__ == "__main__":
    main()