import os
from flask import Flask, request, render_template
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_fallback_secret_key_here')

# 設定資料庫 URI，必須從環境變數獲取
database_url = os.environ.get('DATABASE_URL')
if not database_url:
    raise RuntimeError("DATABASE_URL environment variable is not set. Please set it for database connection.")
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

socketio = SocketIO(app, async_mode='gevent', cors_allowed_origins=['https://wavehook.pythonanywhere.com', 'http://127.0.0.1:5000'])

# Define a database model to store webhook messages
class WebhookLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45))
    data = db.Column(db.JSON) # Use JSON type for flexible data storage
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<WebhookLog {self.id} from {self.ip_address}>'

@app.route('/')
def home():
    # Fetch latest 100 messages from the database
    latest_messages = WebhookLog.query.order_by(WebhookLog.timestamp.desc()).limit(100).all()
    # Convert to a format suitable for the template (e.g., list of dicts)
    messages_for_template = [
        {'ip': msg.ip_address, 'data': msg.data, 'timestamp': msg.timestamp.isoformat()}
        for msg in latest_messages
    ]
    return render_template('index.html', messages=messages_for_template)

@app.route('/webhook', methods=['POST'])
def webhook():
    # client_ip = request.headers.get('X-Real-IP')
    # if client_ip is None:
    #     client_ip = request.headers.get('X-Forwarded-For')
    #     if client_ip is not None:
    #         client_ip = client_ip.split(',')[0].strip()
    # if client_ip is None:
    #     client_ip = request.remote_addr
    # if client_ip is None:
    #     client_ip = 'Unknown' # Fallback if no IP is found

    # # Re-enable IP filtering
    # allowed_ips = [
    #     '52.89.214.238',
    #     '34.212.75.30',
    #     '54.218.53.128',
    #     '52.32.178.7',
    #     '223.19.58.131', # Assuming this is the Postman IP
    #     '127.0.0.1' # Allow localhost for local development
    # ]

    # # print(f"--- IP Debug ---\nDetected client IP: '{client_ip}' (type: {type(client_ip)})\nAllowed IPs: {allowed_ips}\n--- End IP Debug ---") # Remove debug log

    # if client_ip not in allowed_ips:
    #     print(f"Unauthorized access from IP: {client_ip}")
    #     return 'Forbidden', 403

    # Temporarily get client_ip for logging/database without filtering
    client_ip = request.headers.get('X-Real-IP') \
                or request.headers.get('X-Forwarded-For', '').split(',')[0].strip() \
                or request.remote_addr \
                or 'Unknown'

    global message_history # This line is actually removed now with DB integration
    received_data = ""
    if request.is_json:
        received_data = request.json
    elif request.data:
        received_data = request.data.decode('utf-8')
    elif request.form:
        received_data = request.form.to_dict()
    else:
        received_data = "No discernible data received."

    # Store webhook in the database
    new_log = WebhookLog(ip_address=client_ip, data=received_data)
    db.session.add(new_log)
    db.session.commit()

    # Emit the newly saved log entry to all connected clients
    emit('new_message', {
        'ip': client_ip,
        'data': received_data,
        'timestamp': datetime.utcnow().isoformat() # Use current UTC time for emit
    }, broadcast=True, namespace='/')

    return 'OK', 200

@socketio.on('connect')
def test_connect():
    print('Client connected')

@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected')

# Create database tables within the application context
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    import gevent
    gevent.monkey_patch()

    # socketio 已在全局作用域初始化
    # socketio = SocketIO(app, async_mode='gevent', cors_allowed_origins=['https://wavehook.pythonanywhere.com', 'http://127.0.0.1:5000'])
    debug_mode = os.environ.get('FLASK_DEBUG', 'False') == 'True'
    socketio.run(app, debug=debug_mode, host='0.0.0.0', port=80)


# git pull origin master