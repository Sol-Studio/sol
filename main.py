from werkzeug.utils import secure_filename
import logging
import time
from datetime import datetime
from datetime import timedelta
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
from flask import abort
from flask import send_file
from flask import make_response
from pymongo import MongoClient
import pickle
from werkzeug.debug import DebuggedApplication
import sys
import hashlib
import shutil

# Create Flask App
app = Flask(__name__)
app.config['SECRET_KEY'] = open("secret_key.txt", "r").read()
app.config["UPLOAD_DIR"] = "static/upload/"

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
    "/file-server"
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

# 커넥션 로그파일
try:
    ips = pickle.load(open("ips.bin", "rb"))
except FileNotFoundError:
    ips = {}


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
    if not s["userid"]:
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
        session["userid"] = None

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

    # 로그인이 필요없으면 return
    for i in range(len(NoLoginPages)):
        if NoLoginPages[i] in request.full_path:
            return

    # 로그인이 필요하면 로그인 요청페이지
    if not is_logined(session):
        return redirect("/login")


# 홈 INDEX
@app.route("/")
def index_page():
    if is_logined(session):
        return render_template("index.html")
    else:
        return render_template("index_before_login.html")


# 관리자 페이지
@app.route("/manage")
@app.route("/manage/")
def manage():
    if session['userid'] == "관리자" or session['userid'] == "admin":
        # /manage?cmd=어쩌구 처리
        if request.args.get("cmd"):
            cmd = request.args.get("cmd").split()

            # 로그 삭제
            if cmd[0] == "del":
                try:
                    del ips[cmd[1]]
                    os.remove("hist/%s.bin" % cmd[1])
                except:
                    pass

            # 블랙리스트
            elif cmd[0] == "block":
                black_list.append(cmd[1])

            # 블랙리스트 해제
            elif cmd[0] == "unblock":
                if cmd[1] in black_list:
                    black_list.remove(cmd[1])
                else:
                    flash("블랙리스트에 없습니다")

            # db test
            elif cmd[0] == "do":
                if cmd[1] == "db_test":
                    mongodb_test(int(cmd[2]))
                    flash("완료")
            pickle.dump(ips, open("ips.bin", "wb"))

            return redirect("/manage")

        return_dict = manage_helper(ips)

        return render_template("manage/manage.html", ips=return_dict, keys=return_dict.keys(), blacklist=black_list)
    else:
        abort(403)
        black_list.append(request.environ.get('HTTP_X_REAL_IP', request.remote_addr))


@app.route("/manage/<ip>")
def manage_ip(ip):
    if session['userid'] != "admin":
        return ""
    if request.args.get("cmd"):
        cmd = request.args.get("cmd")
        # 로그 삭제
        if cmd == "del":
            del ips[ip]
            os.remove("hist/%s.bin" % ip)
            flash("완료")
            return redirect("/manage")

        # 블랙리스트
        elif cmd == "block":
            black_list.append(ip)
            flash("완료")

        # 블랙리스트 해제
        elif cmd == "unblock":
            if ip in black_list:
                black_list.remove(ip)
                flash("완료")
            else:
                flash("블랙리스트에 없습니다")

        pickle.dump(ips, open("ips.bin", "wb"))

    if not os.path.isfile("hist/%s.bin" % ip):
        flash("방문 기록이 없습니다.")
        return redirect("/manage")
    return_dict = {}
    hist = pickle.load(open("hist/%s.bin" % ip, "rb"))
    for key in hist.keys():
        return_dict[time_passed(key)] = hist[key]

    return render_template("manage/hist_manage.html", hist=return_dict, keys=reversed(list(return_dict.keys())),
                           blacklist=black_list, ip=ip)


# 로그인
@app.route("/login", methods=['POST', 'GET'])
def login():
    form = LoginForm()

    if request.method == "GET":
        if session['userid']:
            flash("이미 로그인돼있습니다.")
            return redirect("/")
        return render_template("login.html", form=form)

    else:
        # db 연결
        client = MongoClient("mongodb://localhost:27017")
        posts = client.sol.users
        # 입력값 불러오기
        id_ = form.data.get('id')
        pw = form.data.get('pw')
        data = list(posts.find({"id": id_}))
        client.close()

        # 아이디가 존재하지 않음
        if len(data) == 0:
            flash("로그인 정보가 맞지 않습니다.")
            return redirect("/login")

        # 비밀번호가 안맞음
        if data[0]["pw"] != pw:
            flash("로그인 정보가 맞지 않습니다.")
            return redirect("/login")

        # 통과
        else:
            print("login passed")
            session['userid'] = form.data.get('id')
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
        client = MongoClient("mongodb://localhost:27017")
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


