import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from linebot import LineBotApi
from linebot.models import TextSendMessage

# 取得 GitHub Secrets
CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
USER_ID = os.getenv('LINE_USER_ID')

def get_mops_data(market_type):
    url = "https://mopsov.twse.com.tw/mops/web/ajax_t35sc09"
    
    # 計算當天日期 (民國紀年格式: 115/04/15)
    now = datetime.now()
    year = now.year - 1911
    date_str = f"{year}/{now.strftime('%m/%d')}"
    
    # 設定 POST 參數
    # step: 1, firstin: 1, TYPEK: sij (上市) 或 otc (上櫃)
    payload = {
        'step': '1',
        'firstin': '1',
        'off': '1',
        'TYPEK': market_type, 
        'year': str(year),
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
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 判斷是否有資料 (公開資訊觀測站查無資料通常會出現特定文字)
        if "查無所需資料" in res.text or not soup.find('table', {'class': 'hasBorder'}):
            return "查無所需資料"
        
        # 抓取表格中的公司代號與名稱
        table = soup.find('table', {'class': 'hasBorder'})
        rows = table.find_all('tr')[1:]  # 跳過標題列
        results = []
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 2:
                code = cols[0].text.strip()
                name = cols[1].text.strip()
                results.append(f"{code} {name}")
        
        return results
    except Exception as e:
        return f"偵測出錯: {e}"

def main():
    # 執行監測
    sij_data = get_mops_data('sij') # 上市
    otc_data = get_mops_data('otc') # 上櫃
    
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    # 格式化上市訊息
    if isinstance(sij_data, list):
        sij_msg = f"偵測到[{len(sij_data)}]筆資料\n(" + ", ".join(sij_data) + ")"
    else:
        sij_msg = sij_data

    # 格式化上櫃訊息
    if isinstance(otc_data, list):
        otc_msg = f"偵測到[{len(otc_data)}]筆資料\n(" + ", ".join(otc_data) + ")"
    else:
        otc_msg = otc_data

    # 合併最終訊息
    final_msg = f"[{now_str}]\n上市:{sij_msg}\n上櫃:{otc_msg}"
    
    # 發送 LINE
    line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
    line_bot_api.push_message(USER_ID, TextSendMessage(text=final_msg))

if __name__ == "__main__":
    main()