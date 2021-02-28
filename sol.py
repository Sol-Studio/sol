# IMPORT
import logging
import time
import datetime
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms import PasswordField
from wtforms.validators import DataRequired
from wtforms.validators import EqualTo
from pytz import timezone
import os


os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
AI_model_dir = "ai/model_v3"


# LOGIN FORMS
class RegisterForm(FlaskForm):
    id = StringField('id', validators=[DataRequired()])
    name = StringField('name', validators=[DataRequired()])
    pw = PasswordField('pw', validators=[DataRequired(), EqualTo('re_password')])
    re_password = PasswordField('re_password', validators=[DataRequired(), EqualTo('pw')])


class LoginForm(FlaskForm):
    id = StringField('id', validators=[DataRequired()])
    pw = PasswordField('pw', validators=[DataRequired()])


class Log:
    def __init__(self):
        # LOG SETTING
        dt = datetime.datetime.now(timezone("Asia/Seoul"))
        log_date = dt.strftime("%Y%m%d")
        logging.basicConfig(filename="logs/" + log_date + "log.log", level=logging.DEBUG)

    # LOG functions
    @staticmethod
    def get_log_date():
        dt = datetime.datetime.now(timezone("Asia/Seoul"))
        log_date = dt.strftime("%Y%m%d_%H:%M:%S")
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


def color(string, start_color=Colors.RESET):
    return start_color + string + Colors.RESET


def time_passed(last_time):
    sec_, min_, hour_, day = time.time() - last_time, 0, 0, 0

    if sec_ > 60:
        min_ = sec_ // 60
        sec_ -= min_ * 60
        if min_ > 60:
            hour_ = min_ // 60
            min_ -= hour_ * 60
            if hour_ > 24:
                day_ = hour_ // 24
                hour_ -= day_ * 24

    return "%d일 %d시간 %d분 %f초" % (day, hour_, min_, sec_)


def manage_helper(data):
    return_dict = {}
    for key in data.keys():
        return_dict[key] = {
            "last": time_passed(data[key]["last"]),
            "url": data[key]["url"],
            "id": data[key]["id"]
        }
    return return_dict


def is_logined(s):
    if "userid" in s.keys():
        return s['userid']
    else:
        return False


Log = Log()
