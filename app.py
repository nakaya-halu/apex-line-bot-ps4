from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,ImageMessage, AudioMessage, StickerMessage, FollowEvent
)
import requests
import json
import re
import configparser

app = Flask(__name__)
#WEBサーバーの起動
if __name__ == "__main__":
    app.run()
#設定ファイルのロード
config = configparser.ConfigParser()
config.read('set.ini')
#設定ファイルセクション
SECTION = 'SECRETS'
#APEX API
URL = "https://public-api.tracker.gg/v2/apex/standard/profile/psn/{id}"
#API Key
API_KEY = config.get(SECTION, 'API_KEY')
#アクセストークン
ACCESS_TOKEN = LineBotApi(config.get(SECTION, 'ACCESS_TOKEN'))
#チャンネルシークレット
CHANNEL_SECRET = WebhookHandler(config.get(SECTION, 'CHANNEL_SECRET'))
#メッセージ
MESSAGE_GREETING = "はじめまして☀\n追加ありがとうございます！\nこちらはPS4専用になりますので\nご注意ください。\n検索したいPSN IDを送ってくださいね！\n※開発中ですので、上手く動かなかったらごめんなさい。"
#メッセージ
MESSAGE_REQUEST = "知りたいプレイヤーのPSN IDを入力してください。\n※検索に時間がかかる場合がありますが、ご了承ください。"
#メッセージ
MESSAGE_FAILURE = "検索に失敗しました。\nIDが正しいかお確かめください。"

"""
署名検証を行い、handleに定義されている関数を呼び出す。
"""
@app.route("/callback", methods=['POST'])
def callback():
    #リクエストヘッダーから署名検証のための値を取得
    signature = request.headers['X-Line-Signature']

    #リクエストボディを取得
    body = request.get_data(as_text=True)

    #署名を検証し、問題なければhandleに定義されている関数を呼び出す
    try:
        CHANNEL_SECRET.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

"""
個別handle関数
テキストメッセージが送られた場合、
返答メッセージを生成し、LINEに送る
"""
@CHANNEL_SECRET.add(MessageEvent, message=TextMessage)
def handle_message(event):
    #ユーザからのメッセージを取得
    message = event.message.text
    #メッセージbody
    body = MESSAGE_FAILURE

    headers = {'TRN-Api-Key': API_KEY}

    #HPPTレスポンスを受け取る
    response = requests.get(URL.format(id=message), headers=headers)

    #正常に受け取れたかどうか(正常:200)
    if response.status_code == 200:
    #JSONの取得
        data = response.json()
        body = "UserID:" + data["data"]["platformInfo"]["platformUserId"] + "\n" \
            + "Rank:" + str(data["data"]["segments"][0]["stats"]["rankScore"]["metadata"]["rankName"]) + "\n" \
            + "RP:" + str(data["data"]["segments"][0]["stats"]["rankScore"]["value"]) + "\n" \
            + "Level:" + str(data["data"]["segments"][0]["stats"]["level"]["displayValue"])

    #生成したbodyをLINEに送る
    ACCESS_TOKEN.reply_message(event.reply_token,TextSendMessage(body))

"""
個別handle関数
音声・画像・スタンプが送られた場合、
返答メッセージを生成し、LINEに送る
"""
@CHANNEL_SECRET.add(MessageEvent, message=(StickerMessage, ImageMessage, AudioMessage))
def handle_other_messages(event):
    body = MESSAGE_REQUEST
    #生成したbodyをLINEに送る
    ACCESS_TOKEN.reply_message(event.reply_token,TextSendMessage(body))

"""
個別handle関数
友達追加された場合、
メッセージを生成し、LINEに送る
"""
@CHANNEL_SECRET.add(FollowEvent)
def handle_follow(event):
    ACCESS_TOKEN.reply_message(
        event.reply_token,
        TextSendMessage(text = MESSAGE_GREETING)
    )