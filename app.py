from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *

#======python的函數庫==========
import tempfile, os
import datetime
import openai
import time
import json
import random
import requests
#======python的函數庫==========

app = Flask(__name__)
static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')
# Channel Access Token
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
# Channel Secret
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))
# OPENAI API Key初始化設定
openai.api_key = os.getenv('OPENAI_API_KEY')

def GPT_response(text):
    # 接收回應
    response = openai.Completion.create(model="text-davinci-003", prompt=text, temperature=0.5, max_tokens=500)
    print(response)
    # 重組回應
    answer = response['choices'][0]['text'].replace('。','')
    return answer


# 監聽所有來自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'


# 處理訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text
    nTemp = msg.find("喂弱吧 ")
    bCallGPT = not (nTemp == -1)
    if bCallGPT :
        GPT_answer = GPT_response(msg.replace("喂弱吧 ",""))
        print(GPT_answer)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(GPT_answer))
 
    sGoogleSheetUrl = "https://sheets.googleapis.com/v4/spreadsheets/113eh7bUFFUWuFRYRUF9N7dJyMt5hZxkpuxm49niTXRY/values/worksheet?alt=json&key=AIzaSyBYyjXjZakvTeRFtYfkYhHqBwp596Bzpis"
    
    #get the json in cell format from google
    ssContent1 = requests.get(sGoogleSheetUrl).json()
    for item in ssContent1['values']:
        keywords = item[3].split(',')
        
        for keyword in keywords:
            nTemp = msg.find(keyword)
            bHasKeyword = not (nTemp == -1)
            if bHasKeyword :
                photourls = item[0].split(',')
                nCntArray = len(photourls)
                photourl = photourls[random.randint(0,(nCntArray -1))]
                print(photourl)
                
                if item[1] == "text":
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(photourl))
                else:
                    print(item)
                    print(item[9])
                    photourls2nd = item[9].split(',')
                    nCntArray2nd = len(photourls2nd)
                    photourl2nd = photourls2nd[random.randint(0,(nCntArray2nd -1))]
                    if photourl2nd == "" :
                        line_bot_api.reply_message(event.reply_token,ImageSendMessage(original_content_url=photourl, preview_image_url=photourl))
                    else:
                        line_bot_api.reply_message(event.reply_token,ImageSendMessage(original_content_url=photourl, preview_image_url=photourl))
                        line_bot_api.reply_message(event.reply_token,ImageSendMessage(original_content_url=photourl2nd, preview_image_url=photourl2nd))
    
    

@handler.add(PostbackEvent)
def handle_message(event):
    print(event.postback.data)


@handler.add(MemberJoinedEvent)
def welcome(event):
    uid = event.joined.members[0].user_id
    gid = event.source.group_id
    profile = line_bot_api.get_group_member_profile(gid, uid)
    name = profile.display_name
    message = TextSendMessage(text=f'{name}歡迎加入')
    line_bot_api.reply_message(event.reply_token, message)
        
        
import os
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)