# Westwords 20-questions style game with social deduction and roles.
#
# NOTE: can only use this configuration with a single worker because socketIO
# and gunicorn are unable to handle sticky sessions. Boo. Scaling jobs will need
# to account for a reverse proxy and keeping each server with a single worker
# thread.

from uuid import uuid4
from random import randint, choice
from string import ascii_uppercase
import westwords

from flask import (Flask, make_response, redirect, render_template,
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
        print(f'Update username and player record, retries: {retry}')
        print(session)
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
    

# TODO: Make it so the updated game_status and the dynamic status is the same
# URL routing


def parse_game_state(g):
    game_state = g[0]
    questions = g[1]
    player_sids = g[2]

    game_state['questions'] = []
    print(f'Parsing game state. Session info: {session}')
    hidden_answer_buttons = ''
    if game_state['mayor'] != session['sid']:
        hidden_answer_buttons = 'hidden'

    for id, question in enumerate(questions):
        formatted_question = question.html_format().format(
            id=id, player_name=PLAYERS[question.player_sid].name,
            hidden=hidden_answer_buttons)
        game_state['questions'].append(formatted_question)
    # Let's make it show most recent at the top. :)
    game_state['questions'].reverse()

    game_state['players'] = []
    for sid in player_sids:
        if sid in PLAYERS:
            game_state['players'].append(PLAYERS[sid].name)

    return game_state

# TODO: Add a redirect to all routes or maybe a handler to ensure someone can
# set their username. Preferably with a route-back to the requested url.
@app.route('/')
def index():
    # TODO: Add a username prompt redirect for first login attempts.
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
        game_state = parse_game_state(GAMES[game_id].get_state(game_id))
    else:
        print('No game found associated with player.')
        # Return the values from an empty game
        game_state = parse_game_state(
            westwords.Game(timer=0, player_sids=[]).get_state(None))

    # FIXME: game_state renders on first load, than fails with local variable
    # 'game_state' referenced before assignment on subsequent loads
    
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
    # session.clear()
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
    # FIXME: Sending initial game state via game_status() breaks socket for some
    #        reason.
    # Send initial game_status
    # game_status()
    try:
        print(f'Session info from connect: {session}')
        game_id = PLAYERS[session['sid']].game
        if game_id in GAMES:
            socketio.emit(
                'game_state', parse_game_state(GAMES[game_id].get_state(game_id)))
    except KeyError as e:
        print(f'No key value found: {e}')
    print(f'Session info from connect: {session}')    
    print('Client connected')


@socketio.on('question')
def question(question_text):
    game_id = PLAYERS[session['sid']].game
    question = westwords.Question(session['sid'], question_text)
    print(f'got a question: {question_text}')
    if game_id in GAMES:
        hidden_answer_buttons = ''
        if GAMES[game_id].mayor != session['sid']:
            hidden_answer_buttons = 'hidden'
        # Race condition is only an issue if you lose the race. :|
        question_id = len(GAMES[game_id].questions)
        question_html = question.html_format().format(
            id=question_id,player_name=PLAYERS[question.player_sid].name,
            hidden=hidden_answer_buttons)

        GAMES[game_id].questions.append(question)
        emit('add_question',
             {'q': question_html,'game_id': game_id}, broadcast=True)


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

    try:
        answer_token = westwords.AnswerToken[answer.upper()]
    except KeyError as e:        
        print(f'Unknown answer: {e}')
    
    if answer_token.value == 'yes_no' and GAMES[game].tokens['yes_no'] == 1:
        GAMES[game].start_vote()
    if GAMES[game].tokens[answer_token.value] <= 0:
        print(f'Unable to apply {answer_token}')
        emit('mayor_error', f'No "{answer}" tokens remaining.')

    # Question ID is basically just the index offset starting at 0
    GAMES[game].questions[question_id].answer = answer_token
    GAMES[game].last_answered = question_id
    asking_player = GAMES[game].questions[question_id].player_sid
    PLAYERS[asking_player].add_token(answer_token)

    try:
        GAMES[game].remove_token(answer_token)
    except (westwords.game.OutOfTokenError,
            westwords.game.OutOfYesNoTokenError) as e:
        # Handle the end of game condition.
        emit('mayor_error', e)
    


@socketio.on('get_game_state')
def game_status():
    game_id = PLAYERS[session['sid']].game
    if game_id in GAMES:
        socketio.emit(
            'game_state', parse_game_state(GAMES[game_id].get_state(game_id)))


@socketio.on('undo')
def undo(game_id):
    if game_id in GAMES:
        if (game_id == PLAYERS[session['sid']].game and
            GAMES[game_id].mayor == session['sid']):
            GAMES[game_id].undo_answer()


@socketio.on('make_me_mayor')
def make_me_mayor(game_id):
    if game_id in GAMES and game_id == PLAYERS[session['sid']].game:
        GAMES[game_id].mayor = session['sid']


# TODO: implement all the scenarios around this
# Timer functions
@socketio.on('game_start_req')
def start_game(game_id):
    print('Starting timer')
    if game_id in GAMES:
        GAMES[game_id].start()
        emit('game_start_rsp', game_id, broadcast=True)


@socketio.on('game_reset_req')
def start_game(game_id):
    # Implement game reset feature
    print('Resetting game')
    if game_id in GAMES:
        GAMES[game_id].reset()
        emit('game_reset_rsp', game_id, broadcast=True)


if __name__ == '__main__':
    socketio.run(app)