# 비밀번호 바꾸기
@app.route("/change-pw", methods=["POST", "GET"])
def change_pw():
    if request.method == "POST":
        client = MongoClient("mongodb://localhost:27017")
        db = client.sol.users
        profile = list(db.find({"id": session["userid"]}))[0]
        if profile["pw"] == request.form.get("last_pw") and request.form.get("new_pw") == request.form.get(
                "new_pw_again"):
            db.update({"id": session["userid"]}, {"$set": {"pw": request.form.get("new_pw")}})
            flash("완료")
            print("hello")
            return redirect("/my-profile")

        else:
            flash("다시 시도해주세요")
            return redirect("/change-pw")
    else:
        return render_template("profile/change-pw.html")


# 페이지가 지정 안됐을 때 redirect
@app.route("/board/")
@app.route("/board/list")
def index_of_board():
    return redirect("/board/list/1")


# 게시판 - 목록
@app.route("/board/list/<index_num>")
def pages_(index_num):
    if int(index_num) < 1:
        return redirect("/board/list/1")
    client = MongoClient("mongodb://localhost:27017")
    posts = client.sol.posts
    i = int(index_num) * 20 - 20
    return_posts = {}

    for post_ in posts.find().sort('_id', -1).skip((int(index_num) - 1) * 20).limit(20):
        return_posts[post_['url']] = post_['title'], post_['url'], post_['time'], post_['author']
        i += 1

    client.close()
    return render_template("board/index.html",
                           posts=return_posts,
                           length=list(return_posts.keys()),
                           page=int(index_num)
                           )


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
    client = MongoClient("mongodb://localhost:27017")
    posts = client.sol.posts
    content = str(request.form.get('content')).replace("\n", "<br>")

    next_id = posts.find().sort('_id', -1)[0]["url"] + 1

    x = datetime.now()
    posts.insert_one({
        "title": request.form.get('title'),
        "author": session['userid'],
        "content": content,
        "url": next_id,
        "time": x.strftime("%Y년 %m월 %d일 %H시 %M분 %S초"),
        "ip": ip
    })

    client.close()
    return redirect("/board/list")


# 글 보기 (조회)
@app.route("/board/list/<idx>/<id_>")
def post(idx, id_):
    client = MongoClient("mongodb://localhost:27017")
    posts = client.sol.posts
    data = posts.find({"url": int(id_)})
    client.close()
    try:
        return render_template("board/post.html", post=data[0], page=int(idx), id=session["userid"])
    except KeyError:
        return redirect("/err/404")


# 글 삭제
@app.route("/board/list/<idx>/<id_>/delete")
def delete_post(idx, id_):
    client = MongoClient("mongodb://localhost:27017")
    posts = client.sol.posts
    data = posts.find({"url": int(id_)})
    client.close()
    if session['userid'] == data[0]['author'] or session["userid"] == "admin":
        posts.delete_one({"url": int(id_)})
        flash("삭제됐습니다")
        return redirect("/board/list")
    else:
        flash("권한이 없습니다")
        return redirect("/board/list/" + idx + "/" + id_)


# 내 프로필
@app.route("/my-profile")
def my_profile():
    ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    client = MongoClient("mongodb://localhost:27017")
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
        client = MongoClient("mongodb://localhost:27017")
        users = client["sol"]["users"]
        data = users.find({"id": session['userid']})
        # db 연결 종료
        client.close()

        # 정보 검색
        profile_data = {}
        i = 0
        for d in data:
            profile_data[str(i)] = d

        return render_template("profile/edit.html", profile=profile_data["0"],
                               ip=request.environ.get('HTTP_X_REAL_IP', request.remote_addr))
    elif request.method == "POST":
        status_message = request.form.get('status_message')
        print(status_message)
        client = MongoClient("mongodb://localhost:27017")
        users = client.sol.users
        users.update({"id": session["userid"]}, {"$set": {"status_message": status_message}})
        # db 연결 종료
        client.close()
        return redirect("/my-profile")


