from flask import Flask, request
from io import StringIO
import sys
from interpreter2 import run

app = Flask(__name__)

@app.route('/')
def home():
    return {"status": "G-Lang API running 🚀"}  # simple JSON response

@app.route('/run', methods=['POST'])
def run_code():
    code = request.form.get("code", "")
    old_stdout = sys.stdout
    sys.stdout = mystdout = StringIO()
    try:
        run(code)
        output = mystdout.getvalue()
    except Exception as e:
        output = str(e)
    finally:
        sys.stdout = old_stdout
    return {"output": output}  # return as JSON

if __name__ == "__main__":
    app.run(debug=True)
