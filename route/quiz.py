from flask import request
from flask import session
from pymongo import MongoClient
from flask import flash
from flask import render_template
from flask import redirect
import time
mobile_meta = '<meta name=\'viewport\' content=\'width=device-width, initial-scale=1, user-scalable=no\' />'


# 퀴즈 출제(로그인된 사람만)
def make():
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

def answer():
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
def question():
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
def list():
    client = MongoClient("mongodb://localhost:27017")
    if session["userid"] == "admin":
        given_quiz_list = list(client.sol.quiz.find())
    else:
        given_quiz_list = list(client.sol.quiz.find({"name": session["userid"]}))
    client.close()
    return render_template("quiz/list.html", l=given_quiz_list, length=len(given_quiz_list), name=session['userid'])


# 퀴즈 삭제(admin 만 가능)
def delete():
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