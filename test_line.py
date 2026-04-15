import os
from datetime import datetime
from linebot import LineBotApi
from linebot.models import TextSendMessage

# 從環境變數讀取 Token 與 ID
CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
USER_ID = os.getenv('LINE_USER_ID')

def send_test_message():
    # 取得當前時間 (GitHub Actions 預設是 UTC 時間)
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    message_text = f"Hello! GitHub Actions 測試成功。\n現在時間：{now} (UTC)"

    try:
        line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
        line_bot_api.push_message(USER_ID, TextSendMessage(text=message_text))
        print(f"✅ 訊息已發送: {now}")
    except Exception as e:
        print(f"❌ 發送失敗: {e}")

if __name__ == "__main__":
    send_test_message()