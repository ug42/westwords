from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

config = {
    'DEBUG': True,
}


@app.route('/')
def game():
    return render_template('game.html')


@socketio.on('connect')
def connect(auth):
    emit('my response', {'data': 'Connected'})
    print('Client connected')
    if auth:
        print('Auth details: ' + str(auth))


@socketio.on('disconnect')
def disconnect():
    print('Client disconnected')


@socketio.on('question')
def question(json):
    print('received question: ' + str(json))
    emit('mayor question', json, broadcast=True)


if __name__ == '__main__':
    socketio.run(app)