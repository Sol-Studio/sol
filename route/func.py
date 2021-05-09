from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms import PasswordField
from wtforms.validators import DataRequired
from wtforms.validators import EqualTo
from datetime import datetime
from pytz import timezone
import logging
import time
import html
import os
import urllib
import json
from pymongo import MongoClient
import random

# LOGIN FORMS
class RegisterForm(FlaskForm):
    id = StringField('id', validators=[DataRequired()])
    name = StringField('name', validators=[DataRequired()])
    pw = PasswordField('pw', validators=[DataRequired(), EqualTo('re_password')])
    re_password = PasswordField('re_password', validators=[DataRequired(), EqualTo('pw')])


class LoginForm(FlaskForm):
    id = StringField('id', validators=[DataRequired()])
    pw = PasswordField('pw', validators=[DataRequired()])


# LOG
class Log:
    def __init__(self):
        # LOG SETTING
        dt = datetime.now(timezone("Asia/Seoul"))
        log_date = dt.strftime("%Y%m%d")
        logging.basicConfig(filename="logs/" + log_date + "log.log", level=logging.ERROR)

    @staticmethod
    def get_log_date():
        dt = datetime.now(timezone("Asia/Seoul"))
        log_date = dt.strftime("%Y.%m.%d %H:%M:%S")
        return log_date

    def log(self, message, r=0):
        log_date = self.get_log_date()
        log_message = "{0}/{1}/{2}".format(log_date, str(r), message)
        print(color(log_message, Colors.CYAN))
        logging.info(log_message)

    def error_log(self, error_message, r=0, error_code=0):
        log_date = self.get_log_date()
        log_message = "{0}/{1}/{2}/{3}".format(log_date, str(r), error_code, error_message)
        print(color(log_message, Colors.MAGENTA))
        logging.info(log_message)


# COLOR
class Colors:
    RESET = "\033[0m"
    RED = "\033[31m"
    BLACK = "\033[30m"
    GREEN = "\033[32m"
    HIDE = "\033[8m"
    UNDERLINE = "\033[4m"
    BOLD = "\033[1m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BG_BLACK = "\033[40m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"




# 색칠 함수
def color(string, start_color=Colors.RESET):
    return start_color + string + Colors.RESET


# MANAGE 페이지에서 쓰임
def time_passed(last_time):
    sec_, min_, hour_, day_ = time.time() - last_time, 0, 0, 0

    if sec_ > 60:
        min_ = sec_ // 60
        sec_ -= min_ * 60

        if min_ > 60:
            hour_ = min_ // 60
            min_ -= hour_ * 60

            if hour_ > 24:
                day_ = hour_ // 24
                hour_ -= day_ * 24

    return "%d일 %d시간 %d분 %f초" % (day_, hour_, min_, sec_)


def manage_helper(data):
    return_dict = {}
    for key in data.keys():
        return_dict[key] = {
            "last": time_passed(data[key]["last"]),
            "url": data[key]["url"],
            "id": data[key]["id"],
            "action": data[key]["action"]
        }
    return return_dict


# 로그인되어있다면 아이디, 아니면 False
def is_logined(s):
    if s["userid"][:6] == "guest-":
        return False
    else:
        return s["userid"]


# post 여러개 올리기
def mongodb_test(num):
    client = MongoClient("mongodb://localhost:27017")
    posts = client.sol.posts

    for i in range(num):
        print(posts.count())
        posts.insert_one(
            {
                "title": "program wrote" + str(posts.estimated_document_count() + 1),
                "author": "program",
                "content": "test",
                "url": posts.estimated_document_count() + 1,
                "time": time.strftime('%c', time.localtime(time.time())),
                "ip": "console"
            }
        )
    client.close()


def custom_secure_filename(name):
    return name.replace('/', "").replace("\\", "")


def get_dir_size(path):
    total = 0
    with os.scandir(path) as it:
        for entry in it:
            if entry.is_file():
                total += entry.stat().st_size
            elif entry.is_dir():
                total += get_dir_size(entry.path)
    return total


def url_short(orignalurl):
    replaceurl = html.unescape(orignalurl)
    index = replaceurl.find("|")
    client_id = "T_IA04FSNb5FsLtQcqD9"
    client_secret = "RR_tUTeSdS"
    encText = urllib.parse.quote(replaceurl[:index])
    data = "url=" + encText
    url = "https://openapi.naver.com/v1/util/shorturl"
    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", client_id)
    request.add_header("X-Naver-Client-Secret", client_secret)
    response = urllib.request.urlopen(request, data=data.encode("utf-8"))
    rescode = response.getcode()
    if (rescode == 200):
        response_body = response.read()
        shorturl = json.loads(response_body.decode('utf-8'))
        returnurl = shorturl['result']['url']
    return returnurl


def make_id():
    key = ""
    for i in range(20):
        key += random.choice("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz")

    print("\033[32m" + key + "\033[0m")
    return key

Log = Log()