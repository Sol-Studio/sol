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

    client = MongoClient("mongodb://localhost:27017")
    posts = client.sol.posts
    i = 0
    return_posts = {}
    if request.args.get("tag"):
        for post_ in posts.find().sort('_id', -1):
            if "tags" in post_.keys():
                if request.args.get("tag") in post_["tags"]:
                    if i < (int(index_num)-1) * 20:
                        i += 1
                        continue
                    return_posts[post_['url']] = post_['title'], post_['url'], post_['time'], post_['author']
                    i += 1
                    if len(return_posts.keys()) == 20:
                        break

        client.close()
        if len(return_posts.keys()) == 0:
            abort(404)
        return render_template("board/index.html",
                            posts=return_posts,
                            length=list(return_posts.keys()),
                            page=int(index_num),
                            tag="#" + request.args.get("tag")
                            )


    else:
        for post_ in posts.find().sort('_id', -1).skip((int(index_num) - 1) * 20).limit(50):
            return_posts[post_['url']] = post_['title'], post_['url'], post_['time'], post_['author']
            i += 1

        client.close()
        if len(return_posts.keys()) == 0:
            abort(404)
        
        print(return_posts)
        return render_template("board/index.html",
                            posts=return_posts,
                            length=list(return_posts.keys()),
                            page=int(index_num)
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
    return redirect("/board/list")


def board_upload_image():
    upload_file = request.files.get('file', None)
    file_id = make_id()
    upload_file.save("static/upload/" + str(int(time.time())) + file_id + upload_file.filename[upload_file.filename.rfind("."):])
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
    return send_file("static/upload/" + file)

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