from flask import session
from flask import request
from flask import flash
from flask import redirect
from flask import render_template
from flask import abort
from flask import send_file
from .func import *
import os
import pickle


# 커넥션 로그파일
try:
    ips = pickle.load(open("ips.bin", "rb"))
except FileNotFoundError:
    ips = {}

black_list = []


# 관리자 페이지
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


# 로그 뷰어
def veiw_log(date):
    return send_file("logs/" + date + "log.log")
