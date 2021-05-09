from flask import render_template
from flask import session
from flask import request
from pymongo import MongoClient
import hashlib


# chat
def chat_index():
    return render_template("chat/index.html")


def chat_room(room):
    client = MongoClient("mongodb://localhost:27017")
    if room in client["chat"].collection_names():
        h = hashlib.sha1()
        h.update(list(client["chat"]["index"].find({"room": room}))[0]["pw"].encode())
        if str(h.hexdigest()) == request.args.get("pw"):
            return render_template("chat/chat.html", room=room, userid=session["userid"])

    return render_template("err/chat-no-room.html")
