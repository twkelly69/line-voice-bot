from flask import Flask, request, abort
import os
import sys

app = Flask(__name__)

@app.route("/", methods=['GET'])
def health_check():
    return "LINE Bot is running!", 200

@app.route("/callback", methods=['POST'])
def callback():
    return 'OK', 200

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    print(f"Python version: {sys.version}")
    print(f"Starting server on port {port}")
    print(f"Environment variables: PORT={os.environ.get('PORT', 'not set')}")
    try:
        app.run(debug=False, host='0.0.0.0', port=port)
    except Exception as e:
        print(f"Error starting server: {e}")
        raise