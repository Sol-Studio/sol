from flask import render_template
def docs_index():
    return render_template("api_docs/index.html")
def docs(file):
    return render_template("api_docs/" + file + ".html")