from .func import *
from flask import request
from flask import render_template
from flask import flash
from flask import session
from flask import redirect
from pymongo import MongoClient


# 로그인
def login():
    form = LoginForm()
    if request.method == "GET":
        if is_logined(session):
            flash("이미 로그인돼있습니다.")
            return redirect("/")
        if request.args.get("next"):
            return render_template("login.html", form=form, action="/login?next=" + request.args.get("next"))
        else:
            return render_template("login.html", form=form, action="/login?next=/")
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
            return redirect(request.args.get("next"))


# 회원가입
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
                client.close()
                return render_template('signup.html', form=form)

            if len(form.data.get('pw')) < 10:
                flash("비밀번호는 10글자 이상으로 해주세요")
                client.close()
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
            client.close()
            return render_template("signup.html", form=form)


# 로그아웃
def logout():
    if not is_logined(session):
        return redirect("/login")
    if is_logined(session):
        del session['userid']
        return redirect("/")
    else:
        return redirect("/login")


# 비밀번호 바꾸기
def change_pw():
    if request.method == "POST":
        client = MongoClient("mongodb://localhost:27017")
        db = client.sol.users
        profile = list(db.find({"id": session["userid"]}))[0]
        if profile["pw"] == request.form.get("last_pw") and request.form.get("new_pw") == request.form.get("new_pw_again"):
            db.update({"id": session["userid"]}, {"$set": {"pw": request.form.get("new_pw")}})
            flash("완료")
            client.close()
            return redirect("/my-profile")

        else:
            flash("다시 시도해주세요")
            client.close()
            return redirect("/change-pw")
    else:
        return render_template("profile/change-pw.html")


# 내 프로필
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
def other_profile(id_):
    if id_[:6] == "guest-":
        return render_template("profile/other_profile.html",
            profile={
                "id": "게스트",
                "status_message": "없음"
            }
        )
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