# 남의 프로필 보기
@app.route("/profile/<id_>")
def other_profile(id_):
    client = MongoClient("mongodb://localhost:27017")
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
        profile_data["0"] = {
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


# 카카오톡 공유
@app.route("/kakaotalk", methods=["GET", "POST"])
def kakaotalk():
    if request.method == "GET":
        return render_template("kakaotalk/make.html")

    else:
        upload_file = request.files.get('file', None)

        id_ = len(os.listdir("static/kakaotalk")) + 1
        filename = str(id_) + ".jpg"
        save_file_path = os.path.join("static/kakaotalk/", secure_filename(filename))
        upload_file.save(save_file_path)

        Log.log(""
                + "카카오 링크 전송\ntitle: "
                + str(request.form.get('title')) + " / description : "
                + str(request.form.get('description')) + " / url : "
                + str(request.form.get('url')) + " / path : "
                + save_file_path + " / id : "
                + session["userid"]
                )

        return render_template("kakaotalk/send.html",
                               title=str(request.form.get('title')),
                               description=str(request.form.get('description')),
                               url=str(request.form.get('url')),
                               img_url=save_file_path
                               )


# 리다이렉트
@app.route("/redirect")
def redirect_page():
    return redirect(request.args.get('url'))


# 퀴즈 출제(로그인된 사람만)
@app.route("/quiz", methods=["GET", "POST"])
def quiz_index():
    if request.method == "POST":
        client = MongoClient("mongodb://localhost:27017")
        quizdb = client.sol.quiz
        register_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))

        if request.form.get("qtype") == "0":
            quizdb.insert_one({
                "id": quizdb.find().sort('_id', -1)[0]["id"] + 1,
                "type": request.form.get("qtype"),
                "q": request.form.get("name"),
                "answer": request.form.get("answer_ox"),
                "name": session['userid'],
                "time": register_time
            })

        elif request.form.get("qtype") == "1":
            quizdb.insert_one({
                "id": quizdb.find().sort('_id', -1)[0]["id"] + 1,
                "type": request.form.get("qtype"),
                "q": request.form.get("name"),
                "answer": str(int(request.form.get("answer_is")) + 1),
                "look": [request.form.get("answer_1"), request.form.get("answer_2"), request.form.get("answer_3"),
                         request.form.get("answer_4"), request.form.get("answer_5")],
                "name": session['userid'],
                "time": register_time
            })

        elif request.form.get("qtype") == "2":
            quizdb.insert_one({
                "id": quizdb.find().sort('_id', -1)[0]["id"] + 1,
                "type": request.form.get("qtype"),
                "q": request.form.get("name"),
                "answer": request.form.get("answer"),
                "name": session['userid'],
                "time": register_time
            })

        id_ = str(quizdb.find().sort('_id', -1)[0]["id"])
        client.close()
        return redirect("/quiz/answer?qno=" + id_)

    elif request.method == "GET":
        quiz_type = request.args.get("type")
        if quiz_type == "0":
            return render_template("quiz/make.html", type=["checked=''", "", ""])
        if quiz_type == "1":
            return render_template("quiz/make.html", type=["", "checked=''", ""])
        elif quiz_type == "2":
            return render_template("quiz/make.html", type=["", "", "checked=''"])
        else:
            return redirect("/quiz?type=0")


# 퀴즈 출제자 페이지(admin 은 다 보임)
@app.route("/quiz/answer")
def quiz_answer():
    try:
        if int(request.args.get("qno")) == 0:
            return mobile_meta + "문제 URL이 잘못되었습니다."

    except TypeError:
        return "문제 URL이 잘못되었습니다."

    client = MongoClient("mongodb://localhost:27017")
    answers = list(client.sol.quiz_answer.find({"id": int(request.args.get("qno"))}))
    try:
        quiz = client.sol.quiz.find({"id": int(request.args.get("qno"))})[0]
        client.close()

    except IndexError:
        client.close()
        return mobile_meta + "문제 URL이 잘못되었습니다."

    if session['userid'] == quiz["name"] or session['userid'] == "admin":
        return render_template("quiz/answer.html", q=quiz, answers=answers, length=len(answers))
    else:
        flash("로그인이 필요합니다")
        return redirect("/login")


