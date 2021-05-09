from flask import request
from flask import render_template
from flask import redirect
from flask import session
from flask import abort
from .func import *
import pprint

ip_track = {}


def ip_collect_index():
    if request.method == "POST":
        id_ = make_id()
        rd = request.form.get("rd")
        ip_track[id_] = []
        ip_track[id_ + "-rd"] = rd
        return redirect("/ip-collect/view/" + id_)

    else:
        return render_template("ip-track/collect.html")


def view(track_id):
    rd = ip_track[track_id + "-rd"]
    print("http://sol-studio.tk/ip-collect/c?track_id=" + track_id)
    return render_template("ip-track/view.html",
        info=ip_track[track_id],
        url=url_short("http://sol-studio.tk/ip-collect/c?track_id=" + track_id + "_")
    )


def main():
    track_id = request.args.get("track_id")
    rd = ip_track[track_id + "-rd"]
    if track_id in ip_track.keys():
        ip_track[track_id].append(request.environ.get('HTTP_X_REAL_IP', request.remote_addr))
    else:
        ip_track[track_id] = [request.environ.get('HTTP_X_REAL_IP', request.remote_addr)]


    return redirect(rd)


def ip_collect_list():
    if session["userid"] == "admin":
        return pprint.pformat(ip_track).replace("\n", "<br>") + "<br><br>네이버 api 사용량 : <a href='https://developers.naver.com/apps/#/myapps/T_IA04FSNb5FsLtQcqD9/overview'>보기</a>"
    abort(404)
