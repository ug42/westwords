# Westwords 20-questions style game with social deduction and roles.
#
# NOTE: can only use this configuration with a single worker because socketIO
# and gunicorn are unable to handle sticky sessions. Boo. Scaling jobs will need
# to account for a reverse proxy and keeping each server with a single worker
# thread.

# requirements.txt may still need Flask-Session==0.4.0 : but testing without it.

import re
import sys
from random import choice, randint
from string import ascii_uppercase
from uuid import uuid4

from flask import (Flask, flash, make_response, redirect, render_template,
                   request, session)
from flask_socketio import SocketIO, emit, join_room, leave_room

import westwords
from westwords.enums import AnswerToken

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['USE_PERMANENT_SESSION'] = True

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
# TODO: Make it so the updated game_status and the dynamic status is the same
# URL routing


# TODO: Replace this with a proper log to file statement.
def log(text):
    print(text)


def parse_game_state(game_id, session_sid):
    """Parses the initial game state dict + tuple into a dict with player info.

    Args:
        game_id: String game id on which to get game state.
        session_id: String session ID of requesting user.

    Returns:
        game_state: a dict of str 'game_state', int 'timer', str 'game_id',
            str 'mayor' name, bool 'am_mayor', bool 'am_admin', a list of
            'questions' dicts of int 'id', str 'question', str 'player', str
            'answer', a list of str 'players' names, and a str 'role' for the
            player.
    """
    if game_id:
        (game_state, questions,
         player_sids) = GAMES[game_id].get_state(game_id)
    else:
        (game_state, questions, player_sids) = westwords.Game(
            timer=0, player_sids=[]).get_state(None)

    game_state['questions'] = []

    for id, question in enumerate(questions):
        get_question_info(question, id)
        game_state['questions'].append({
            'id': id,
            'question': question.question_text,
            'player': PLAYERS[question.player_sid].name,
            'answer': question.get_answer(),
        })
    game_state['questions'].reverse()

    game_state['players'] = []
    for sid in player_sids:
        if sid in PLAYERS:
            game_state['players']

    game_state['am_mayor'] = game_state['mayor'] == session_sid
    game_state['am_admin'] = game_state['admin'] == session_sid

    try:
        # Replace the mayor SID with name
        game_state['mayor'] = PLAYERS[game_state['mayor']].name
    except KeyError:
        # No mayor is yet selected. and this is now a load-bearing string. :|
        game_state['mayor'] = 'No Mayor yet elected'

    if session_sid in player_sids:
        game_state['role'] = str(player_sids[session_sid]).capitalize()
    else:
        game_state['role'] = None

    return game_state


def get_question_info(question, id):
    return {
        'id': id,
        'question': question.question_text,
        'player': PLAYERS[question.player_sid].name,
        'answer': question.get_answer(),
    }


