from flask import Flask, request, render_template
from flask_socketio import SocketIO, emit

APP = Flask(__name__)
SOCKET = SocketIO(APP)


@APP.route('/')
def index():
    return render_template('client.html')


@SOCKET.on('connect')
def connect():
    print("[CLIENT CONNECTED]:", request.sid)


@SOCKET.on('disconnect')
def disconn():
    print("[CLIENT DISCONNECTED]:", request.sid)


@SOCKET.on('notify')
def notify(user):
    emit('notify', user, broadcast=True, skip_sid=request.sid)


@SOCKET.on('data')
def emitback(data):
    emit('returndata', data, broadcast=True)

if __name__ == "__main__":
    SOCKET.run(APP)
