from .func import *
from flask import session
from flask import render_template


# 홈 INDEX
def index_page():
    if is_logined(session):
        return render_template("index.html")
    else:
        return render_template("index_before_login.html")