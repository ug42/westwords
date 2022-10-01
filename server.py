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
DEBUG = False
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


class AnswerToken(enum.Enum):
    YES = "yes"
    NO = "no"
    MAYBE = "maybe"
    SO_CLOSE = "so_close"
    SO_FAR = "so_far"
    CORRECT = "correct"
    LARAMIE = "laramie"


class Question(object):
    """Simple question construct for named variables"""

    def __init__(self, player_sid, question_text):
        self.player_name = Players[player_sid].name
        self.question_text = question_text
        self.answer = ''

    def __repr__(self):
        return 'Question()'

    def __str__(self):
        return f'{self.player_name}: {self.question_text} ({self.answer})'


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
        self.time = timer
        # TODO: Plumb in user objects to this
        self.admin = players
        # TODO: Make this to a dict so it can contain roles
        self.players = players
        self.tokens = {
            'yes_no': 36,
            'maybe': 10,
            'so_close': 1,
            'so_far': 1,
            # Purpose is generally unknown even by lar.
            'laramie': 1,
            'correct': 1,
        }
        self.mayor = None
        self.questions = {}

    def __repr__(self):
        return f'Game({self.timer}, {self.players})'

    def __str__(self):
        return ('Game with state: {game_state}\n'
                'Timer: {timer}\n'
                'Time left: {time}\n'
                'Questions:\n{questions}\n'
                'Players: {players}').format(
                    game_state=self.game_state,
                    timer=self.timer,
                    time=self.time,
                    questions=self.get_questions(),
                    players=self.get_player_names())

    def start(self):
        self.game_state = GameState.STARTED

    def pause(self):
        self.game_state = GameState.PAUSED

    def start_vote(self):
        self.game_state = GameState.VOTING

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
            'players': self.get_player_names(),
            'time': self.timer,
            'questions': self.get_questions(),
        }
        if app.config['DEBUG'] == True:
            print(game_status)
        return game_status

    def get_questions(self):
        return [f'{id}: {str(question)}' for id, question in enumerate(self.questions)]

    def get_player_names(self):
        return [Players[sid].name for sid in self.players]

    def get_player_sessions(self):
        # TODO: determine if this is used.
        return [player.session_id for player in self.players]

# TODO: Make all references use the SID to reference player info


class Player(object):
    """Simple class for player"""

    def __init__(self, name, game=None):
        self.name = name
        self.game = game

    # def __repr__(self):
    #     return f'Player({self.name}, {self.game})'

    def __str__(self):
        return f'Player name: {self.name}, in game id: {self.game}'


Players = {
    # Keyed by session ID
    '87ebd04a-c039-4cf3-919f-1a8b2eb23163': Player('Me'),
    '207ba035-2ea6-4ffb-9f6b-129a2f18850b': Player('Test'),
}


Games = {
    # TODO: replace with real player objects associated with session
    'defaultgame': Game(timer=120, players=Players.keys())
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
    if 'sid' not in session:
        session['sid'] = str(uuid4())
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
        if session['sid'] in Players:
            Players[session['sid']].username = session['username']
    return redirect('/')


@app.route('/join/<game>')
def join_game(game):
    if game in Games:
        Games[game].players.append(Players[session['sid']])
        Players[session['sid']].game = game
    return redirect('/')


@app.route('/create', methods=['POST', 'GET'])
def create_game():
    if request.method == 'GET':
        game_id = ''.join(random.choice(ascii_uppercase) for i in range(4))
        Games[game_id] = Game(players=[session['id']])
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
    print(session)
    if session['sid'] not in Players:
        Players[session['sid']] = Player(session['username'])
    # emit('my response', {'data': 'Connected'})
    print('Client connected')
    if auth:
        print('Auth details: ' + str(auth))


@socketio.on('question')
def question(question_text):
    print(f'got a question: {question_text}')
    print(str(Players[session['sid']]))
    print('Session: ' + session['sid'])
    if Players[session['sid']].game in Games:
        Games[game].questions.append(Question(session['sid'], question_text))


@socketio.on('answer_question')
def answer_question(question_id, answer):
    """Answer the question for a given game, if the user is the mayor.

    Args:
        question_id: An integer ID for the question in the game object
        answer: A string for the answer type

        (Yes/No/Maybe/So Close/So Far/Correct)
    """
    if session['game'] not in Games:
        print('Unable to find game: ' + session['game'])
        return
    if Games[session['game']].mayor != session['sid']:
        print('User is not mayor!')
        return
    if question_id not in Games[session['game']].questions:
        print(f'Question {question_id} not in Games construct')
    if answer.upper() not in [token.name for token in AnswerToken]:
        print(f'Unknown answer type: {answer}')
    if answer in ['yes', 'no']:
        if Games[session['game']].tokens['yes_no'] == 1:
            Games[session['game']].start_vote()
    else:
        if Games[session['game']].tokens[answer] <= 0:
            print('Unable to apply')
            emit('mayor_error', 'Out of tokens')

    Games[session['game']].questions[question_id].answer = answer


# # TODO: determine if this is needed.
# @socketio.on('update_game')
# def update_game(game_updates, game_id):
#     if (game_id in Games) and Games[game_id].admin == 'all':
#         Games[game_id].update_state_json(game_updates)


@socketio.on('get_game_state')
def game_status(game_id):
    response = app.response_class(response=jsonify(Games[game_id].get_state()),
                                  status=200,
                                  mimetype='application/json')
    socketio.emit('game_state', Games[game_id].get_state())

# TODO: implement all the scenarios around this
# Timer functions


@socketio.on('game_start')
def start_game(game_id):
    print('Starting timer')
    Games[game_id].start()


@socketio.on('game_pause')
def start_game(game_id):
    print('Pausing timer')
    Games[game_id].pause()


@socketio.on('game_reset')
def start_game(game_id):
    print('Resetting game')
    Games[game_id].reset()


if __name__ == '__main__':
    socketio.run(app)