@app.route('/')
def index():
    log(app.config)
    if 'sid' not in session:
        session['sid'] = str(uuid4())
    if 'username' not in session:
        session['username'] = f'Not_a_wolf_{randint(1000,9999)}'
        return redirect('/login')
    if session['sid'] not in PLAYERS:
        PLAYERS[session['sid']] = westwords.Player(session['username'])

    #######################################
    # FIXME: Remove this when game join is more functional
    #######################################
    GAMES['defaultgame'].add_player(session['sid'])
    PLAYERS[session['sid']].game = 'defaultgame'
    ###########
    # Remove to here.
    ############

    if PLAYERS[session['sid']] and PLAYERS[session['sid']].game in GAMES:
        game_id = PLAYERS[session['sid']].game
        game_state = parse_game_state(game_id, session['sid'])
    else:
        # Return the values from an empty game
        game_id = None
        game_state = parse_game_state(None, session['sid'])

    return render_template(
        'game.html.j2',
        question_list=game_state['questions'],
        players=game_state['players'],
        game_name=game_state['game_id'],
        game_state=game_state['game_state'],
        time=game_state['time'],
        mayor=game_state['mayor'],
        tokens=game_state['tokens'],
        am_mayor=game_state['am_mayor'],
        am_admin=game_state['am_admin'],
        role=game_state['role'],
        game_id=game_id,
        # Remove this when done poking at things. :P
        DEBUG=app.config['DEBUG'],
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
        GAMES[game].add_player(session['sid'])
        PLAYERS[session['sid']].game = game
    return redirect('/')


@app.route('/get_words/<game_id>')
def get_words(game_id):
    if game_id in GAMES and GAMES[game_id].is_started():
        if GAMES[game_id].chosen_word:
            return None
        words = GAMES[game_id].get_words()
        if words:
            return render_template(
                'word_choice.html.j2',
                words=words,
                game_id=game_id,
            )
        else:
            return 'Unable to provide word choices.'


# TODO: Move this to use Flask rooms, if useful above current setup
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
    try:
        if session['sid'] not in PLAYERS:
            PLAYERS[session['sid']] = westwords.Player(session['username'])
    except KeyError as e:
        log(f'Unable to register Player, due to lookup failure. {e}')
    game_status()
    try:
        game_status(PLAYERS[session['sid']].game)
    except KeyError as e:
        log(f'No key value found: {e}')


@socketio.on('question')
def add_question(game_id, question_text):
    if game_id in GAMES:
        success, id = GAMES[game_id].add_question(
            session['sid'], question_text)
        if success:
            emit('new_question', {
                'game_id': game_id, 'question_id': id}, broadcast=True)

    print(f'Unable to add question for game {game_id}')


@socketio.on('get_question_req')
def send_question(game_id, question_id):
    if game_id in GAMES and int(question_id) < len(GAMES[game_id].questions):
        question = GAMES[game_id].questions[question_id]
        response = {
            'game_id': game_id,
            'question': render_template(
                'question_layout.html.j2',
                question_object=get_question_info(question, question_id))
        }
        socketio.emit('get_question_rsp', response)


@ socketio.on('answer_question')
def answer_question(game_id, question_id, answer):
    """Answer the question for a given game, if the user is the mayor.

    Args:
        question_id: An integer ID for the question in the game object
        answer: A string for the answer type

        (Yes/No/Maybe/So Close/So Far/Correct)

    Returns:
        True is answer is successfully set; False otherwise.
    """
    if session['sid'] not in PLAYERS:
        log('No player found for session: ' + session['sid'])
        return False

    game_id=PLAYERS[session['sid']].game
    if game_id not in GAMES:
        log('Unable to find game: ' + game_id)
        return False

    if GAMES[game_id].mayor != session['sid']:
        log('User is not mayor!')
        return False

    if question_id >= len(GAMES[game_id].questions):
        log(f'Question {question_id} is an out of array index.')
        return False

    try:
        answer_token=westwords.AnswerToken[answer.upper()]
        log(f'Answer at beginning: {answer_token.value}/{answer_token.name}')
    except KeyError as e:
        log(f'Unknown answer: {e}')
        return False

    # Question ID is basically just the index offset starting at 0
    results=GAMES[game_id].remove_token(answer_token)
    if not results['success']:
        socketio.emit('mayor_error', f'Out of {answer_token.value} tokens')
        return False

    GAMES[game_id].answer_question(question_id, answer_token)
    asking_player=GAMES[game_id].questions[question_id].player_sid
    PLAYERS[asking_player].add_token(answer_token)

    if results['end_of_game']:
        socketio.emit('mayor_error',
                      f'Last token played, Undo or Move to vote.')
    socketio.emit('force_refresh', game_id, broadcast = True)
    return True


@ socketio.on('get_game_state')
def game_status(game_id = None):
    if not game_id:
        game_id=PLAYERS[session['sid']].game
    if game_id in GAMES:
        emit(
            'game_state',
            parse_game_state(game_id, session['sid'])
        )


@socketio.on('undo')
def undo(game_id):
    print(f'Attempting to undo something for {game_id}')
    if game_id in GAMES:
        if (game_id == PLAYERS[session['sid']].game and
                GAMES[game_id].mayor == session['sid']):
            GAMES[game_id].undo_answer()
        socketio.emit('force_refresh', game_id, broadcast=True)


@socketio.on('nominate_mayor')
def add_mayor_nominee(game_id):
    if game_id in GAMES and PLAYERS[session['sid']].game == game_id:
        GAMES[game_id].nominate_for_mayor(session['sid'])


# TODO: implement all the scenarios around this
# Timer functions
@socketio.on('game_start_req')
def start_game(game_id):
    if game_id in GAMES:
        (success, message) = GAMES[game_id].start()
        if not success:
            emit('admin_error', f'Unable to start game: {message}')
            return
        log(f'Starting timer for game {game_id}')
        emit('game_start_rsp', game_id, broadcast=True)
        socketio.emit('force_refresh', game_id, broadcast=True)


@socketio.on('game_reset_req')
def reset_game(game_id):
    # Implement game reset feature
    log(f'Resetting game: {game_id}')
    if game_id in GAMES:
        GAMES[game_id].reset()
        emit('game_reset_rsp', game_id, broadcast=True)
        socketio.emit('force_refresh', game_id, broadcast=True)


@socketio.on('vote')
def vote(game_id, target_id):
    log(f'{PLAYERS[session["sid"]].name} voted for {PLAYERS[target_id].name}')
    if game_id in GAMES:
        success = GAMES[game_id].vote(session['sid'], target_id)
        if not success:
            log(f'Unable to cast vote.')


@socketio.on('get_role')
def get_role(game_id):
    if PLAYERS[session['sid']].game == game_id and game_id in GAMES:
        emit('player_role', GAMES[game_id].get_player_role(session['sid']))


@socketio.on('word_choice')
def set_word(game_id, word):
    """Set the chosen word for the provided game ID.

    Args:
        game_id: String game ID referencing the game.
        word: String word referencing the word to set as the chosen word for the
            game.
    """
    if game_id not in GAMES:
        socket.emit('mayor_error', f'Unable to set word for game {game_id}.')
        return

    if session['sid'] != GAMES[game_id].mayor:
        socket.emit('mayor_error',
                    f'Word set attempt failed. User is not mayor.')
        return

    GAMES[game_id].set_word()


if __name__ == '__main__':
    socketio.run(app)
