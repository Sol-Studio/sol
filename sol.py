# IMPORT
import logging
import time
import datetime
import pprint
from pytz import timezone
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms import PasswordField
from wtforms.validators import DataRequired
from wtforms.validators import EqualTo
from flask import Flask
from flask import render_template
from flask import redirect
from flask import request
from flask import make_response
from flask import session
from flask import flash
from flask import jsonify
from pymongo import MongoClient
from pymongo import ASCENDING
from pytz import timezone
from werkzeug.utils import secure_filename
import tensorflow.keras
from PIL import Image
from PIL import ImageOps
import numpy as np
import os
import random


os.environ['TF_CPP_MIN_LOG_LEVEL']='2'
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
class Log():
    def __init__(self):
        # LOG SETTING
        dt = datetime.datetime.now(timezone("Asia/Seoul"))
        log_date = dt.strftime("%Y%m%d")
        logging.basicConfig(filename = "logs/" + log_date + "log.log", level = logging.DEBUG)

    # LOG FUCNTIONS
    def get_log_date(self):
        dt = datetime.datetime.now(timezone("Asia/Seoul"))
        log_date = dt.strftime("%Y%m%d_%H:%M:%S")
        return log_date

    def log(self, message, request=0):
        log_date = self.get_log_date()
        log_message = "{0}/{1}/{2}".format(log_date, str(request), message)
        print(color(log_message, Colors.CYAN))
        logging.info(log_message)

    def error_log(self, error_message, request=0, error_code=0):
        log_date = self.get_log_date()
        log_message = "{0}/{1}/{2}/{3}".format(log_date, str(request), error_code, error_message)
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
    YELLO = "\033[33m"
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
    sec, min, hour, day   = time.time() - last_time, 0, 0, 0

    if sec > 60:
        min = sec // 60
        sec -= min * 60
        if min > 60:
            hour = min // 60
            min -= hour * 60
            if hour > 24:
                day = hour // 24
                hour -= day * 24

    return "%d일 %d시간 %d분 %f초" % (day, hour, min, sec)
def manage_helper(data):
    return_dict = {}
    for key in data.keys():
        return_dict[key] = {
            "last": time_passed(data[key]["last"]),
            "url": data[key]["url"],
            "id": data[key]["id"]
        }
    return return_dict


def isLogined(session):
    if "userid" in session.keys():
        return session['userid']
    else:
        return False


def run_ai( img):
    Log.log(img)
    index = open(AI_model_dir + ".idx").read().split("\n")
    np.set_printoptions(suppress=True)
    model = tensorflow.keras.models.load_model(AI_model_dir + '.h5')
    data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)
    image = Image.open(img)
    size = (224, 224)
    image = ImageOps.fit(image, size, Image.ANTIALIAS)
    image_array = np.asarray(image)
    normalized_image_array = (image_array.astype(np.float32) / 127.0) - 1
    data[0] = normalized_image_array
    prediction             = list(model.predict(data)[0])
    return_dict            = {}
    for i in range(len(index)):
        return_dict[float(prediction[i])] = index[i]
    return return_dict


Log = Log()
