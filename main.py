# IMPORT
import logging                                    # 로깅
import time                                       # 시간
import datetime                                   # 시간
from flask_wtf import FlaskForm                   # 로그인 검증
from wtforms import StringField                   # 로그인 검증
from wtforms import PasswordField                 # 로그인 검증
from wtforms.validators import DataRequired       # 로그인 검증
from wtforms.validators import EqualTo            # 로그인 검증
from pytz import timezone                         # 시간 정보
import os                                         # os
from flask import Flask                           # app
from flask import render_template                 # 템플릿
from flask import redirect                        # 리다이렉트
from flask import request                         # 클라이언트 정보
from flask import session                         # 로그인 정보
from flask import flash                           # alert 띄우기
from flask import abort                           # 정상적이지 않은 상황에서 abort(403)하면 바로 403 띄워줌
from pymongo import MongoClient                   # MongoDB
import mimetypes                                  # 파일 검증
from werkzeug.utils import secure_filename
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
from flask import Flask
from flask import render_template
from flask import redirect
from flask import request
from flask import session
from flask import flash
from flask import abort  # 정상적이지 않은 상황에서 abort(403)하면 바로 403 띄워줌
from pymongo import MongoClient

# Create Flask App
app = Flask(__name__)


ips = {}

black_list = []

NoLoginPages = [
    "/?",
    "/signup?",
    "/login?"
]

IgnoreConnect = [
    "/static/",
    "/plugin/",
    "/config",
    "/favicon.ico?",
    "/manage",
    "/ai/wait/"
]


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
        dt = datetime.datetime.now(timezone("Asia/Seoul"))
        log_date = dt.strftime("%Y%m%d")
        logging.basicConfig(filename="logs/" + log_date + "log.log", level=logging.DEBUG)

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


# 색칠 함수
def color(string, start_color=Colors.RESET):
    return start_color + string + Colors.RESET


# MANAGE 페이지에서 쓰임
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


# collection => dict 변환
def manage_helper(data):
    return_dict = {}
    for key in data.keys():
        return_dict[key] = {
            "last": time_passed(data[key]["last"]),
            "url": data[key]["url"],
            "id": data[key]["id"]
        }
    return return_dict


# 로그인되어있다면 아이디, 아니면 False
def is_logined(s):
    if s["userid"] == None:
        return False
    else:
        return s["userid"]


# post 여러개 올리기
def mongodb_test():
    client = MongoClient("mongodb://localhost:27017/")
    database = client["sol"]
    posts = database["posts"]


    num = 100

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

# post 여러개 올리기
def mongodb_test():
    client = MongoClient("mongodb://localhost:27017/")
    database = client["sol"]
    posts = database["posts"]


    num = 100

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


# 모든 연결에 대해 실행
@app.before_request
def before_all_connect_():
    ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    # 블랙리스트면 403 띄우기
    if ip in black_list:
        abort(403)

    # 로그 출력이 필요없는 url로 접근할때 그냥 return
    for connect in IgnoreConnect:
        if connect in request.full_path:
            return

    # 로그인이 아직 안됐을때 None을 아이디로
    if "userid" not in session.keys():
        session["userid"] = None

    # 마지막 접속 기록을 남김
    ips[ip] = {
        "last": time.time(),
        "url": request.full_path,
        "id": session["userid"]
    }

    # ip와 접근 url 출력
    print(ip, request.full_path)

    # 로그인이 필요없으면 return
    for page in NoLoginPages:
        if page == request.full_path:
            return

    # 로그인이 필요하면 /login으로 redirect
    if not is_logined(session):
        return redirect("/login")


# 홈
@app.route("/")
@app.route("/home")
def index_page():
    if "kakaotalk-callback." in str(request):
        return "ok"
    return render_template("index.html", logined=is_logined(session))





