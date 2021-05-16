import time
from datetime import timedelta
import os
from flask import Flask
from flask import render_template
from flask import redirect
from flask import request
from flask import session
from flask import abort
from flask import make_response
import pickle
from werkzeug.debug import DebuggedApplication
import sys
import re
from route import *
from route.api import *
from route.func import *
from route.manage import ips

app = Flask(__name__)

app.config['SECRET_KEY'] = open("secret_key.txt", "r").read()
app.config["UPLOAD_DIR"] = "static/upload/"
ip_track = {}
# DEBUG
if len(sys.argv) > 1:
    is_debug = True
else:
    is_debug = False

# debug app
if is_debug:
    app.wsgi_app = DebuggedApplication(app.wsgi_app, evalex=True)

# 변수 선언
connect_count = 0
black_list = []
NoLoginPages = [
    "/?",
    "/signup?",
    "/login?",
    "/redirect",
    "/quiz/question",
    "/file-server",
    "/ip-collect/c",
    "/board"
]
IgnoreConnect = [
    "/static/",
    "/plugin/",
    "/config",
    "/favicon.ico?",
    "/manage",
    "/send-message",
    "/chat-load"
]
mobile_meta = '<meta name=\'viewport\' content=\'width=device-width, initial-scale=1, user-scalable=no\' />'
config = {"save_point": 1}


# 모든 연결에 대해 실행
@app.before_request
def before_all_connect_():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(hours=10)
    global connect_count
    ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)

    # 로그 출력이 필요없는 url 로 접근할때 그냥 return
    for connect in IgnoreConnect:
        if connect in request.full_path:
            return

    # 로그인이 아직 안됐을때 None 을 아이디로
    if "userid" not in session.keys():
        p = re.compile(r"(\d+)[.](\d+)[.](\d+)[.](\d+)")
        m1 = p.search(ip)
        m2 = m1.group(1) + '.' + m1.group(2) + '.' + '***' + '.' + m1.group(4)
        session["userid"] = "guest-" + make_id()[:5] + m2

    # 마지막 접속 기록을 남김
    if ip not in ips.keys():
        ips[ip] = {
            "last": time.time(),
            "url": request.full_path,
            "id": session["userid"],
            "action": 1
        }
    else:
        ips[ip] = {
            "last": time.time(),
            "url": request.full_path,
            "id": session["userid"],
            "action": ips[ip]["action"] + 1
        }
    if os.path.isfile("hist/%s.bin" % ip):
        hist = pickle.load(open("hist/%s.bin" % ip, "rb"))
        hist[time.time()] = request.full_path

    else:
        hist = {time.time(): request.full_path}
    pickle.dump(hist, open("hist/%s.bin" % ip, "wb"))
    connect_count += 1
    if connect_count == config["save_point"]:
        pickle.dump(ips, open("ips.bin", "wb"))
        connect_count = 0

    # ip와 접근 url 출력
    print(ip, request.full_path)

    # 블랙리스트면 403 띄우기
    if ip in black_list:
        abort(403)

    if request.environ.get('SERVER_PROTOCOL') != "HTTP/1.1":
        return make_response("Only Support HTTP 1.1<br>sol-studio", 502)

    if is_logined(session):
        return

    # 로그인이 필요하면 로그인 요청페이지
    if request.full_path.startswith("/drive?")\
    or request.full_path.startswith("/chat/")\
    or request.full_path.startswith("/developer")\
    or request.full_path.startswith("/my-profile"):
        return redirect("/login?next=" + request.full_path)

def slide(slide):
    try:
        return render_template("slide/" + slide + ".html")
    except:
        return render_template("err/common.html", err_code="404", err_message="해당 슬라이드를 찾을 수 없습니다.")


# ROUTE
# INDEX
app.add_url_rule("/", view_func=index.index_page)


# BOARD
app.add_url_rule('/board', view_func=board.index)
app.add_url_rule("/board/list/<index_num>", view_func=board.pages_, defaults={"index_num": "1"})
app.add_url_rule("/board/new", view_func=board.new, methods=['POST', 'GET'])
app.add_url_rule("/board/new/upload-image", view_func=board.board_upload_image, methods=["GET", "POST"])
app.add_url_rule("/board/post/<id_>", view_func=board.post)
app.add_url_rule("/board/file/<file>", view_func=board.board_file)
app.add_url_rule("/board/post/delete/<id_>", view_func=board.delete_post)
app.add_url_rule("/board/post/edit/<id_>", view_func=board.post_edit, methods=["POST", "GET"])


