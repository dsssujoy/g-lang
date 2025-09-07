from flask import Flask, request, render_template
from io import StringIO
import sys
from interpreter2 import run

app = Flask(__name__)

@app.route('/')
def home():
    return render_template("index.html")  # Serve HTML from templates folder

@app.route('/run', methods=['POST'])
def run_code():
    code = request.form.get("code","")
    old_stdout = sys.stdout
    sys.stdout = mystdout = StringIO()
    try:
        run(code)
        output = mystdout.getvalue()
    except Exception as e:
        output = str(e)
    finally:
        sys.stdout = old_stdout
    return output

if __name__ == "__main__":
    app.run(debug=True)
