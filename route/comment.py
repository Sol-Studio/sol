from pymongo import MongoClient
from flask import render_template
from flask import request
from flask import session
from .func import *


# 댓글 로드
def comment_load():
    url = request.args.get("url")
    if not url:
        return "ㅋㅋㄹㅃㅃ"
    client = MongoClient("mongodb://localhost:27017")
    commentsdb = client.sol.comments
    comments = commentsdb.find({"url": url}).sort("_id", -1)
    return render_template("comment.html", comments=list(comments), userid=session["userid"])


# 댓글 추가
def comment_add():
    client = MongoClient("mongodb://localhost:27017")
    commentsdb = client.sol.comments
    commentsdb.insert_one({
        "url": request.args.get("url"),
        "user": session["userid"],
        "date": Log.get_log_date(),
        "content": request.args.get("content"),
        "id": commentsdb.find().sort('_id', -1)[0]["id"] + 1,
        "ip": request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    })
    client.close()
    return "complete"


# 댓글 삭제
def comment_del():
    client = MongoClient("mongodb://localhost:27017")
    commentsdb = client.sol.comments
    data = list(commentsdb.find({
        "id": int(request.args.get("id"))
    }))
    if data[0]["user"] == session["userid"] or session["userid"] == "admin":
        commentsdb.delete_one({
            "id": int(request.args.get("id"))
        })
        client.close()
        return ''
    client.close()
    return ''