# 관리자 페이지
@app.route("/manage", methods=["POST", "GET"])
def manage():
    if session['userid'] == "관리자" or session['userid'] == "admin":
        # /manage?cmd=어쩌구 처리
        if request.args.get("cmd"):
            cmd = request.args.get("cmd").split()

            # 로그 삭제
            if cmd[0] == "del":
                del ips[cmd[1]]

            # 블랙리스트
            elif cmd[0] == "block":
                if cmd[1] != "192.168.0.1":
                    black_list.append(cmd[1])
                else:
                    flash("관리자는 차단할 수 없습니다")

            # 블랙리스트 해제
            elif cmd[0] == "unblock":
                black_list.remove(cmd[1])

            elif cmd[0] == "do":
                if cmd[1] == "db_test":
                    mongodb_test()

            elif cmd[0] == "do":
                if cmd[1] == "db_test":
                    mongodb_test()

            return redirect("/manage")

        return_dict = manage_helper(ips)

        # CREATE HTML
        return_str = ""
        for key in return_dict.keys():
            return_str += key \
                          + "\n&nbsp;&nbsp;ID    : " \
                          + str(return_dict[key]["id"]) \
                          + "\n&nbsp;&nbsp;URL  : " \
                          + return_dict[key]["url"] \
                          + "\n&nbsp;&nbsp;TIME : " \
                          + return_dict[key]["last"] \
                          + "\n\n"
        return_str += "\n블랙리스트 : " + str(black_list)

        return render_template("manage.html", ips=return_str.replace("\n", "<br>").replace(" ", "&nbsp;"))
    else:
        abort(403)


# 로그인
@app.route("/login", methods=['POST', 'GET'])
def login():
    form = LoginForm()

    if request.method == "GET":
        return render_template("login.html", form=form)

    elif request.method == "POST":
        # db 연결
        client = MongoClient("mongodb://localhost:27017/")
        posts = client.sol.users
        # 입력값 불러오기
        id_ = form.data.get('id')
        pw = form.data.get('pw')
        data = posts.find({"id": id_})

        # db 연결 종료
        client.close()

        # 정보 검색
        login_data = {}
        i = 0
        for d in data:
            login_data[str(i)] = d

        # 아이디가 존재하지 않음
        if len(login_data) != 1:
            return redirect("/login")

        # 비밀번호가 안맞음
        if login_data["0"]["pw"] != pw:
            return redirect("/login")

        # 통과
        else:
            session['userid'] = id_
            return redirect("/")


# 회원가입
@app.route("/signup", methods=["GET", "POST"])
def signup():
    ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    if is_logined(session):
        flash("이미 로그인되어있습니다.")
        return redirect("/")

    form = RegisterForm()
    if request.method == "GET":
        return render_template("signup.html", form=form)

    elif request.method == "POST":
        client = MongoClient("mongodb://localhost:27017/")
        database = client["sol"]
        users = database["users"]
        data = users.find({"id": form.data.get('id')})
        login_data = {}
        i = 0
        print(form.data.get('id'), form.data.get('pw'), form.data.get('name'))
        for d in data:
            login_data[str(i)] = d

        # 아이디가 존재하지 않음
        if len(login_data) != 1:
            if form.data.get('pw') != form.data.get('re_password'):
                flash('비밀번호가 일치하지 않습니다')
                return render_template('signup.html', form=form)

            if len(form.data.get('pw')) < 10:
                flash("비밀번호는 10글자 이상으로 해주세요")
                return render_template("signup.html", form=form)
            users.insert_one(
                {
                    "id": form.data.get('id'),
                    "pw": form.data.get('pw'),
                    "ip": ip,
                    "name": form.data.get('name'),
                    "status_messages": "상태메시지가 없습니다."
                }
            )
            client.close()
            return redirect("/login")
        else:
            flash("해당 아이디는 이미 사용중입니다.")
            return render_template("signup.html", form=form)


# 로그아웃
@app.route("/logout")
def logout():
    if not is_logined(session):
        return redirect("/login")
    if is_logined(session):
        del session['userid']
        return redirect("/")
    else:
        return redirect("/login")


# 페이지가 지정 안됐을 때 redirect
@app.route("/board/")
@app.route("/board/list")
def index_of_board():
    return redirect("/board/list/1")


