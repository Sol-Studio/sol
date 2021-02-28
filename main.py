# 커스텀 모듈
from sol import *

# 일반 모듈
from flask import Flask
from flask import render_template
from flask import redirect
from flask import request
from flask import session
from flask import flash
from pymongo import MongoClient

# Create Flask App
app = Flask(__name__)

ips = {}
NoLoginPages = [
    "/?",
    "/signup?",
    "/login?",
]

IgnoreConnect = [
    "/static/",
    "/plugin/",
    "/config",
    "/favicon.ico?",
    "/manage",
    "/ai/wait/"
]


@app.before_request
def all_connect_():
    ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    for connect in IgnoreConnect:
        if connect in request.full_path:
            return

    if "userid" not in session.keys():
        session["userid"] = None

    ips[ip] = {
        "last": time.time(),
        "url": request.full_path,
        "id": session["userid"]
    }
    print(ip, request.full_path)
    for page in NoLoginPages:
        if page == request.full_path:
            return

    if not is_logined(session):
        return redirect("/login")


def manager_pages():
    # 관리자 페이지
    @app.route("/manage")
    def manage():
        if session['userid'] == "관리자" or session['userid'] == "admin":
            if request.args.get("cmd"):
                cmd = request.args.get("cmd").split()
                if cmd[0] == "del":
                    del ips[cmd[1]]
                return redirect("/manage")

            return_dict = manage_helper(ips)
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

            return render_template("manage.html", ips=return_str.replace("\n", "<br>").replace(" ", "&nbsp;"))
        else:
            return redirect("/login")


@app.route("/")
def index_pages():
    return render_template("index.html", logined=is_logined(session))


def about_login():
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
            # form
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
                        "name": form.data.get('name')
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


def board_pages():
    # /board
    @app.route("/board/")
    @app.route("/board/list")
    def index_of_board():
        return redirect("/board/list/1")

    # board/list/
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
        client.close()
        try:
            return render_template("board/post.html", post=data[0], page=data[0]["url"] // 20 + 1)
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


def ai_pages():
    @app.route("/ai", methods=['POST', 'GET'])
    def ai_page():
        if request.method == "GET":
            return render_template("ai/index.html")
        else:
            f = request.files['file']
            f_name = str(len(os.listdir("static/upload")) + 1) + ".jpg"
            path = os.path.join(app.config['UPLOAD_DIR'], f_name)
            f.save(path)
            id_ = len(os.listdir("ai/result")) + 1
            os.system("start python multi.py %s %d %s" % (path, id_, session['userid']))

            return redirect("/ai/wait/" + str(id_))

    @app.route("/ai/wait/<id_>")
    def ai_wait(id_):
        if os.path.isfile("ai/result/" + id_ + ".txt"):
            return redirect("/ai/result/" + id_)

        else:
            return render_template("ai/wait.html")

    @app.route("/ai/result/<id_>")
    def ai_result(id_):
        if os.path.isfile("ai/result/" + id_ + ".txt"):
            result = eval(open("ai/result/" + id_ + ".txt", "r").read())
            if session["userid"] == result[-100]:
                return render_template("ai/result.html", max_=result[max(result.keys())],
                                       confidence=round(max(result.keys()), 3), img=result[-101])
            return "다른 사람의 결과는 볼 수 없습니다."

        return "잘못된 결과 id 입니다."


def error_handler():
    # 404
    @app.route("/err/404")
    @app.errorhandler(404)
    def _page_not_found():
        return "존재하지 않는 페이지입니다. "


# run server
if __name__ == "__main__":
    manager_pages()
    about_login()
    board_pages()
    ai_pages()
    Log.log("server started")

    app.config['SECRET_KEY'] = open("secret_key.txt", "r").read()
    app.config["UPLOAD_DIR"] = "static/upload/"
    app.run(host='0.0.0.0', port=5000, debug=True)
    Log.log("server closed")
