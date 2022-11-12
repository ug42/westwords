# Westwords 20-questions style game with social deduction and roles.
#
# NOTE: can only use this configuration with a single worker because socketIO
# and gunicorn are unable to handle sticky sessions. Boo. Scaling jobs will need
# to account for a reverse proxy and keeping each server with a single worker
# thread.

# Overall game flow, make sure each step has plumbing here.

# self.game.game_status == GameState.SETUP
# self.game.nominate_for_mayor('player1')
# self.game.set_word_choice_count(word_list_length)
# self.game.start_night_phase_word_choice()
# words = self.game.get_words()
# self.game.set_word(word)

# self.game.game_state == GameState.NIGHT_PHASE_DOPPELGANGER
# role = self.game.set_doppelganger_role_target('player1', 'player2')

# self.game.game_state == GameState.NIGHT_PHASE_TARGETTING
# self.game.set_player_target('player1', 'player7') # esper only targetting
# self.game.set_player_target('player2', 'player3') # and doppelesper

# self.game.game_state == GameState.NIGHT_PHASE_REVEAL
# self.game.get_players_needing_to_ack()
# self.game.get_player_revealed_information('player1')
# self.game.acknowledge_revealed_info('player2')
# self.game.get_player_revealed_information('player3', acknowledge=True)
# self.game.get_player_revealed_information('player4', acknowledge=True)
# self.game.get_player_revealed_information('player5', acknowledge=True)
# self.game.get_player_revealed_information('player6', acknowledge=True)
# self.game.get_player_revealed_information('player7')
# self.game.acknowledge_revealed_info('player7')


# self.game.game_state == GameState.DAY_PHASE_QUESTIONS
# success, id = self.game.add_question('mason2', 'Am I the first question?')
# success, end_of_game = self.game.answer_question(id, AnswerToken.YES)
# success, id = self.game.add_question('werewolf2', 'Is it a squirrel?')
# success, end_of_game = self.game.answer_question(id, AnswerToken.NO)
# success, id = self.game.add_question('villager', 'Chimpanzee?')
# success, end_of_game = self.game.answer_question(id, AnswerToken.CORRECT)
# success, players_needing_to_vote = self.game.start_vote(word_guessed=True)

# self.game.game_status == GameState.VOTING
# self.game.get_required_voters()
# self.game.vote('werewolf2', 'mason2')
# self.game.get_results() 
    # (Affiliation.VILLAGE,
    # ['villager', 'mason2'],
    # {'werewolf1': 'villager', 'werewolf2': 'mason2'}))
# self.game.game_status == GameState.FINISHED
# self.game.reset()
# self.game.game_status == GameState.SETUP


import re
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


