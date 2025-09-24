from flask import Flask, request

app = Flask(__name__)

@app.route('/')
def home():
    return 'Hello from Wavehook Flask App!'

@app.route('/webhook', methods=['POST'])
def webhook():
    # Webhook handling logic will go here
    print(request.json)
    return 'OK', 200

if __name__ == '__main__':
    app.run(debug=True)


