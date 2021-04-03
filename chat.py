from flask import Flask, request, render_template
from datetime import datetime
from pytz import timezone
def get_log_date():
    dt = datetime.now(timezone("Asia/Seoul"))
    log_date = dt.strftime("%Y%m%d_%H:%M:%S")
    return log_date


app = Flask(__name__)
chat = [
    {
        "id":"공지",
        "time": "공지",
        "content": "server started"
    }
]

@app.route("/load")
def chat_load():
    room = request.args.get("room")
    id_ = request.args.get("id")
    try:
        if request.args.get("userid") == chat[int(id_)]["id"]:
            z = "msg-self"
        else:
            z = ""

        print(chat[int(id_)]["content"])
        return render_template("chat/load.html", 
                                name=chat[int(id_)]["id"],
                                time=chat[int(id_)]["time"],
                                content=chat[int(id_)]["content"],
                                isself=z)
    except Exception as e:
        print(e)
        return "fail"


@app.route("/send")
def chat_send():
    chat.append({
        "id": request.args.get("userid"),
        "time": get_log_date(),
        "content": request.args.get("msg")
    })
    print(chat)
    return ""

app.run(host="0.0.0.0", port=2000, debug=True)
