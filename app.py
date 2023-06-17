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
import pyimgur
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
        #print('發送GET請求獲取網頁內容')
        url = f"https://ezgif.com/webp-to-jpg?url={webpUrl}"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")

        # 找到表單輸入框和提交按鈕
        #print('找到表單輸入框和提交按鈕')
        input_form = soup.find("form", {"class": "form ajax-form"})
        
        # 發送POST請求進行轉換
        #print('發送POST請求進行轉換ing...')
        convert_url = input_form.get("action")
        sFile = convert_url.replace('https://ezgif.com/webp-to-jpg/','')
        #print('file====' + sFile + '====')
        
        # 構建POST請求的資料
        #print('構建POST請求的資料')
        params={'ajax':True}
        files=[
        ]
        payload = {
            'file': sFile,
            'background': '#ffffff'
        }
        emptyHeaders = {}
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
            'Content-Encoding': 'gzip',
            'Content-Type': 'text/html;charset=UTF-8'
        }
        #print('url====' + convert_url)
        convert_url2 = convert_url + '?ajax=true'
        #print('url====' + convert_url2)
        
        #=========1
        response2 = requests.post(convert_url2, data=payload)
        
        # 找到轉換後的圖像URL
        #print('找轉換後的圖像URL')
        result_soup = BeautifulSoup(response2.text, "html.parser")
        
        #print(result_soup)
        #response = result_soup.find("div", {"id": "output"})
        
        ret = 'https:' + result_soup.find("img").get("src")
        #print('==1:' + ret)
    
    except Exception as ex:
        print("轉換失敗:" + ex)
        
    return ret

# 爬蟲-Apple Music
def SendAudioMessage(event,searchText):
    try:
        print("Into 弱吧唱一下:" + searchText)
        #first part: apple music查詢 爬試聽連結
        sPart1url = "https://music.apple.com/tw/search?term=" + searchText
        #print("GetAppleMusicHtmlServiceTag:" + sPart1url)
        sJson = GetAppleMusicHtmlServiceTag(sPart1url)
        
        #secend part:試聽連結 爬試聽檔案連結
        sPart2url = GetAppleMusicJsonUrl(sJson)
        #print("GetAppleMusicHtmlServiceTag:" + sPart2url)
        sJson = GetAppleMusicHtmlServiceTag(sPart2url)
        #撈出專輯封面
        picUrl = TranUrlWebpToPNG(GetAppleMusicHtmlServiceTag2(sPart2url))
        
        tempObj = {
            'artistName':'artistName',
            'albumName':'albumName',
            'songName':'songName'
        }
        #最後的Json撈出檔案url
        sAudioUrl = GetAppleMusicSongUrl(sJson,tempObj)
        print("GetAppleMusicSongUrl:" + sAudioUrl)
        print(tempObj['artistName'] + ',' + tempObj['albumName'] + ',' + tempObj['songName'])
        
        if picUrl != '':
            
            line_bot_api.reply_message(
                event.reply_token,
                [FlexSendMessage(alt_text="profile",contents={
                    "type": "carousel",
                    "contents": [
                    {
                      "type": "bubble",
                      "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                          {
                            "type": "image",
                            "url": picUrl,
                            "size": "full",
                            "aspectMode": "cover",
                            "aspectRatio": "3:3",
                            "gravity": "top",
                            "action": {
                              "type": "uri",
                              "label": "action",
                              "uri": sPart2url
                            }
                          },
                          {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                              {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                  {
                                    "type": "text",
                                    "text": tempObj['songName'],
                                    "size": "xl",
                                    "color": "#ffffff",
                                    "weight": "bold"
                                  }
                                ]
                              },
                              {
                                "type": "box",
                                "layout": "baseline",
                                "contents": [
                                  {
                                    "type": "text",
                                    "text": tempObj['artistName'],
                                    "color": "#ebebeb",
                                    "size": "sm",
                                    "flex": 0
                                  }
                                ],
                                "spacing": "lg"
                              },
                              {
                                "type": "box",
                                "layout": "baseline",
                                "contents": [
                                  {
                                    "type": "text",
                                    "text": tempObj['albumName'],
                                    "color": "#ECEAEA",
                                    "size": "xs",
                                    "flex": 0,
                                    "style": "italic"
                                  }
                                ],
                                "spacing": "lg"
                              }
                            ],
                            "position": "absolute",
                            "offsetBottom": "0px",
                            "offsetStart": "0px",
                            "offsetEnd": "0px",
                            "backgroundColor": "#03303Acc",
                            "paddingAll": "20px",
                            "paddingTop": "18px"
                          },
                          {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                              {
                                "type": "text",
                                "text": "Apple Music",
                                "color": "#ffffff",
                                "align": "center",
                                "size": "xxs",
                                "offsetTop": "3px"
                              }
                            ],
                            "position": "absolute",
                            "cornerRadius": "20px",
                            "offsetTop": "18px",
                            "backgroundColor": "#ff334b",
                            "offsetStart": "18px",
                            "height": "25px",
                            "width": "73px"
                          },
                          {
                            "type": "box",
                            "layout": "baseline",
                            "contents": [
                              {
                                "type": "text",
                                "text": "QQ弱吧",
                                "color": "#ffffff",
                                "size": "md",
                                "offsetTop": "3px",
                                "weight": "bold",
                                "align": "center"
                              }
                            ],
                            "position": "absolute",
                            "cornerRadius": "20px",
                            "offsetTop": "260px",
                            "offsetStart": "230px",
                            "height": "25px",
                            "width": "70px",
                            "backgroundColor": "#FF60AF"
                          }
                        ],
                        "paddingAll": "0px"
                      }
                    }
                  ]
                }
                )
                ,AudioSendMessage(original_content_url=sAudioUrl, duration=59000)
                ]
            )
            #line_bot_api.reply_message(event.reply_token,[ImageSendMessage(original_content_url=picUrl, preview_image_url=picUrl),AudioSendMessage(original_content_url=sAudioUrl, duration=59000)])
        else:
            line_bot_api.reply_message(event.reply_token,AudioSendMessage(original_content_url=sAudioUrl, duration=59000))
        
    except Exception as ex:
        print(ex)
        line_bot_api.reply_message(event.reply_token, TextSendMessage("哎呀，找不到。"))
    return None