# 게시판 - 목록
@app.route("/board/list/<index_num>")
def pages_(index_num):
    if not is_logined(session):
        return redirect("/login")
    client = MongoClient("mongodb://localhost:27017/")
    posts = client.sol.posts
    i = int(index_num) * 20 - 20
    return_posts = {}

    for post_ in posts.find({
        'url': {
            '$gt': posts.estimated_document_count() - (int(index_num) * 20 + 1),
            '$lt': posts.estimated_document_count() - (int(index_num) * 20 - 21)
            }}).sort("url", -1):
        return_posts[post_['url']] = post_['title'], post_['url'], post_['time'], post_['author']
        i += 1

    client.close()
    return render_template("board/index.html",
                           posts=return_posts,
                           length=list(return_posts.keys()),
                           page=int(index_num)
                           )


# TODO : 보안 취약
# 글 쓰기
@app.route("/board/new", methods=['POST', 'GET'])
def new():
    if request.method == "GET":
        return render_template("board/new.html")
    content = str(request.form.get('content'))
    if not content:
        flash("내용을 입력해주세요")
        return render_template("board/new.html")
    if not request.form.get('title'):
        flash("제목을 입력해주세요")
        return render_template("board/new.html")

    ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    client = MongoClient("mongodb://localhost:27017/")
    posts = client.sol.posts
    content = str(request.form.get('content'))
    if "<br>" not in content:
        content = content.replace("\n", "<br>")

    posts.insert_one(
        {
            "title": request.form.get('title'),
            "author": session['userid'],
            "content": content,
            "url": posts.estimated_document_count() + 1,
            "time": time.strftime('%c', time.localtime(time.time())),
            "ip": ip
        }
    )
    client.close()
    return redirect("/board/list")


