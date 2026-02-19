from flask import Flask, request, jsonify, render_template_string, Response
from datetime import datetime
import sqlite3

app = Flask(__name__)

# 初始化数据库
def init_db():
    conn = sqlite3.connect("checkin.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL,
            scan_time TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

# 首页（扫码页面）
@app.route("/")
def home():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>扫码打卡系统</title>
    </head>
    <body>
        <h2>扫码打卡</h2>
        <input type="text" id="code" autofocus placeholder="请扫码">
        <p id="result"></p>
        <br>
        <a href="/records">查看记录</a> |
        <a href="/download">下载CSV</a>

        <script>
        const input = document.getElementById("code");

        input.addEventListener("keypress", function(e) {
            if (e.key === "Enter") {
                submitCode();
            }
        });

        function submitCode() {
            let code = input.value.trim();
            if (!code) return;

            fetch("/scan", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({code: code})
            })
            .then(res => res.json())
            .then(data => {
                document.getElementById("result").innerText =
                    "记录成功 时间: " + data.time;
                input.value = "";
                input.focus();
            });
        }
        </script>
    </body>
    </html>
    """)

# 扫码接口
@app.route("/scan", methods=["POST"])
def scan():
    data = request.get_json()
    code = data.get("code")

    scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect("checkin.db")
    c = conn.cursor()
    c.execute("INSERT INTO records (code, scan_time) VALUES (?, ?)", (code, scan_time))
    conn.commit()
    conn.close()

    return jsonify({"status": "ok", "time": scan_time})

# 查看记录页面
@app.route("/records")
def records():
    conn = sqlite3.connect("checkin.db")
    c = conn.cursor()
    c.execute("SELECT code, scan_time FROM records ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()

    html = "<h2>打卡记录</h2><table border=1><tr><th>二维码内容</th><th>时间</th></tr>"
    for row in rows:
        html += f"<tr><td>{row[0]}</td><td>{row[1]}</td></tr>"
    html += "</table><br><a href='/'>返回首页</a>"
    return html

# 下载CSV
@app.route("/download")
def download():
    conn = sqlite3.connect("checkin.db")
    c = conn.cursor()
    c.execute("SELECT code, scan_time FROM records ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()

    def generate():
        yield "code,scan_time\n"
        for row in rows:
            yield f"{row[0]},{row[1]}\n"

    return Response(
        generate(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=checkin_records.csv"}
    )

import os

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

