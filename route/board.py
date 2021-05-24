from pymongo import MongoClient
from flask import render_template
from flask import redirect
from flask import request
from flask import session
from flask import flash
from flask import abort
from flask import send_file
from .func import *


# 페이지가 지정 안됐을 때 redirect
def index():
    return redirect("/board/list/1")


# 게시판 - 목록
def pages_(index_num):
    try:
        if int(index_num) < 1:
            return redirect("/board/list/1")
    except:
        return redirect("/board/list/1")


    tag = request.args.get("tag")
    if not tag:
        tag = ""
    return render_template("board/index.html",
        page=int(index_num),
        tag=tag
    )


# 글 쓰기
def new():
    if request.method == "GET":
        return render_template("board/new.html", submit="/board/new")
    content = str(request.form.get('content')).replace("\n", "<br>").replace("<script", "&lt;script")

    if not content:
        flash("내용을 입력해주세요")
        return render_template("board/new.html")
    if not request.form.get('title'):
        flash("제목을 입력해주세요")
        return render_template("board/new.html")
    
    ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    client = MongoClient("mongodb://localhost:27017")
    posts = client.sol.posts
    

    next_id = posts.find().sort('_id', -1)[0]["url"] + 1

    posts.insert_one({
        "title": request.form.get('title'),
        "author": session['userid'],
        "content": content,
        "tags": request.form.get("tag").split(","),
        "url": next_id,
        "time": Log.get_log_date(),
        "ip": ip
    })

    client.close()
    return redirect("/board/list/1")


def board_upload_image():
    upload_file = request.files.get('file', None)
    file_id = make_id()
    upload_file.save("D:/storage/nSP3uhFQ2TKi4XdfiV4coS5Od5KyUtRQzw937vGxAoi5Y1n8QIr52Kqp6HyVmqdfzoXm170OpdNZ6cfyIHA2EjbByZpVTurL9S9T/board" + str(int(time.time())) + file_id + upload_file.filename[upload_file.filename.rfind("."):])
    return "/board/file/" + str(int(time.time())) + file_id + upload_file.filename[upload_file.filename.rfind("."):]


# 글 보기 (조회)
def post(id_):
    client = MongoClient("mongodb://localhost:27017")
    posts = client.sol.posts
    data = posts.find({"url": int(id_)})
    client.close()
    if "b_page" not in session.keys():
        session["b_page"] = 0
    try:
        return render_template("board/post.html", post=data[0], page=int(session["b_page"]), id=session["userid"])
    except:
        return abort(404)


# 파일 로드
def board_file(file):
    return send_file("D:/storage/nSP3uhFQ2TKi4XdfiV4coS5Od5KyUtRQzw937vGxAoi5Y1n8QIr52Kqp6HyVmqdfzoXm170OpdNZ6cfyIHA2EjbByZpVTurL9S9T/board" + file)

# 글 삭제
def delete_post(id_):
    client = MongoClient("mongodb://localhost:27017")
    posts = client.sol.posts
    data = posts.find({"url": int(id_)})
    client.close()
    if session['userid'] == data[0]['author'] or session["userid"] == "admin":
        posts.delete_one({"url": int(id_)})
        client.sol.comments.delete_many({"url": "/board/post/" + id_})
        flash("삭제됐습니다")
        return redirect("/board/list")
    else:
        flash("권한이 없습니다")
        return redirect("/board/post/" + id_ + session["b_page"])


# 글 수정
def post_edit(id_):
    client = MongoClient("mongodb://localhost:27017")
    posts = client.sol.posts
    data = posts.find({"url": int(id_)})[0]
    
    if request.method == "GET":
        client.close()
        return render_template("board/new.html", submit="/board/post/edit/" + id_,
            content=data["content"],
            title=data["title"])
    else:
        posts.update({"url": int(id_)}, 
            {"title": request.form.get("title"),
            "content": request.form.get("content"),
            "time": data["time"],
            "author": data["author"],
            "url": data["url"],
            "ip": data["ip"] + ", " + request.environ.get('HTTP_X_REAL_IP', request.remote_addr) + "에서 수정"}, False, True)
        return redirect("/board/post/" + str(data["url"]))
    

def post_list(page):
    client = MongoClient("mongodb://localhost:27017")
    posts = client.sol.posts
    return_posts = ""
    tag = request.args.get("tag")
    i = 0
    if tag:
        for post_ in posts.find({"tags": {"$all": [tag]}}).sort('_id', -1).skip((int(page) - 1) * 50).limit(50):
            return_posts += '<a href="/board/post/' + str(post_["url"]) + '"></a><tr id="' + str(post_["url"]) + '" onclick="window.location = \'/board/post/' + str(post_["url"]) + '\'"><td>' + post_["title"] + '</td><td>' + post_["author"] + '</td><td>' + str(post_["time"]) + '</td></tr>'
        client.close()
        if return_posts:
            return return_posts
        else:
            return ""
    else:
        i = 0
        for post_ in posts.find().sort('_id', -1).skip((int(page) - 1) * 50).limit(50):
            return_posts += '<a href="/board/post/' + str(post_["url"]) + '"></a><tr id="' + str(post_["url"]) + '" onclick="window.location = \'/board/post/' + str(post_["url"]) + '\'"><td>' + post_["title"] + '</td><td>' + post_["author"] + '</td><td>' + str(post_["time"]) + '</td></tr>'
            i += 1
        client.close()
        if not return_posts:
            return ""
        return return_posts
