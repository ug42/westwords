# Westwords 20-questions style game with social deduction and roles.
#
# NOTE: can only use this configuration with a single worker because socketIO
# and gunicorn are unable to handle sticky sessions. Boo. Scaling jobs will need
# to account for a reverse proxy and keeping each server with a single worker
# thread.

# requirements.txt may still need Flask-Session==0.4.0 : but testing without it.

import re
from uuid import uuid4
from random import randint, choice
from string import ascii_uppercase
import westwords

from flask import (Flask, flash, make_response, redirect, render_template,
                   request, session)
from flask_socketio import SocketIO, emit

from westwords.enums import AnswerToken

# TODO: remove or factor out so only set if flag is set.
DEBUG = True
app = Flask(__name__)
app.config['SECRET_KEY'] = '8fdd9716f2f66f1390440cbef84a4bd825375e12a4d31562a4ec8bda4cddc3a4'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['USE_PERMANENT_SESSION'] = True

if DEBUG:
    app.config['DEBUG'] = True
socketio = SocketIO(app)

# TOP LEVEL TODOs
# TODO: add roles plumbing
# TODO: add spectate
# TODO: game lock for players state
# TODO: add create game
# TODO: plumb game state reset functionality


# TODO: move this off to a backing store.
PLAYERS = {}
# TODO: move this off to a backing store.
GAMES = {
    # TODO: replace with real player objects associated with session
    'defaultgame': westwords.Game(timer=300, player_sids=[]),
}
MAX_RETRIES = 5


def verify_player_session(retry=0):
    # If we manage to get someone modifying the cookie without being connected
    # for some reason, let's sync up.
    if retry > MAX_RETRIES:
        return

    username = session.get('username', f'Not_a_wolf_{randint(1000,9999)}')
    sid = session.get('sid', str(uuid4()))
    try:
        if username != PLAYERS[session['sid']].name:
            print('Player name out-of-date: {} / {}'.format(
                username, session['sid']))

        PLAYERS[sid].name = username
    except KeyError:
        generate_session_info()
        verify_player_session(retry+1)


def generate_session_info():
    if 'sid' not in session:
        session['sid'] = str(uuid4())
        session.modified = True
        print(f'Registering SID: {session["sid"]}')
    if 'username' not in session:
        session['username'] = f'Not_a_wolf_{randint(1000,9999)}'
        print(f'Registering username: {session["username"]}')
        return redirect('/login')
    if session['sid'] not in PLAYERS:
        print('Attempting to add sid to PLAYERS')
        PLAYERS[session['sid']] = westwords.Player(session['username'])
        if app.config['DEBUG']:
            print('Adding player to defaultgame game')
            PLAYERS[session['sid']].game = 'defaultgame'
            GAMES['defaultgame'].add_player(session['sid'])


# TODO: Make it so the updated game_status and the dynamic status is the same
# URL routing


def parse_game_state(unparsed_game_state, session_sid):
    """Parses the initial game state dict + tuple into a dict with player info.
    
    Args:
        unparsed_game_state: A tuple containing [0] dict of str game_state, int
            timer, str game_id, and str mayor player session ID, [1] a list of
            westword.question.Question objects, and [2] a dict of str player
            sessions IDs to westword.role.Role type objects.
        
    Returns:
        game_state: a dict of str 'game_state', int 'timer', str 'game_id', 
            str 'mayor' name, bool 'am_mayor', a list of str 'questions', a list
            of str 'players' names, and a str 'role' for the player.
    """
    game_state = unparsed_game_state[0]
    questions = unparsed_game_state[1]
    player_sids = unparsed_game_state[2]

    game_state['questions'] = []
    for id, question in enumerate(questions):
        formatted_question = question.html_format().format(
            id=id, player_name=PLAYERS[question.player_sid].name)
        game_state['questions'].append(formatted_question)
    # Let's make it show most recent at the top. :)
    game_state['questions'].reverse()

    game_state['players'] = []
    for sid in player_sids:
        if sid in PLAYERS:
            game_state['players'].append(PLAYERS[sid].name)

    game_state['am_mayor'] = game_state['mayor'] == session_sid

    try:
        # Replace the mayor SID with name
        game_state['mayor'] = PLAYERS[game_state['mayor']].name
    except KeyError:
        # No mayor is yet selected. and this is now a load-bearing string. :|
        game_state['mayor'] = 'No Mayor yet elected'

    try:
        game_state['role'] = str(player_sids[session_sid])
    except KeyError as e:
        print(f'Unable to find player role from SID in game: {e}')

    print(f'Tokens: {game_state["tokens"]}')

    return game_state


@app.route('/')
def index():
    if 'sid' not in session:
        session['sid'] = str(uuid4())
        print(f'Registering SID: {session["sid"]}')
    if 'username' not in session:
        session['username'] = f'Not_a_wolf_{randint(1000,9999)}'
        print(f'Registering username: {session["username"]}')
        return redirect('/login')
    if session['sid'] not in PLAYERS:
        print('Attempting to add sid to PLAYERS')
        PLAYERS[session['sid']] = westwords.Player(session['username'])

    if PLAYERS[session['sid']] and PLAYERS[session['sid']].game in GAMES:
        print(f'Game found')
        game_id = PLAYERS[session['sid']].game
        game_state = parse_game_state(
            GAMES[game_id].get_state(game_id), session['sid'])
    else:
        print('No game found associated with player.')
        # Return the values from an empty game
        game_state = parse_game_state(
            westwords.Game(timer=0, player_sids=[]).get_state(None),
            session['sid'])

    return render_template(
        'game.html',
        questions=game_state['questions'],
        players=game_state['players'],
        game_name=game_state['game_id'],
        game_state=game_state['game_state'],
        time=game_state['time'],
        mayor=game_state['mayor'],
    )


