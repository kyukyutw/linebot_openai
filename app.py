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
from datetime import datetime,timedelta 
import pytz #時區設定
from bs4 import BeautifulSoup #爬蟲
import mechanicalsoup
#======python的函數庫==========

app = Flask(__name__)
static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')
# Channel Access Token
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
# Channel Secret
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))
# OPENAI API Key初始化設定
openai.api_key = os.getenv('OPENAI_API_KEY')

#webp to png
def TranUrlWebpToPNG(webpUrl):
    ret = ''
    try:
        # 發送GET請求獲取網頁內容
        print('發送GET請求獲取網頁內容')
        url = f"https://ezgif.com/webp-to-jpg?url={webpUrl}"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")

        # 找到表單輸入框和提交按鈕
        print('找到表單輸入框和提交按鈕')
        input_form = soup.find("form", {"class": "form ajax-form"})
        print('找到表單輸入框和提交按鈕2')
        submit_button = input_form.find("input", {"type": "submit"})
        
        # 取得按鈕的相關資訊
        button_action = submit_button.get('onclick')  # 或替換為其他屬性，例如 'href' 或 'data-action'


        # 構建POST請求的資料
        print('構建POST請求的資料')
        data = {
            "file": webpUrl,
            "convert": "Convert to JPG"
        }
        # 發送POST請求進行轉換
        print('發送POST請求進行轉換')
        convert_url = input_form.get("action") + '?ajax=true'
        response = requests.post(convert_url, data=data)

        # 找到轉換後的圖像URL
        print('找到轉換後的圖像URL')
        result_soup = BeautifulSoup(response.text, "html.parser")
        #img 在script之下 div id=output是空的(?)
        result_image = result_soup.find("div", {"id": "output"}) 
        print(result_image)
    
        if result_image:
            ret = result_image.find("img").get("src")

            print("轉換完成並下載為JPG檔案:", output_path)
        else:
            print("轉換失敗")
    except Exception as ex:
        print("轉換失敗:" + ex)
        
    return ret

# 爬蟲-Apple Music
def SendAudioMessage(event,searchText):
    try:
        print("Into 弱吧唱一下:" + searchText)
        #first part: apple music查詢 爬試聽連結
        sPart1url = "https://music.apple.com/tw/search?term=" + searchText
        print("GetAppleMusicHtmlServiceTag:" + sPart1url)
        sJson = GetAppleMusicHtmlServiceTag(sPart1url)
        
        #secend part:試聽連結 爬試聽檔案連結
        sPart2url = GetAppleMusicJsonUrl(sJson)
        print("GetAppleMusicHtmlServiceTag:" + sPart2url)
        sJson = GetAppleMusicHtmlServiceTag(sPart2url)
        #撈出專輯封面
        picUrl = TranUrlWebpToPNG(GetAppleMusicHtmlServiceTag2(sPart2url))
        
        #最後的Json撈出檔案url
        sAudioUrl = GetAppleMusicSongUrl(sJson)
        print("GetAppleMusicSongUrl:" + sAudioUrl)
        
        if picUrl != '':
            line_bot_api.reply_message(event.reply_token,[ImageSendMessage(original_content_url=picUrl, preview_image_url=picUrl),AudioSendMessage(original_content_url=sAudioUrl, duration=59000)])
        else:
            line_bot_api.reply_message(event.reply_token,AudioSendMessage(original_content_url=sAudioUrl, duration=59000))
        
    except Exception as ex:
        print(ex)
        line_bot_api.reply_message(event.reply_token, TextSendMessage("哎呀，找不到。"))
    return None

