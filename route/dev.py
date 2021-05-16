from flask import render_template
from pymongo import MongoClient
from .func import *
from flask import session
def dev_index():
    return render_template("dev/index.html")

def dev_get_token():
    client = MongoClient("mongodb://localhost:27017")
    tokendb = client.dev.token
    if not list(tokendb.find({"user": session["userid"]})):
        while True:
            token = make_id() + make_id() + make_id() + make_id() + make_id()
            if not list(tokendb.find({"token": token})):
                tokendb.insert_one({"user": session["userid"], "token": token})
                return "절대 노출되지 않게 주의하세요.<br>당신의 토큰 : " + token
    return "절대 노출되지 않게 주의하세요.<br>당신의 토큰 : " + list(tokendb.find({"user": session["userid"]}))[0]["token"]