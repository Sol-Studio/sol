from flask import Flask, redirect
app = Flask(__name__)
@app.route("/")
def kakaotalk_callback():
    return redirect("http://sol-studio.kro.kr:5000/kakaotalk-callback")
app.run(host="0.0.0.0", port=4999, debug=False)