SOCKET_MAP = {}
# TODO: move this off to a backing store.
PLAYERS = {}
# TODO: move this off to a backing store.
GAMES = {
    # TODO: replace with real player objects associated with session
    'defaultgame': westwords.Game(timer=300, player_sids=[]),
}


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
    if 'sid' not in session:
        session['sid'] = str(uuid4())
    if 'username' not in session:
        session['username'] = f'Not_a_wolf_{randint(1000,9999)}'
        return redirect('/login')
    if session['sid'] not in PLAYERS:
        PLAYERS[session['sid']] = westwords.Player(session['username'])

    return render_template(
        'index.html.j2',
        games=list(GAMES),
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


@app.route('/join/<game_id>', strict_slashes=False)
@app.route('/join?game_name=<game_id>', strict_slashes=False)
def join_game(game_id):
    app.logger.debug(f"{session['sid']} attempting to join {game_id}")
    if game_id in GAMES:
        GAMES[game_id].add_player(session['sid'])
        PLAYERS[session['sid']].join_room(game_id)
    return redirect(f'/game/{game_id}')

@app.route('/game/<game_id>')
def game_index(game_id):
    if 'sid' not in session:
        session['sid'] = str(uuid4())
    if 'username' not in session:
        session['username'] = f'Not_a_wolf_{randint(1000,9999)}'
        return redirect('/login')
    if session['sid'] not in PLAYERS:
        PLAYERS[session['sid']] = westwords.Player(session['username'])
    

    if game_id in GAMES:
        game_state = parse_game_state(game_id, session['sid'])
    else:
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


@app.route('/get_words/<game_id>')
def get_words(game_id):
    if game_id in GAMES and GAMES[game_id].is_started():
        if GAMES[game_id].word:
            return None
        words = GAMES[game_id].get_words()
        if words and GAMES[game_id].mayor == session['sid']:
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
    if request.method == 'POST':
        game_id = request.form['game_id']
        if game_id not in GAMES:
            GAMES[game_id] = westwords.Game(player_sids=[session['sid']])
        return redirect(f'/join/{game_id}')
    else:
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
    if 'sid' not in session:
        session['sid'] = str(uuid4())
    if session['sid'] not in PLAYERS:
        PLAYERS[session['sid']] = westwords.Player(session['username'])
    SOCKET_MAP[session['sid']] = request.sid
    for room in PLAYERS[session['sid']].get_rooms():
        join_room(room)
        emit('user_info', f"{PLAYERS[session['sid']]} joined.", to=room)

    app.logger.debug(f'Current socket map: {SOCKET_MAP}')


@socketio.on('disconnect')
def disconnect():
    try:
        SOCKET_MAP[session['sid']] = None
        if PLAYERS[session['sid']].rooms:
            for room in PLAYERS[session['sid']].rooms:
                leave_room(room)
                emit('user_info', f"{PLAYERS[session['sid']]} left.", to=room)
    except KeyError as e:
        app.logger.debug(
            f"Unable to remove socket mapping for {session['sid']}: {e}")
    app.logger.debug(f'Current socket map: {SOCKET_MAP}')


@socketio.on('question')
def add_question(game_id, question_text):
    if game_id in GAMES:
        success, id = GAMES[game_id].add_question(
            session['sid'], question_text)
        if success:
            emit('new_question', {
                'game_id': game_id, 'question_id': id}, broadcast=True)
            app.logger.info(f'Successfully added question to {game_id}')
            return True

    app.logger.error(f'Unable to add question for game {game_id}')
    return False


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
        app.logger.error('No player found for session: ' + session['sid'])
        return False

    if game_id not in GAMES:
        app.logger.error('Unable to find game: ' + game_id)
        return False

    if GAMES[game_id].mayor != session['sid']:
        app.logger.error('User is not mayor!')
        return False

    if question_id >= len(GAMES[game_id].questions):
        app.logger.error(f'Question {question_id} is an out of array index.')
        return False

    try:
        answer_token = westwords.AnswerToken[answer.upper()]
    except KeyError as e:
        app.logger.error(f'Unknown answer: {e}')
        return False

    # Question ID is basically just the index offset starting at 0
    success, end_of_game = GAMES[game_id].answer_question(question_id,
                                                          answer_token)
    if not success:
        socketio.emit('mayor_error', f'Out of {answer_token.value} tokens')
        return False

    if end_of_game:
        socketio.emit('mayor_error',
                      f'Last token played, Undo or Move to vote.')
    socketio.emit('force_refresh', game_id, broadcast=True)
    return True


@ socketio.on('get_game_state')
def game_status(game_id: str):
    if game_id in GAMES:
        emit(
            'game_state',
            parse_game_state(game_id, session['sid'])
        )


@socketio.on('undo')
def undo(game_id: str):
    app.logger.debug(f'Attempting to undo something for {game_id}')
    if game_id in GAMES and GAMES[game_id].mayor == session['sid']:
        GAMES[game_id].undo_answer()
        socketio.emit('force_refresh', game_id, broadcast=True)


@socketio.on('nominate_for_mayor')
def nominate_for_mayor(game_id: str):
    if game_id in GAMES and GAMES[game_id].is_player_in_game(session['sid']):
        GAMES[game_id].nominate_for_mayor(session['sid'])


# TODO: implement all the scenarios around this
# Timer functions
@socketio.on('game_start_req')
def start_game(game_id: str):
    if game_id in GAMES:
        if not GAMES[game_id].start_night_phase_word_choice():
            emit('admin_error', f'Unable to start game. No game: {game_id}.')
            return
        emit('game_start_rsp', game_id, broadcast=True)
        socketio.emit('force_refresh', game_id, broadcast=True)


@socketio.on('game_reset_req')
def reset_game(game_id):
    # Implement game reset feature
    app.logger.info(f'Resetting game: {game_id}')
    if game_id in GAMES:
        GAMES[game_id].reset()
        emit('game_reset_rsp', game_id, broadcast=True)
        socketio.emit('force_refresh', game_id, broadcast=True)


@socketio.on('vote')
def vote(game_id, target_id):
    app.logger.debug(
        f"{PLAYERS[session['sid']].name} vote for {PLAYERS[target_id].name}")
    if game_id in GAMES:
        success = GAMES[game_id].vote(session['sid'], target_id)
        if not success:
            app.logger.error(f'Unable to cast vote.')


@socketio.on('get_role')
def get_role(game_id):
    # TODO: Move this to use a callback
    if game_id in GAMES and GAMES[game_id].is_player_in_game(session['sid']):
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
        emit('mayor_error', f'Unable to set word for game {game_id}.')
        return

    if session['sid'] != GAMES[game_id].mayor:
        emit('mayor_error',
             f'Word set attempt failed. User is not mayor.')
        return

    GAMES[game_id].set_word()


if __name__ == '__main__':
    socketio.run(app)
