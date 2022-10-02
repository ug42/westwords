import enum
import random
from uuid import uuid4
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


class AnswerToken(enum.Enum):
    # Provides canonical tokens and mapping to buckets
    YES = "yes_no"
    NO = "yes_no"
    MAYBE = "maybe"
    SO_CLOSE = "so_close"
    SO_FAR = "so_far"
    CORRECT = "correct"
    LARAMIE = "laramie"


class Question(object):
    """Simple question construct for named variables"""

    def __init__(self, player_sid, question_text):
        self.player_sid = player_sid
        self.question_text = question_text
        self.answer = ''

    def __repr__(self):
        return f'Question({self.player_sid}, {self.question_text})'

    def __str__(self):
        return f'{PLAYERS[self.player_name].name}: {self.question_text} ({self.answer})'


class Game(object):
    """Simple game object for recording status of game.
        12 role tiles
        36 Yes/No tokens
        10 Maybe tokens
        1 So Close token
        1 Correct token
    """

    def __init__(self, timer=300, player_sids=[], admin=None):
        # TODO: Add concept of a game admin and management of users in that space
        self.game_state = GameState.SETUP
        self.timer = timer
        self.time = timer
        # TODO: Plumb in user objects to this
        self.admin = admin
        # TODO: Make this to a dict so it can contain roles
        self.player_sids = player_sids
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
        self.questions = []

    def __repr__(self):
        return f'Game({self.timer}, {self.player_sids})'

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
        if app.config['DEBUG']:
            print(f'DEBUG ENABLED! Current game state: {game_status}')
        return game_status

    def get_questions(self):
        return [f'{id}: {str(question)}' for id, question in enumerate(self.questions)]

    def get_player_names(self):
        return [PLAYERS[sid].name for sid in self.player_sids]

    def get_player_sessions(self):
        # TODO: determine if this is used.
        return self.player_sids

# TODO: Make all references use the SID to reference player info


class Player(object):
    """Simple class for player"""

    def __init__(self, name, game=None):
        self.name = name
        self.game = game
        self.tokens = {
            AnswerToken.CORRECT: 0,
            AnswerToken.YES: 0,
            AnswerToken.NO: 0,
            AnswerToken.MAYBE: 0,
            AnswerToken.SO_CLOSE: 0,
            AnswerToken.SO_FAR: 0,
            AnswerToken.CORRECT: 0,
            AnswerToken.LARAMIE: 0,
        }

    # def __repr__(self):
    #     return f'Player({self.name}, {self.game})'

    def __str__(self):
        return f'Player name: {self.name}, in game id: {self.game}'

    def add_token(self, token):
        # Add a token of a given enum value to this player's total
        self.tokens[token] += 1

PLAYERS = {
    # Keyed by session ID
    '87ebd04a-c039-4cf3-919f-1a8b2eb23163': Player('Me'),
    '207ba035-2ea6-4ffb-9f6b-129a2f18850b': Player('Test'),
}


GAMES = {
    # TODO: replace with real player objects associated with session
    'defaultgame': Game(timer=120, player_sids=PLAYERS.keys())
}

GAMES['defaultgame'].questions

def verify_player_session():
    # If we manage to get someone modifying the cookie without being connected
    # for some reason, let's sync up.
    if session['sid'] in PLAYERS:
        if session['name'] != PLAYERS[session['sid']].name:
            print('Player name out-of-date: {} / {}'.format(
                session['username'], session['sid']))
        PLAYERS['sid'].name = session['name']

# URL routing
@app.route('/')
def game():
    if 'username' not in session:
        session['username'] = f'Not_a_wolf_{randint(1000,9999)}'
    if 'sid' not in session:
        session['sid'] = str(uuid4())
    return render_template('game.html')


@app.route('/username', methods=['POST'])
def username():
    if request.method == 'POST' and request.form.get('username'):
        print(f'Username registered:{session["username"]}')
        session['username'] = request.form.get('username')
        if session['sid'] in PLAYERS:
            PLAYERS[session['sid']].username = session['username']
    return redirect('/')


@app.route('/join/<game>')
def join_game(game):
    if game in GAMES:
        if session['sid'] not in GAMES[game].player_sids:
          GAMES[game].player_sids.append(PLAYERS[session['sid']])
        PLAYERS[session['sid']].game = game
    return redirect('/')


@app.route('/create', methods=['POST', 'GET'])
def create_game():
    if request.method == 'GET':
        game_id = ''.join(random.choice(ascii_uppercase) for i in range(4))
        GAMES[game_id] = Game(player_sids=[session['id']])
    return redirect('/')


@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/logout')
def logout():
    response = make_response(render_template('logout.html'))
    response.set_cookie(app.config['SESSION_COOKIE_NAME'], expires=0)
    session.clear()
    return response


# Socket control functions
@socketio.on('connect')
def connect(auth):
    if app.config['DEBUG']:
        print(session)
    if session['sid'] not in PLAYERS:
        PLAYERS[session['sid']] = Player(session['username'])
    # emit('my response', {'data': 'Connected'})
    print('Client connected')
    if auth:
        print('Auth details: ' + str(auth))


@socketio.on('question')
def question(question_text):
    game = PLAYERS[session['sid']].game
    question = Question(session['sid'], question_text)
    print(f'got a question: {question_text}')
    print(str(game))
    print('Session: ' + session['sid'])
    if game in GAMES:
        GAMES[game].questions.append(question)


@socketio.on('answer_question')
def answer_question(question_id, answer):
    """Answer the question for a given game, if the user is the mayor.

    Args:
        question_id: An integer ID for the question in the game object
        answer: A string for the answer type

        (Yes/No/Maybe/So Close/So Far/Correct)
    """
    if session['sid'] not in PLAYERS:
        print('No player found for session: ' + session['sid'])
    
    game = PLAYERS[session['sid']].game
    if PLAYERS[session['sid']].game not in GAMES:
        print('Unable to find game: ' + game)
        return
    
    if GAMES[game].mayor != session['sid']:
        print('User is not mayor!')
        return
    
    if question_id not in GAMES[game].questions:
        print(f'Question {question_id} not in game.' + GAMES[game].get_state())

    if answer.upper() not in [token.name for token in AnswerToken]:
        print(f'Unknown answer type: {answer}')
    answer_token = AnswerToken[answer.upper()]
    if answer_token.value is 'yes_no' and GAMES[game].tokens['yes_no'] == 1:
        GAMES[game].start_vote()
    if GAMES[game].tokens[answer_token.value] <= 0:
        print(f'Unable to apply {answer_token}')
        emit('mayor_error', f'No "{answer}" tokens remaining.')

    # Question ID is basically just the index offset starting at 0
    GAMES[game].questions[question_id].answer = answer_token

    # TODO: add the accounting back to the player
    asking_player = GAMES[game].questions[question_id].player_sid
    PLAYERS[asking_player].add_token(answer_token)



@socketio.on('get_game_state')
def game_status(game_id):
    response = app.response_class(response=jsonify(GAMES[game_id].get_state()),
                                  status=200,
                                  mimetype='application/json')
    socketio.emit('game_state', GAMES[game_id].get_state())

# TODO: implement all the scenarios around this
# Timer functions


@socketio.on('game_start')
def start_game(game_id):
    print('Starting timer')
    GAMES[game_id].start()


@socketio.on('game_pause')
def start_game(game_id):
    print('Pausing timer')
    GAMES[game_id].pause()


@socketio.on('game_reset')
def start_game(game_id):
    print('Resetting game')
    GAMES[game_id].reset()


if __name__ == '__main__':
    socketio.run(app)
