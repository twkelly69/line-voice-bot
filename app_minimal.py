from flask import Flask, request, abort
import os

app = Flask(__name__)

@app.route("/", methods=['GET'])
def health_check():
    return "LINE Bot is running!", 200

@app.route("/callback", methods=['POST'])
def callback():
    return 'OK', 200

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting server on port {port}")
    app.run(debug=False, host='0.0.0.0', port=port)