# 글 보기 (조회)
@app.route("/board/post/<id_>")
def post(id_):
    if not is_logined(session):
        return redirect("/login")

    client = MongoClient("mongodb://localhost:27017/")
    posts = client.sol.posts
    data = posts.find({"url": int(id_)})
    posts_count = posts.estimated_document_count()
    client.close()
    try:
        return render_template("board/post.html", post=data[0], page=(posts_count - data[0]["url"]) // 20 + 1)
    except KeyError:
        return redirect("/err/404")


# 글 삭제
@app.route("/board/post/<id_>/delete")
def delete_post(id_):
    client = MongoClient("mongodb://localhost:27017/")
    posts = client.sol.posts
    data = posts.find({"url": int(id_)})
    client.close()
    if session['userid'] == data[0]['author']:
        posts.delete_one({"url": int(id_)})
        flash("삭제됐습니다")
        return redirect("/board/list")
    else:
        flash("권한이 없습니다")
        return redirect("/board/post/" + id_)





# TODO : 보안 취약
# 인공지능
@app.route("/ai", methods=['POST', 'GET'])
def ai_page():
    if request.method == "GET":
        return render_template("ai/index.html")
    else:
        upload_file = request.files.get('file', None)
        if mimetypes.guess_type(secure_filename(upload_file.filename)) == ('image/jpeg', None):
            id_ = len(os.listdir("ai/result")) + 1
            filename = str(id_) + ".jpg"
            save_file_path = os.path.join(app.config['UPLOAD_DIR'], filename)
            upload_file.save(save_file_path)

            os.system("start python ai.py %s %d %s" % (save_file_path, id_, session['userid']))
            return redirect("/ai/wait/" + str(id_))

        else:
            black_list.append(request.environ.get('HTTP_X_REAL_IP', request.remote_addr))
            return "해킹 시도 감지됨."

# 인공지능 결과 나올때까지 대기
@app.route("/ai/wait/<id_>")
def ai_wait(id_):
    if os.path.isfile("ai/result/" + id_ + ".txt"):
        return redirect("/ai/result/" + id_)

    else:
        return render_template("ai/wait.html")


# 인공지능 결과
@app.route("/ai/result/<id_>")
def ai_result(id_):
    if os.path.isfile("ai/result/" + id_ + ".txt"):
        result = eval(open("ai/result/" + id_ + ".txt", "r").read())
        if session["userid"] == result[-100]:
            return render_template("ai/result.html", max_=result[max(result.keys())],
                                   confidence=round(max(result.keys()), 3), img=result[-101])
        return "다른 사람의 결과는 볼 수 없습니다."

    return "잘못된 결과 id 입니다."


# 내 프로필
@app.route("/my-profile")
def my_profile():
    ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    client = MongoClient("mongodb://localhost:27017/")
    users = client.sol.users
    data = users.find({"id": session['userid']})
    # db 연결 종료
    client.close()

    # 정보 검색
    profile_data = {}
    i = 0
    for d in data:
        profile_data[str(i)] = d

    return render_template("profile/my_profile.html",
                           profile=profile_data["0"],
                           ip=ip
                           )


# 내 프로필 수정
@app.route("/my-profile-edit", methods=["POST", "GET"])
def edit_profile():
    if request.method == "GET":
        client = MongoClient("mongodb://localhost:27017/")
        users = client["sol"]["users"]
        data = users.find({"id": session['userid']})
        # db 연결 종료
        client.close()

        # 정보 검색
        profile_data = {}
        i = 0
        for d in data:
            profile_data[str(i)] = d

        return render_template("profile/edit.html", profile=profile_data["0"])
    elif request.method == "POST":
        status_message = request.form.get('status_message')
        print(status_message)
        client = MongoClient("mongodb://localhost:27017/")
        users = client.sol.users
        users.update({"id": session["userid"]}, {"$set": {"status_message": status_message}})
        # db 연결 종료
        client.close()
        return redirect("/my-profile")

# 남의 프로필 보기
@app.route("/profile")
@app.route("/profile/")
@app.route("/profile/<id_>")
def other_profile(id_="관리자"):
    client = MongoClient("mongodb://localhost:27017/")
    users = client.sol.users
    data = users.find({"id": id_})
    # db 연결 종료
    client.close()

    # 정보 검색
    profile_data = {}
    i = 0
    for d in data:
        profile_data[str(i)] = d
        i += 1

    if len(profile_data.keys()) == 0:
        profile_data["0"] = profile={
                                "id": "존재하지 않는 사용자",
                                "status_message": "없음"
                            }
        return render_template("profile/other_profile.html",
                               profile={
                                   "id": "존재하지 않는 사용자",
                                   "status_message": "없음"
                               }
                               )

    return render_template("profile/other_profile.html",
                           profile=profile_data["0"], )

    return render_template("profile/other_profile.html",
                           profile=profile_data["0"], )



# 카카오톡 공유
@app.route("/kakaotalk", methods=["GET", "POST"])
def kakaotalk():
    if request.method == "GET":
        return render_template("kakaotalk/make.html")
    else:
        upload_file = request.files.get('file', None)

        id_ = len(os.listdir("static/upload")) + 1
        filename = str(id_) + ".jpg"
        save_file_path = os.path.join(app.config['UPLOAD_DIR'], filename)
        upload_file.save(save_file_path)\

        Log.log("카카오 링크 전송\ntitle: "
              + str(request.form.get('title')) + " / description : "
              + str(request.form.get('description')) + " / url : "
              + str(request.form.get('url')) + " / path : "
              + save_file_path + " / id : "
              + session["userid"])

        return render_template("kakaotalk/send.html",
                    title=str(request.form.get('title')),
                    description=str(request.form.get('description')),
                    url=str(request.form.get('url')),
                    img_url=save_file_path
                )


@app.route("/redirect")
def redirect_page():
    return redirect(request.args.get('url'))


@app.route("/temp/file/html/guide")
def tmp():
    if request.args.get("key") == "kim-wun-chan":
        return render_template("tmp.html")


# 404 처리
@app.route("/err/404")
@app.errorhandler(404)
def _page_not_found(e=404):
    return "존재하지 않는 페이지입니다. <br>오류 코드 : " + str(e)

#
#
#
#
# # 선언 끝
# APP CONFIG
app.config['SECRET_KEY'] = open("secret_key.txt", "r").read()
app.config["UPLOAD_DIR"] = "static/upload/"

ips = {}

black_list = []

NoLoginPages = [
    "/?",
    "/signup?",
    "/login?"
]

IgnoreConnect = [
    "/static/",
    "/plugin/",
    "/config",
    "/favicon.ico?",
    "/manage",
    "/ai/wait/"
]


Log = Log()
# RUN SERVER
Log.log("server started")
app.run(host='0.0.0.0', port=5000, debug=True)
Log.log("server closed")