# 퀴즈 푸는 페이지
@app.route("/quiz/question", methods=['GET', "POST"])
def quiz_question():
    if request.method == "GET":
        try:
            if int(request.args.get("qno")) == 0:
                return mobile_meta + "문제 URL이 잘못되었습니다."

        except TypeError:
            return mobile_meta + "문제 URL이 잘못되었습니다."

        client = MongoClient("mongodb://localhost:27017")
        quizdb = client.sol.quiz

        try:
            quiz = quizdb.find({"id": int(request.args.get("qno"))})[0]
            client.close()

        except IndexError:
            client.close()
            return mobile_meta + "문제 URL이 잘못되었습니다."

        if "name" not in session.keys():
            session['name'] = "이름을 입력해주세요"
        return render_template("quiz/question.html", q=quiz, name=session['name'], close=False)

    else:
        try:
            int(request.args.get("qno"))

        except TypeError:
            return mobile_meta + "문제 URL이 잘못되었습니다."

        client = MongoClient("mongodb://localhost:27017")
        quizdb = client.sol.quiz
        quiz_answerdb = client.sol.quiz_answer
        quiz = quizdb.find({"id": int(request.args.get("qno"))})[0]
        answer_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        session['name'] = request.form.get("name")

        quiz_answerdb.insert_one({
            "id": int(request.args.get("qno")),
            "name": request.form.get("name"),
            "time": answer_time,
            "answer": request.form.get("answer_is")
        })

        client.close()
        if request.form.get("answer_is") == quiz["answer"]:
            flash("정답입니다!")

        else:
            if quiz["type"] == "1":
                flash("안타깝게도 오답입니다! 정답은 %s번 입니다!" % quiz["answer"])
            else:
                flash("안타깝게도 오답입니다! 정답은 %s 입니다!" % quiz["answer"])

        return render_template("quiz/question.html", q=quiz, name=session['name'], close=True)


# 출제한 퀴즈 목록(admin 은 다 보임)
@app.route("/quiz/list")
def quiz_list():
    client = MongoClient("mongodb://localhost:27017")
    if session["userid"] == "admin":
        given_quiz_list = list(client.sol.quiz.find())
    else:
        given_quiz_list = list(client.sol.quiz.find({"name": session["userid"]}))
    client.close()
    return render_template("quiz/list.html", l=given_quiz_list, length=len(given_quiz_list), name=session['userid'])


# 퀴즈 삭제(admin 만 가능)
@app.route("/quiz/del")
def quiz_del():
    if session["userid"] == "admin":
        try:
            if int(request.args.get("qno")) == 0:
                return mobile_meta + "문제 URL이 잘못되었습니다."

        except TypeError:
            return mobile_meta + "문제 URL이 잘못되었습니다."

        client = MongoClient("mongodb://localhost:27017")
        quizdb = client.sol.quiz
        quiz_answerdb = client.sol.quiz_answer
        target = {"id": int(request.args.get("qno"))}
        length = len(list(quiz_answerdb.find(target)))

        if len(list(quizdb.find(target))) == 0:
            flash("대상이 없습니다.")
            return redirect("/")

        quizdb.remove(target)
        quiz_answerdb.remove(target)
        flash("성공했습니다 : 1개의 퀴즈, %d개의 응답을 삭제함." % length)
        return redirect("/")

    else:
        flash("삭제는 관리자에게 문의하세요(db 꼬임 방지)")
        return redirect("/")


@app.route("/file-server/upload", methods=["POST"])
def file_server_upload():
    upload_file = request.files.get('file', None)
    upload_file.save("static/upload/" + request.form.get("id"))
    print(request.form.get("id"))
    return make_response(200)


@app.route("/file-server/download", methods=["GET"])
def file_server_download():
    return send_file("static/upload/" + request.args.get("id"),
                     attachment_filename=request.args.get("id"))


# chat
#   index
@app.route("/chat")
def chat_index():
    return render_template("chat/index.html")


#   room
@app.route("/chat/<room>")
def chat_room(room):
    client = MongoClient("mongodb://localhost:27017")
    if room in client["chat"].collection_names():
        h = hashlib.sha1()
        h.update(list(client["chat"]["index"].find({"room": room}))[0]["pw"].encode())
        if str(h.hexdigest()) == request.args.get("pw"):
            return render_template("chat/chat.html", room=room, userid=session["userid"])

    return render_template("err/chat-no-room.html")


def drive_path_check(session, full_path_, path_):
    if "게시판\\drive\\" + session["userid"] not in os.path.abspath("drive/%s/%s/%s" % (session["userid"], full_path_, str(path_))):
        return True
    return False