# MANAGE
app.add_url_rule("/manage", view_func=manage.manage)
app.add_url_rule("/manage/<ip>", view_func=manage.manage_ip)
app.add_url_rule("/log-view/<date>", view_func=manage.veiw_log)


# TOOL
app.add_url_rule("/tools", view_func=tools.tools_index)
app.add_url_rule("/tools/p/<tool>", view_func=tools.tools_p)
app.add_url_rule("/tools/w/<tool>", view_func=tools.tools_w)


# COMMENT
app.add_url_rule("/comment/load", view_func=comment.comment_load)
app.add_url_rule("/comment/add", view_func=comment.comment_add)
app.add_url_rule("/comment/del", view_func=comment.comment_del)


# CHAT
app.add_url_rule("/chat", view_func=chat.chat_index)
app.add_url_rule("/chat/<room>", view_func=chat.chat_room)


# QUIZ
app.add_url_rule("/quiz", view_func=quiz.make, methods=["GET", "POST"])
app.add_url_rule("/quiz/answer", view_func=quiz.answer)
app.add_url_rule("/quiz/list", view_func=quiz.list)
app.add_url_rule("/quiz/del", view_func=quiz.delete)
app.add_url_rule("/quiz/question", view_func=quiz.question, methods=['GET', "POST"])


# DRIVE
app.add_url_rule("/drive", view_func=drive.drive, methods=["GET", "POST"])


# ACCOUNT, PROFILE
app.add_url_rule("/login", view_func=account.login, methods=['POST', 'GET'])
app.add_url_rule("/signup", view_func=account.signup, methods=["GET", "POST"])
app.add_url_rule("/logout", view_func=account.logout)
app.add_url_rule("/change-pw", view_func=account.change_pw, methods=["POST", "GET"])
app.add_url_rule("/my-profile", view_func=account.my_profile)
app.add_url_rule("/my-profile-edit", view_func=account.edit_profile, methods=["POST", "GET"])
app.add_url_rule("/profile/<id_>", view_func=account.other_profile)


# FILE SERVER
app.add_url_rule("/file-server/upload", view_func=file_server.file_server_upload, methods=["POST"])
app.add_url_rule("/file-server/download", view_func=file_server.file_server_download)


# IP-COLLECT
app.add_url_rule("/ip-collect", view_func=ip_collect.ip_collect_index, methods=["POST", "GET"])
app.add_url_rule("/ip-collect/view/<track_id>", view_func=ip_collect.view)
app.add_url_rule("/ip-collect/c", view_func=ip_collect.main)
app.add_url_rule("/ip-collect/data", view_func=ip_collect.ip_collect_list)

# api
# file
app.add_url_rule("/api/storage/upload", view_func=api.storage.upload, methods=["POST"])
app.add_url_rule("/api/storage/download", view_func=api.storage.download, methods=["POST"])
app.add_url_rule("/api/storage/explorer", view_func=api.storage.explorer, methods=["POST"])
app.add_url_rule("/api/storage/register", view_func=api.storage.register)

# DOCS
app.add_url_rule("/api/docs", view_func=api.docs.docs_index)
app.add_url_rule("/api/docs/<file>", view_func=api.docs.docs)


# developer
app.add_url_rule("/developer", view_func=dev.dev_index)
app.add_url_rule("/developer/get-token", view_func=dev.dev_get_token)


# GUITAR
app.add_url_rule("/intro", view_func=guitar.intro)
app.add_url_rule("/redirect", view_func=guitar.redirect_page)
app.add_url_rule("/slide/2-1/국어/<slide>", view_func=slide)

# ERR
@app.errorhandler(404)
def error_404(e):
    return render_template("err/common.html", err_code="404", err_message="원하시는 페이지를 찾을 수 없습니다.")


@app.errorhandler(500)
def error_500(e):
    return render_template("err/common.html", err_code="500", err_message="서버 내부 오류가 발견됐습니다.")


@app.errorhandler(403)
def error_500(e):
    return render_template("err/common.html", err_code="403", err_message="접근 권한이 없습니다.")


# SERVER RUN
Log.log("server restarted")
app.run(host="0.0.0.0", port=80, debug=is_debug)

# SERVER CLOSED
pickle.dump(ips, open("ips.bin", "wb"))
print("saved")
