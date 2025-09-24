from flask import Flask, request, jsonify

app = Flask(__name__)

last_webhook_data = {} # Initialize with an empty dictionary

@app.route('/')
def home():
    if last_webhook_data:
        return jsonify(last_webhook_data)
    return 'No webhook data received yet.'

@app.route('/webhook', methods=['POST'])
def webhook():
    global last_webhook_data
    last_webhook_data = request.json
    print(last_webhook_data)
    return jsonify(last_webhook_data)

if __name__ == '__main__':
    app.run(debug=True)


