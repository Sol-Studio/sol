from flask import redirect
from flask import request
from flask import render_template


# 리다이렉트
def redirect_page():
    return redirect(request.args.get('url'))


def intro():
    return render_template("intro.html")