# drive
@app.route("/drive", methods=["GET", "POST"])
def drive():
    full_path = request.args.get("path")

    if not full_path:
        full_path = ""

    if request.method == "POST":
        files = request.files.getlist("file[]")
        for file in files:
            file.save(
                os.path.join("drive/%s/%s" % (session["userid"], full_path), custom_secure_filename(file.filename)))

        if get_dir_size("drive/" + session["userid"]) > 1000000000:
            os.remove(
                os.path.join("drive/%s/%s" % (session["userid"], full_path), custom_secure_filename(file.filename)))
            return redirect("/drive?path=" + full_path + "&overflow=yes")

        return redirect("/drive?path=" + full_path)

    else:

        # path check
        if drive_path_check(session, full_path, "")\
            or drive_path_check(session, full_path, request.args.get("file"))\
            or drive_path_check(session, full_path, request.args.get("mkdir"))\
            or drive_path_check(session, full_path, request.args.get("rmdir"))\
            or drive_path_check(session, full_path, request.args.get("del")):
            return "누구인가 누가 해킹을 하려고 하는가!!!"




        # 그 사람 폴더 없으면 생성
        if not os.path.isdir("drive/" + session["userid"]):
            os.mkdir("drive/" + session["userid"])




        if request.args.get("mkdir"):
            try:
                os.mkdir("drive/%s/%s/%s" % (session["userid"], full_path, request.args.get("mkdir")))
                return redirect("/drive?path=" + full_path)

            except:
                flash("같은 이름의 폴더가 이미 있거나 폴더 이름으로 사용할 수 없는 기호가 포함돼있습니다.")
                return redirect("/drive?path=" + full_path)



        if request.args.get("rmdir"):
            shutil.rmtree("drive/%s/%s/%s" % (session["userid"], full_path, request.args.get("rmdir")))
            return redirect("/drive?path=" + full_path)



        if request.args.get("del"):
            try:
                os.remove("drive/%s/%s/%s" % (session["userid"], full_path, request.args.get("del")))
                return redirect("/drive?path=" + full_path)
            except:
                flash("해당 파일이 없거나 오류가 발생했습니다.")
                return redirect("/drive?path=" + full_path)



        if request.args.get("overflow"):
            flash("사용 가능한 용량을 초과했습니다.")
            return ""



        if request.args.get("file"):
            try:
                return send_file("drive/" + session["userid"] + "/" + request.args.get("file"), as_attachment=True)

            except:
                return ""



        # 상위폴더 경로
        if "/" not in full_path:
            upper = None
        else:
            upper = full_path[:full_path.find("/")]

        # file, dir list
        tmp = os.listdir("drive/%s/%s" % (session["userid"], full_path))
        dirs = {}
        files = {}

        for dir_ in tmp:
            if os.path.isdir("drive/%s/%s" % (session["userid"], full_path) + "/" + dir_):
                dirs[dir_] = get_dir_size(os.path.abspath("drive/%s/%s/%s" % (session["userid"], full_path, dir_)))
                tmp.remove(dir_)

        for file in tmp:
            files[file] = os.path.getsize(os.path.abspath("drive/%s/%s/%s" % (session["userid"], full_path, file)))

        full_path_l = full_path.split("/")
        try:
            full_path_l.remove("")
        except:
            pass
        full_path_l = [session["userid"]] + full_path_l

        paths = ["", ""]
        for i in full_path_l[1:]:
            paths.append(paths[-1] + "/" + i)

        return render_template("drive/index.html",
                                files=files,
                                dirs=dirs,
                                full_path=full_path,
                                full_path_l=full_path_l,
                                upper=upper,
                                paths=paths[1:],
                                paths_len=len(paths)
                                )


# TOOL
#   index
@app.route("/tools")
@app.route("/tools/")
def tools_index():
    return render_template("tools/index.html")


#   wtool
@app.route("/tools/w/<tool>")
def tools_w(tool):
    try:
        return render_template("tools/" + tool + ".html")

    except:
        return render_template("err/common.html", err_code="404", err_message="원하시는 페이지를 찾을 수 없습니다.")


#   ptool
@app.route("/tools/p/<tool>")
def tools_p(tool):
    try:
        return send_file(
            "templates/tools/p/" + tool,
            attachment_filename=tool,
            as_attachment=True
        )

    except:
        return render_template("err/common.html", err_code="404", err_message="원하시는 페이지를 찾을 수 없습니다.")


# intro
@app.route("/intro")
def intro():
    return render_template("intro.html")


#
#
#
#
#
#
# errorhandler
# 404
@app.errorhandler(404)
def error_404(e):
    return render_template("err/common.html", err_code="404", err_message="원하시는 페이지를 찾을 수 없습니다.")


# 500
@app.errorhandler(500)
def error_500(e):
    return render_template("err/common.html", err_code="500", err_message="서버 내부 오류가 발견됐습니다.")


# 403
@app.errorhandler(403)
def error_500(e):
    return render_template("err/common.html", err_code="403", err_message="접근 권한이 없습니다.")


#
#
#
#
#
#
#
#
# SERVER RUN
Log = Log()
Log.log("server restarted")
app.run(host="0.0.0.0", port=80, debug=is_debug)

# SERVER CLOSED
pickle.dump(ips, open("ips.bin", "wb"))
print("saved")
