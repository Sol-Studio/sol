from flask import render_template
from flask import send_file


def tools_index():
    return render_template("tools/index.html")


def tools_w(tool):
    try:
        return render_template("tools/" + tool + ".html")

    except:
        return render_template("err/common.html", err_code="404", err_message="원하시는 페이지를 찾을 수 없습니다.")


def tools_p(tool):
    try:
        return send_file(
            "templates/tools/p/" + tool,
            attachment_filename=tool,
            as_attachment=True
        )

    except:
        return render_template("err/common.html", err_code="404", err_message="원하시는 페이지를 찾을 수 없습니다.")