def GetAppleMusicHtmlServiceTag(url):
    response = requests.get(url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, "html.parser")
    sRet = soup.find("script",id="serialized-server-data").getText()
    return sRet
def GetAppleMusicHtmlServiceTag2(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    result = soup.find("picture",class_="svelte-yxysdi")
    sHtmlAttribute = result.select_one("source").get("srcset")
    sRet = sHtmlAttribute[:sHtmlAttribute.find(".webp") + 5]
    #print(sRet)
    return sRet

def GetAppleMusicJsonUrl(sJsonString):
    sJson = json.loads(sJsonString)
    sRet = sJson[0]['data']['sections'][0]['items'][0]['contentDescriptor']['url']
    return sRet
    
def GetAppleMusicSongUrl(sJsonString,obj):
    sJson = json.loads(sJsonString)
    sRet = sJson[0]['data']['seoData']['ogSongs'][0]['attributes']['previews'][0]['url']
    print(sJson[0]['data']['seoData']['ogSongs'][0]['attributes'])
    obj['songName'] = sJson[0]['data']['seoData']['ogSongs'][0]['attributes']['name']
    print('songName:' + obj['songName'])
    obj['artistName'] = sJson[0]['data']['seoData']['ogSongs'][0]['attributes']['artistName']
    print('artistName:' + obj['artistName'])
    obj['albumName'] =  sJson[0]['data']['seoData']['ogSongs'][0]['attributes']['albumName']
    print('albumName:' + obj['albumName'])
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
    
def Update390url(event,url):
    sIndex = '390' #跨服表的index:390
    sTouchUrl = "http://api.pushingbox.com/pushingbox?devid=v77AE443E7A89FBD&data=" + sIndex + "," + url
    result = requests.get(sTouchUrl)
    print(result)

def HasWaittingProcess(userid):
    print('HasWaittingProcess:' + 'do nothing.')

'''
def glucose_graph(client_id, imgpath):
	im = pyimgur.Imgur(client_id)
	upload_image = im.upload_image(imgpath, title="Uploaded with PyImgur")
	return upload_image.link
'''

# 處理圖片訊息
@handler.add(MessageEvent, message=ImageMessage)
def handle_message(event):
    print('Into Image Message.')
    client_id = "05f738e527b6fea"
    SendImage = line_bot_api.get_message_content(event.message.id)
    print('message.id:' + event.message.id)
    print(type(SendImage))
    
    # 建立 API 請求的標頭
    headers = {'Authorization': f'Client-ID {client_id}'}
    # 發送 POST 請求並上傳圖片
    response = requests.post('https://api.imgur.com/3/image', headers=headers, data=SendImage.iter_content)

    # 解析回傳的 JSON 資料
    data = response.json()
    if response.status_code == 200 and data['success']:
        uploaded_url = data['data']['link']
        print('圖片上傳成功！')
        print('圖片連結：', uploaded_url)
    else:
        print('圖片上傳失敗！')
        print('錯誤訊息：', data['data']['error'])
        
    #line_bot_api.reply_message(event.reply_token, ImageSendMessage(original_content_url=img_url, preview_image_url=img_url))
    
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
    if HasWaittingProcess(userid) :
        print('查有尚未完成作業.')
    if (msg.find("跨服表更新") > -1) :
        print("Into Music Search.")
        sInputUrl = msg.replace("跨服表更新","").strip()
        if len(sInputUrl) > 0 :
            Update390url(event,sInputUrl)
    elif (msg.find("弱吧唱一下") > -1) :
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
        bGetKeyDone = False
        
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
                        bGetKeyDone = True
                    break
        if bGetKeyDone == False :
            if (msg.find("運氣") > -1) :
                print("Into 運氣.")
                
            elif (msg.find("運勢") > -1) :
                print("Into 運勢.")
                #抽籤google表單
                '''
                 0 "url",
                 1 "ourl",
                 2 "keyword",
                 3 "descr",
                 4 "q1",
                 5 "q2",
                 6 "q3",
                 7 "q4",
                 8 "q5",
                 9 "index",
                 10"group"
                '''
                sGoogleSheetUrl = "https://sheets.googleapis.com/v4/spreadsheets/1hdB4W5tbTsr_bcNhPmR6OG7-rqJPdqGIKq_0SwL4Ngk/values/worksheet?alt=json&key=AIzaSyBYyjXjZakvTeRFtYfkYhHqBwp596Bzpis"
                ssContent1 = requests.get(sGoogleSheetUrl).json()
                nRandNumber = random.randint(1,60)
                for item in ssContent1['values']:
                    if item[9] == str(nRandNumber):
                        line_bot_api.reply_message(event.reply_token,ImageSendMessage(original_content_url=item[0], preview_image_url=item[0]))
                        break
               
            elif (msg.find("解籤") > -1) :
                print("Into 解籤.")
                #抽籤google表單
                '''
                 0 "url",
                 1 "ourl",
                 2 "keyword",
                 3 "descr",
                 4 "q1",
                 5 "q2",
                 6 "q3",
                 7 "q4",
                 8 "q5",
                 9 "index",
                 10"group"
                '''
                sGoogleSheetUrl = "https://sheets.googleapis.com/v4/spreadsheets/1hdB4W5tbTsr_bcNhPmR6OG7-rqJPdqGIKq_0SwL4Ngk/values/worksheet?alt=json&key=AIzaSyBYyjXjZakvTeRFtYfkYhHqBwp596Bzpis"
                ssContent1 = requests.get(sGoogleSheetUrl).json()
                for item in ssContent1['values']:
                    keywords = item[2].split(',')
                    for keyword in keywords:
                        nTemp = msg.find(keyword)
                        bHasKeyword = (nTemp > -1) and keyword != ""
                        if bHasKeyword == True:
                            sMsg = '第' + item[4] + '籤-' + item[7] + item[8] + """
解籤參考：
""" + item[3] + """
❇資料來源籤詩網❇
http://www.chance.org.tw/"""
                            line_bot_api.reply_message(event.reply_token, TextSendMessage(sMsg))
                print("解籤 End.")
            elif (msg.find("溫度分布") > -1) or (msg.find("溫度分佈") > -1):
                print("Into 溫度分佈")
                sTempFName = ( now + timedelta(minutes=-19)).strftime('%Y-%m-%d_%H') + "00.GTP8w"
                photourl = "https://www.cwb.gov.tw/Data/temperature/" + sTempFName + '.jpg'
                print(photourl)
                line_bot_api.reply_message(event.reply_token,ImageSendMessage(original_content_url=photourl, preview_image_url=photourl))
                '''
                $fewMinAgo = strtotime('-19 minute');
                $photourl = 'https://www.cwb.gov.tw/Data/temperature/' . date("Y", $fewMinAgo) . '-' . date("m", $fewMinAgo) . '-' . date("d", $fewMinAgo) . '_' . date("H", $fewMinAgo) . '00.GTP8w.jpg';
                /* https://www.cwb.gov.tw/Data/temperature/2022-07-25_0600.GTP8.jpg  */
                '''
                
            elif (msg.find("累積雨量") > -1) or (msg.find("累計雨量") > -1) :
                print("Into 累積雨量")
                sTempMin = ( now + timedelta(minutes=-7) ).strftime('%M')
                sMin30 = int(int(sTempMin)/30) * 3
                sTempFName = ( now + timedelta(minutes=-7)).strftime('%Y-%m-%d_%H') + str(sMin30) + "0.QZJ8"
                photourl = "https://www.cwb.gov.tw/Data/rainfall/" + sTempFName + '.jpg'
                print(photourl)
                line_bot_api.reply_message(event.reply_token,ImageSendMessage(original_content_url=photourl, preview_image_url=photourl))
                '''累積雨量
					$sTempMin = date("i", strtotime('-7 minute'));
					$sMin30 = intval($sTempMin/30) * 3;
					$photourl = 'https://www.cwb.gov.tw/Data/rainfall/' . date("Y-m-d", strtotime('-7 minute')) . '_' . date("H", strtotime('-7 minute')) . $sMin30 . '0.QZJ8.jpg';
					https://www.cwb.gov.tw/Data/rainfall/2023-06-13_1500.QZJ8.jpg
                '''
                
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