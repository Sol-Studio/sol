import os
from flask import request
from flask import session
from flask import redirect
from flask import flash
from flask import send_file
from flask import render_template
from .func import *
import shutil


def drive_path_check(session, full_path_, path_):
    if session["userid"] not in os.path.abspath("drive/%s/%s/%s" % (session["userid"], full_path_, str(path_))):
        return True

    else:
        return False


# drive
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
            return "누구인가 누가 해킹을 하려고 하는가!!!" + os.path.abspath("drive/%s/%s" % (session["userid"], full_path))




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