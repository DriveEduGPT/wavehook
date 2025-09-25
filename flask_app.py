import os
from flask import Flask, request, render_template
from flask_socketio import SocketIO, emit


app = Flask(__name__)
app.config['SECRET_KEY'] = 'YOUR_ACTUAL_STRONG_SECRET_KEY_HERE' # Directly set SECRET_KEY here for PythonAnywhere async deployment
socketio = SocketIO(app, async_mode='gevent', cors_allowed_origins=['https://wavehook.pythonanywhere.com', 'http://127.0.0.1:5000'])

message_history = [] # Initialize with an empty list to store all messages

@app.route('/')
def home():
    return render_template('index.html', messages=message_history)

@app.route('/webhook', methods=['POST'])
def webhook():
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if client_ip is None:
        client_ip = 'Unknown' # Fallback if no IP is found

    print(f"Detected client IP: {client_ip}") # Temporarily log detected IP
    # print(f"Request Headers: {request.headers}") # Remove temporary log for headers

    # Re-enable IP filtering
    allowed_ips = [
        '52.89.214.238',
        '34.212.75.30',
        '54.218.53.128',
        '52.32.178.7',
        '223.19.58.131' # Postman IP
    ]
    if client_ip not in allowed_ips:
        print(f"Unauthorized access from IP: {client_ip}")
        return 'Forbidden', 403

    global message_history
    received_data = ""

    if request.is_json:
        received_data = request.json
    elif request.data:
        received_data = request.data.decode('utf-8') # Handle plain text or other data
    elif request.form:
        received_data = request.form.to_dict() # Handle form data
    else:
        received_data = "No discernible data received."

    # Store both IP, data and headers in history
    message_entry = {
        'ip': client_ip,
        'data': received_data,
        'headers': dict(request.headers) # Convert headers to a dict for display
    }
    message_history.insert(0, message_entry) # Add new message to the beginning of the list
    print(f"Received webhook: {received_data}")
    emit('new_message', message_entry, broadcast=True, namespace='/') # Emit the whole entry

    return 'OK', 200

@socketio.on('connect')
def test_connect():
    print('Client connected')

@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_DEBUG', 'False') == 'True'
    # In development, SocketIO should handle debug mode for Flask itself
    # The host and port will be handled by socketio.run()
    socketio.run(app, debug=debug_mode, host='0.0.0.0', port=80)


# git pull origin master