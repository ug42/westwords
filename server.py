import enum
import random
from uuid import uuid4
from datetime import datetime
from random import randint
from string import ascii_uppercase

from flask import (Flask, jsonify, make_response, redirect, render_template,
                   request, session)
from flask_socketio import SocketIO, emit

from flask_session import Session

# TODO: remove or factor out so only set if flag is set.
DEBUG = True
app = Flask(__name__)
app.config['SECRET_KEY'] = '8fdd9716f2f66f1390440cbef84a4bd825375e12a4d31562a4ec8bda4cddc3a4'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['USE_PERMANENT_SESSION'] = True

if DEBUG:
    app.config['DEBUG'] = True
# TODO: add session key login and get rid of a ton of logic grown here
Session(app)
socketio = SocketIO(app)


class GameState(enum.Enum):
    SETUP = 1
    STARTED = 2
    PAUSED = 3
    VOTING = 4
    FINISHED = 5


class Game(object):
    """Simple game object for recording status of game.
        12 role tiles
        36 Yes/No tokens
        10 Maybe tokens
        1 So Close token
        1 Correct token
    """

    def __init__(self, timer=300, players=[]):
        # TODO: Add concept of a game admin and management of users in that space
        self.game_state = GameState.SETUP
        self.timer = timer
        self.time_start = None
        # TODO: Plumb in user objects to this
        self.admin = 'all'
        # TODO: Make this to a dict so it can contain roles
        self.players = players
        self.tokens = {
            'yes_no': 36,
            'maybe': 10,
            'so_close': 1,
            'so_far': 1,
            # Purpose is generally unknown even by laramie.
            'laramie': 1,
            'correct': 1,
        }

    def start(self):
        self.game_state = GameState.STARTED

    def pause(self):
        self.game_state = GameState.PAUSED

    def set_timer(self, time_in_seconds):
        self.timer = time_in_seconds

    def finish(self):
        self.game_state = GameState.FINISHED

    def reset(self):
        if self.game_state is not GameState.STARTED:
            self.game_state = GameState.SETUP

    def update_state(self, json):
        # TODO: Update to parse a json
        pass

    def get_state(self):
        game_status = {
            'game_state': self.game_state.name,
            'players': self.players,
            'time': self.timer,
        }
        if app.config['DEBUG'] == True:
            print(game_status)
        return game_status

    def set_state(self, json):
        # TODO: parse and set the game state based on this.
        # Could be used for future updates to write out to data store
        pass

    def get_player_names(self):
        return [player.name for player in self.players]

    def get_player_sessions(self):
        # TODO: determine if this is used.
        return [player.session_id for player in self.players]


class Player(object):
    """Simple class for player"""

    def __init__(self, name, session_id, game_id):
        self.name = name
        # Figure out how to emit to a given user here for transmission directly,
        # if needed.
        self.session_id = session_id
        self.game_id = game_id


Games = {
    # TODO: replace with real player objects associated with session
    'defaultgame': Game(timer=120, players=[
        Player('Me', 12, 'defaultgame'),
        Player('Test', 13, 'defaultgame'),
    ])
}


def verify_player_session():
    # TODO: make this actually work and plumb in to check the session for
    # reconnect purposes.
    if session['player'].session_id != session.id:
        print(f'Updating session id for {session["username"]}:  {session.id}')
        session['player'].session_id = session.id

# TODO: figure out if the socket channel and the HTTP channel share the same
# session info

# URL routing
@app.route('/')
def game():
    if 'username' not in session:
        session['username'] = f'Not_a_wolf_{randint(1000,9999)}'
    if 'player' not in session:
        session['player'] = Games['defaultgame'].players
    return render_template('game.html')


@app.route('/username', methods=['GET', 'POST'])
def username():
    # if DEBUG and request.method == 'POST':
    #     print(f'Request: {request.data}')
    #     print('Requesting /username URL')
    # print('Username requested: {}'.format(request.form.get('username')))
    if request.method == 'POST' and request.form.get('username'):
        print(f'Username registered:{session["username"]}')
        session['username'] = request.form.get('username')
        if session['']
    return redirect('/')


@app.route('/join/<game>')
def join_game(game):
    if game in Games:
        Games[game].players.append(Player(session['username'], session['sid']))
    return redirect('/')


@app.route('/create', methods=['POST', 'GET'])
def create_game():
    if request.method == 'GET':
        game_id = ''.join(random.choice(ascii_uppercase) for i in range(4))
        Games[game_id] = Game(players=Player(session['username'], session.id))
    return redirect('/')


@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/logout')
def logout():
    response = make_response(render_template('logout.html'))
    response.set_cookie(app.session_cookie_name, expires=0)
    session.clear()
    return response


# Socket control functions
@socketio.on('connect')
def connect(auth):
    session['sid'] = str(uuid.uuid4())
    session['username']
    emit('my response', {'data': 'Connected'})
    print('Client connected')
    if auth:
        print('Auth details: ' + str(auth))


@socketio.on('question')
def question(json):
    print('got a question: ' + str(json))
    emit('mayor question', json, broadcast=True)


@socketio.on('answer_question')
def answer_question(question_id):
    if session['game'] Games and Games[session['game']]
        if 


@socketio.on('update_game')
def update_game(game_updates, game_id):
    if (game_id in Games) and Games[game_id].admin == 'all':
        Games[game_id].update_state_json(game_updates)


@socketio.on('get_game_state')
def game_status(game_id):
    socketio.emit('game_state', Games[game_id].get_state())


@socketio.on('game_start')
def start_game(game_id):
    Games[game_id].start()


@socketio.on('game_pause')
def start_game(game_id):
    Games[game_id].pause()


@socketio.on('game_reset')
def start_game(game_id):
    Games[game_id].reset()


if __name__ == '__main__':
    socketio.run(app)
