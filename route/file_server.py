from flask import request
from flask import send_file
from flask import make_response


def file_server_upload():
    upload_file = request.files.get('file', None)
    upload_file.save("static/upload/" + request.form.get("id"))
    print(request.form.get("id"))
    return make_response(200)


def file_server_download():
    return send_file("static/upload/" + request.args.get("id"),
                     attachment_filename=request.args.get("id"))