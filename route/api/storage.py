from flask import request
import os
from flask import send_file, jsonify, session
from ..func import *
from pymongo import MongoClient


def register():
    client = MongoClient("mongodb://localhost:27017")
    tokendb = client.dev.token
    try:
        token = list(tokendb.find({"user": session["userid"]}))[0]["token"]
    except:
        return "Get Token First <a href='/developer/get-token'>at here</a>"
    try:
        os.mkdir("D:/storage/" + token)
    except:
        return "Fail"
    return "Success"


def upload():
    file = request.files.get("file")
    full_path = request.form.get("path")
    token = request.form.get("token")
    if not full_path.startswith("/") or "../" in file:
        return "Path Err"
    
    if not token or not os.path.isdir(os.path.join("D:\\storage\\"+token)):
        return "Token Err"

    if not file:
        return "File Err"
    save_path = os.path.join("D:/storage/%s/%s" % (request.form.get("token"), full_path), custom_secure_filename(file.filename))
    file.save(save_path)    
    
    if get_dir_size("D:/storage/" + request.form.get("token")) > 1073741824:
        os.remove(os.path.join(save_path))
        return "Limit Err"

    return "/" + os.path.join(full_path, custom_secure_filename(file.filename))



def download():
    file = request.args.get("file")
    token = request.args.get("token")
    if not file.startswith("/") or "../" in file:
        return "Path Err"

    if not token or not os.path.isdir(os.path.join("D:\\storage\\"+token)):
        return "Token Err"
    if not file:
        return "File Err"

    try:
        return send_file("D:/storage/" + token + file)
    except:
        return "File Err"

def explorer():
    full_path = request.form.get("path")
    token = request.form.get("token")
    if not full_path.startswith("/") or "../" in full_path or token in full_path:
        return "Path Err"
    token = request.form.get("token")
    if not token or not os.path.isdir(os.path.join("D:\\storage\\"+token)):
        return "Token Err"
    return_dict = {"files":{}, "folders":[]}


    for entry in os.listdir("D:/storage/" +  + full_path):
        if os.path.isfile("D:/storage/" + token + full_path + "/" + entry):
            return_dict["files"][entry] = os.path.getsize(os.path.abspath("D:/storage/%s/%s/%s" % (token, full_path, entry)))
        else:
            return_dict["folders"].append(entry)
    return jsonify(return_dict)

def mkdir():
    return ""

def rmdir():
    return ""

def delete_file():
    return ""