@app.route('/username', methods=['POST'])
def username():
    if request.method == 'POST' and request.form.get('username'):
        if re.search(r'mayor', request.form.get('username').casefold()):
            flash('Cute, smartass.')
            return redirect('/')                    
        session['username'] = request.form.get('username')
        if session['sid'] in PLAYERS:
            PLAYERS[session['sid']].name = session['username']
    return redirect('/')


@app.route('/join/<game>')
def join_game(game):
    if game in GAMES:
        if session['sid'] not in GAMES[game].player_sids:
            GAMES[game].add_player(session['sid'])
        PLAYERS[session['sid']].game = game
    return redirect('/')


# TODO: Move this to use rooms, if useful above current setup
@app.route('/create', methods=['POST', 'GET'])
def create_game():
    if request.method == 'GET':
        game_id = ''.join(choice(ascii_uppercase) for i in range(4))
        GAMES[game_id] = westwords.Game(player_sids=[session['id']])
    return redirect('/')


@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/logout')
def logout():
    response = make_response(render_template('logout.html'))
    response.set_cookie(app.config['SESSION_COOKIE_NAME'], expires=0)
    flash('Session destroyed. You are now logged out; redirecting to /')
    session.clear()
    return response


# Socket control functions
@socketio.on('connect')
def connect(auth):
    # if auth:
    # verify_player_session()
    try:
        if session['sid'] not in PLAYERS:
            PLAYERS[session['sid']] = westwords.Player(session['username'])
    except KeyError as e:
        print(f'Unable to register Player, due to lookup failure. {e}')
    game_status()
    try:
        game_status(PLAYERS[session['sid']].game)
    except KeyError as e:
        print(f'No key value found: {e}')
    print(f'Session info from connect: {session}')
    print('Client connected')


@socketio.on('question')
def question(question_text):
    game_id = PLAYERS[session['sid']].game
    question = westwords.Question(session['sid'], question_text)
    print(f'Question: {str(question)}')
    print(f'got a question: {question_text}')
    if game_id in GAMES:
        # Race condition is only an issue if you lose the race. :|
        question_id = len(GAMES[game_id].questions)
        print(f'next question id: {question_id}')
        print(f'question_html: question_id')
        question_html = question.html_format().format(
            id=question_id, player_name=PLAYERS[question.player_sid].name)

        GAMES[game_id].questions.append(question)
        emit('add_question',
             {'q': question_html, 'game_id': game_id}, broadcast=True)


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
        return

    game_id = PLAYERS[session['sid']].game
    if game_id not in GAMES:
        print('Unable to find game: ' + game_id)
        return

    if GAMES[game_id].mayor != session['sid']:
        print('User is not mayor!')
        return

    if question_id >= len(GAMES[game_id].questions):
        print(f'Question {question_id} is an out of array index.')

    try:
        answer_token = westwords.AnswerToken[answer.upper()]
        print(f'Answer at beginning: {answer_token.value}/{answer_token.name}')
    except KeyError as e:
        print(f'Unknown answer: {e}')

    # Question ID is basically just the index offset starting at 0
    results = GAMES[game_id].remove_token(answer_token)
    if not results['success']:
        socketio.emit('mayor_error', f'Out of {answer_token.value} tokens')
        return

    GAMES[game_id].answer_question(question_id, answer_token)
    asking_player = GAMES[game_id].questions[question_id].player_sid
    PLAYERS[asking_player].add_token(answer_token)

    if results['end_of_game']:
        socketio.emit('mayor_error',
                        f'Last token played, Undo or Move to vote.')

    socketio.emit('force_refresh', game_id, broadcast=True)


@socketio.on('get_game_state')
def game_status(game_id=None):
    if not game_id:
        game_id = PLAYERS[session['sid']].game
    if game_id in GAMES:
        emit(
            'game_state',
            parse_game_state(GAMES[game_id].get_state(game_id), session['sid'])
        )


@socketio.on('undo')
def undo(game_id):
    if game_id in GAMES:
        if (game_id == PLAYERS[session['sid']].game and
                GAMES[game_id].mayor == session['sid']):
            GAMES[game_id].undo_answer()
        socketio.emit('force_refresh', game_id, broadcast=True)


@socketio.on('make_me_mayor')
def make_me_mayor(game_id):
    if game_id in GAMES and game_id == PLAYERS[session['sid']].game:
        GAMES[game_id].mayor = session['sid']
    socketio.emit('force_refresh', game_id, broadcast=True)


# TODO: implement all the scenarios around this
# Timer functions
@socketio.on('game_start_req')
def start_game(game_id):
    print('Starting timer')
    if game_id in GAMES:
        GAMES[game_id].start()
        emit('game_start_rsp', game_id, broadcast=True)
        socketio.emit('force_refresh', game_id, broadcast=True)


@socketio.on('game_reset_req')
def start_game(game_id):
    # Implement game reset feature
    print('Resetting game')
    if game_id in GAMES:
        GAMES[game_id].reset()
        emit('game_reset_rsp', game_id, broadcast=True)
        socketio.emit('force_refresh', game_id, broadcast=True)


@socketio.on('get_role')
def get_role(game_id):
    if PLAYERS[session['sid']].game == game_id and game_id in GAMES:
        emit('player_role', GAMES[game_id].get_player_role(session['sid']))


if __name__ == '__main__':
    socketio.run(app)