def GetAppleMusicHtmlServiceTag(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    sRet = soup.find("script",id="serialized-server-data").getText()
    return sRet
def GetAppleMusicHtmlServiceTag2(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    result = soup.find("picture",class_="svelte-yxysdi")
    sHtmlAttribute = result.select_one("source").get("srcset")
    sRet = sHtmlAttribute[:sHtmlAttribute.find(".webp") + 5]
    print(sRet)
    return sRet

def GetAppleMusicJsonUrl(sJsonString):
    sJson = json.loads(sJsonString)
    sRet = sJson[0]['data']['sections'][0]['items'][0]['contentDescriptor']['url']
    return sRet
    
def GetAppleMusicSongUrl(sJsonString):
    sJson = json.loads(sJsonString)
    sRet = sJson[0]['data']['seoData']['ogSongs'][0]['attributes']['previews'][0]['url']
    return sRet
    
def GPT_response(text):
    # 接收回應
    response = openai.Completion.create(model="text-davinci-003", prompt=text, temperature=0.5, max_tokens=500)
    print(response)
    # 重組回應
    answer = response['choices'][0]['text'].replace('。','').replace('\n\n','')
    return answer

def GPT_IMAGE_response(image) :
    response = openai.Image.create(prompt=image, n=1, size="512x512")
    print(response)
    answer = response['data'][0]['url']
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
    print(msg)
    
    #print(event.source)
    jSource = json.loads(str(event.source))
    groupid = ""
    userid = ""
    if jSource["type"] == "group" :
        groupid = jSource["groupId"]
        userid = jSource["userId"]
    elif jSource["type"] == "user" :
        userid = jSource["userId"]
    
    bPass = False
    #C35ffb4e93a34ce198634429fb8e0df21 LINE-BOT-TEST-1
    #Cd8ca09b51a8074d0c23c34337e0bb691 LINE-BOT-TEST-2
    #C61f797a454e8e1db2a87f62042ff05d2 紐西蘭進口的-二之國  
    if groupid == "C35ffb4e93a34ce198634429fb8e0df21" : bPass = True
    elif groupid == "Cd8ca09b51a8074d0c23c34337e0bb691" : bPass = True
    elif groupid == "C61f797a454e8e1db2a87f62042ff05d2" : bPass = True
    elif userid == "Ub6491d91c5b11078c3315f99a9b1035f" : bPass = True
    
    if bPass == False : return None
    
    #時間調整-台灣
    timezone_TW=pytz.timezone('ROC')
    now=datetime.now(timezone_TW)
    if (msg.find("弱吧唱一下") > -1) :
        print("Into Music Search.")
        sInputMusic = msg.replace("弱吧唱一下","").strip()
        if len(sInputMusic) > 0 :
            SendAudioMessage(event,sInputMusic)
    elif (msg.find("喂弱吧 ") > -1) :
        print("Into GPT.")
        sInputGPT = msg.replace("喂弱吧 ","").strip()
        if len(sInputGPT) > 0 :
            GPT_answer = GPT_response(sInputGPT)
            #print(GPT_answer)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(GPT_answer))
    elif (msg.find("弱吧畫一下") > -1) :
        print("Into GPT IMAGE.")
        sInputGPTIMAGE = msg.replace("弱吧畫一下","").strip()
        if len(sInputGPTIMAGE) > 0 :
            GPT_IMAGE_answer = GPT_IMAGE_response(sInputGPTIMAGE)
            print(GPT_IMAGE_answer)
            line_bot_api.reply_message(event.reply_token,ImageSendMessage(original_content_url=GPT_IMAGE_answer, preview_image_url=GPT_IMAGE_answer))
    elif (msg.find("雷達回波") > -1) :
        print("Into 雷達回波.")
        sTempMin = ( now + timedelta(minutes=-7) ).strftime('%M')
        sMin10 = int(int(sTempMin)/10)
        sTempFName = ( now + timedelta(minutes=-7)).strftime('%Y%m%d%H') + str(sMin10) + "0"
        photourl = "https://www.cwb.gov.tw/Data/radar/CV1_1000_" + sTempFName + '.png'
        print(photourl)
        line_bot_api.reply_message(event.reply_token,ImageSendMessage(original_content_url=photourl, preview_image_url=photourl))
    else :
        print("Into Keyword Search.")
        #google表單
        sGoogleSheetUrl = "https://sheets.googleapis.com/v4/spreadsheets/113eh7bUFFUWuFRYRUF9N7dJyMt5hZxkpuxm49niTXRY/values/worksheet?alt=json&key=AIzaSyBYyjXjZakvTeRFtYfkYhHqBwp596Bzpis"
        ssContent1 = requests.get(sGoogleSheetUrl).json()
        
        bShutUp = False
        nStartHourOfOff = 0
        nEndHourOfOff = 11
        bOutOfWorkTime = False
            
        for item in ssContent1['values']:
            keywords = item[3].split(',')
            
            if (item[5] == '2') :
                if (len(item) > 12) : 
                    if (item[12] == 'Y') : bShutUp = True;
                
                if (len(item) > 13) : 
                    if (item[13] != '') : nStartHourOfOff = int(item[13])
                if (len(item) > 14) : 
                    if (item[14] != '') : nEndHourOfOff = int(item[14])
                nHourOfNow = int(now.hour)
                if (nStartHourOfOff <= nHourOfNow and nHourOfNow <= nEndHourOfOff) : bOutOfWorkTime = True

            for keyword in keywords:
                nTemp = msg.find(keyword)
                bHasKeyword = (nTemp > -1) and keyword != ""
                if bHasKeyword == True:
                    sIndex = item[5]
                    sTempDate = "2000-01-01"
                    sTempTime = "00:00:00"
                    if len(item) > 6 : 
                        if (item[6] != "") : sTempDate = item[6]
                    if len(item) > 7 : 
                        if (item[7] != "") : sTempTime = item[7]
                    dateBefore = sTempDate + ' ' + sTempTime
                    bCalled = False
                    #近期未連續觸發
                    datetime_object = datetime.strptime(dateBefore, '%Y-%m-%d %H:%M:%S')
                    datetime_object_E = datetime.strptime(now.strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
                    datetime_diff = datetime_object_E - datetime_object
                    diff_days = datetime_diff.days #日期差距
                    diff_seconds = datetime_diff.seconds #秒數差距
                    if ( item[2] == "公告" or diff_days > 0 or (diff_days == 0 and diff_seconds > 899) ) :
                        bCalled = True
                    
                    bHasExclude = False
                    if (len(item) > 11) :
                        if (item[11] != "") :
                            sExclude = item[11].split(',')
                            for exclude in sExclude :
                                if (msg.find(exclude) > -1 and exclude != "") :
                                    print("exclude:" + exclude)
                                    bHasExclude = True
                                    break
                    
                    if (bHasExclude == True) : continue
                    if (bShutUp == True) : continue
                    if (bOutOfWorkTime == True) : continue
                    if len(item) > 6 :
                        if ( (item[6] != "") and (item[2] == "once") ) : continue 
                    
                    if bCalled == True :
                        
                        photourls = item[0].split(',')
                        nCntArray = len(photourls)
                        photourl = photourls[random.randint(0,(nCntArray -1))]
                        #print("keyword:" + keyword)
                        #print(photourl)
                        
                        if item[1] == "text":
                            line_bot_api.reply_message(event.reply_token, TextSendMessage(photourl))
                        else:
                            photourl2nd = ""
                            if len(item) > 9 :
                                photourls2nd = item[9].split(',')
                                nCntArray2nd = len(photourls2nd)
                                photourl2nd = photourls2nd[random.randint(0,(nCntArray2nd -1))]
                                
                            if photourl2nd == "" :
                                line_bot_api.reply_message(event.reply_token,ImageSendMessage(original_content_url=photourl, preview_image_url=photourl))
                            else:
                                line_bot_api.reply_message(event.reply_token,[ImageSendMessage(original_content_url=photourl, preview_image_url=photourl),ImageSendMessage(original_content_url=photourl2nd, preview_image_url=photourl2nd)])

                        sTouchUrl1 = "http://api.pushingbox.com/pushingbox?devid=v8FD032D0733DF5D&data=" + sIndex + "," + now.strftime('%Y-%m-%d')
                        sTouchUrl2 = "http://api.pushingbox.com/pushingbox?devid=v14A88C7A33FC0DC&data=" + sIndex + "," + now.strftime('%H:%M:%S')
                        sTouchUrl3 = "http://api.pushingbox.com/pushingbox?devid=vB3E9F5CEA4E5E34&data=" + sIndex + "," + userid
                        requests.get(sTouchUrl1)
                        requests.get(sTouchUrl2)
                        requests.get(sTouchUrl3)
                    break
    print("End of testing.")
    
    

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