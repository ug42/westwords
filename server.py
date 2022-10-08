# Westwords 20-questions style game with social deduction and roles.
#
# NOTE: can only use this configuration with a single worker because socketIO
# and gunicorn are unable to handle sticky sessions. Boo. Scaling jobs will need
# to account for a reverse proxy and keeping each server with a single worker
# thread. Stupid lack of scaling is stupid.

from enum import Enum
from datetime import datetime
import random
from uuid import uuid4
from random import randint
from string import ascii_uppercase
from game.game import *

from flask import (Flask, jsonify, make_response, redirect, render_template,
                   request, session)
from flask_socketio import SocketIO, emit

# Session used ONLY for 'username' and server-generated player id 'sid'
from flask_session import Session

# TODO: remove or factor out so only set if flag is set.
DEBUG = True
app = Flask(__name__)
app.config['SECRET_KEY'] = '8fdd9716f2f66f1390440cbef84a4bd825375e12a4d31562a4ec8bda4cddc3a4'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['USE_PERMANENT_SESSION'] = True

if DEBUG:
    app.config['DEBUG'] = True
Session(app)
socketio = SocketIO(app)

# TOP LEVEL TODOs
# TODO: add roles plumbing
# TODO: add spectate
# TODO: game lock for players state
# TODO: add create game
# TODO: plumb game state reset functionality
# TODO: Factor out data store bits so PLAYERS and GAMES are not accessible to
#       Question/Player/Game objects


# TODO: move this off to a backing store.
PLAYERS = {}
# TODO: move this off to a backing store.
GAMES = {
    # Load-bearing empty state response for error handling.
    # TODO: Do something else here, feels hacky.
    None: Game(timer=0, player_sids=[]),
    # TODO: replace with real player objects associated with session
    'defaultgame': Game(timer=300, player_sids=[]),
}
MAX_RETRIES = 5


def verify_player_session(retry=0):
    # If we manage to get someone modifying the cookie without being connected
    # for some reason, let's sync up.
    if retry > MAX_RETRIES:
        return
    try:
        if session['sid'] in PLAYERS:
            if session['username'] != PLAYERS[session['sid']].name:
                print('Player name out-of-date: {} / {}'.format(
                    session['username'], session['sid']))
            PLAYERS['sid'].name = session['username']
    except KeyError:
        generate_session_info()
        verify_player_session(retry+1)


def generate_session_info():
    if 'sid' not in session:
        session['sid'] = str(uuid4())
    if 'username' not in session:
        session['username'] = f'Not_a_wolf_{randint(1000,9999)}'

# TODO: Make it so the updated game_status and the dynamic status is the same
# URL routing


def parse_game_state(g):
    game_state = g[0]
    questions = g[1]
    player_sids = g[2]

    game_state['questions'] = []
    for id, question in enumerate(questions):
        formatted_question = question.html_format().format(
            id=id, player_name=PLAYERS[question.player_sid].name)
        game_state['questions'].append(formatted_question)

    game_state['players'] = []
    for sid in player_sids:
        if sid in PLAYERS:
            game_state['players'].append(PLAYERS[sid].name)
    # game_state['players'] = [PLAYERS[sid].name for sid in player_sids]

    return game_state


@app.route('/')
def game():
    generate_session_info()
    verify_player_session()
    try:
        if PLAYERS[session['sid']].game in GAMES:
            game = PLAYERS[session['sid']].game
            game_state = parse_game_state(GAMES[game].get_state(game))
    except KeyError:
        game_state = parse_game_state(GAMES[None].get_state(None))

    return render_template(
        'game.html',
        questions=game_state['questions'],
        players=game_state['players'],
        game_name=game_state['game_id'],
        game_state=game_state['game_state'],
        time=game_state['time'],
    )


@app.route('/username', methods=['POST'])
def username():
    if request.method == 'POST' and request.form.get('username'):
        print(f'Username registered:{session["username"]}')
        session['username'] = request.form.get('username')
        if session['sid'] in PLAYERS:
            PLAYERS[session['sid']].name = session['username']
    return redirect('/')


@app.route('/join/<game>')
def join_game(game):
    if game in GAMES:
        if session['sid'] not in GAMES[game].player_sids:
            GAMES[game].player_sids.append(session['sid'])
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
def connect():
    if app.config['DEBUG']:
        print(session)
    if session['sid'] not in PLAYERS:
        PLAYERS[session['sid']] = Player(session['username'])
    # Send initial game_status
    # game_status()
    # emit('my response', {'data': 'Connected'})
    print('Client connected')


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
        print(
            f'Question {question_id} not in game.' +
            parse_game_state(GAMES[game].get_state())
        )

    if answer.upper() not in [token.name for token in AnswerToken]:
        print(f'Unknown answer type: {answer}')
    answer_token = AnswerToken[answer.upper()]
    if answer_token.value == 'yes_no' and GAMES[game].tokens['yes_no'] == 1:
        GAMES[game].start_vote()
    if GAMES[game].tokens[answer_token.value] <= 0:
        print(f'Unable to apply {answer_token}')
        emit('mayor_error', f'No "{answer}" tokens remaining.')

    # Question ID is basically just the index offset starting at 0
    GAMES[game].questions[question_id].answer = answer_token
    asking_player = GAMES[game].questions[question_id].player_sid
    PLAYERS[asking_player].add_token(answer_token)
    GAMES[game].remove_token(answer_token)


@socketio.on('get_game_state')
def game_status():
    game_id = PLAYERS[session['sid']].game
    # response = app.response_class(response=jsonify(parse_game_state(GAMES[game_id].get_state())),
    #                               status=200,
    #                               mimetype='application/json')
    if game_id in GAMES:
        socketio.emit(
            'game_state', parse_game_state(GAMES[game_id].get_state(game_id)))

# TODO: implement all the scenarios around this
# Timer functions


@socketio.on('game_start_req')
def start_game(game_id):
    print('Starting timer')
    if game_id in GAMES:
        GAMES[game_id].start()
        emit('game_start_rsp', game_id, broadcast=True)


@socketio.on('game_pause_req')
def start_game(game_id):
    print('Pausing timer')
    if game_id in GAMES:
        GAMES[game_id].pause()
        emit('game_pause_rsp', game_id, broadcast=True)


@socketio.on('game_reset_req')
def start_game(game_id):
    # Implement game reset feature
    print('Resetting game')
    if game_id in GAMES:
        GAMES[game_id].reset()
        emit('game_reset_rsp', game_id, broadcast=True)


if __name__ == '__main__':
    socketio.run(app)
