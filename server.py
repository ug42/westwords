# Westwords 20-questions style game with social deduction and roles.
#
# NOTE: can only use this configuration with a single worker because socketIO
# and gunicorn are unable to handle sticky sessions. Boo. Scaling jobs will need
# to account for a reverse proxy and keeping each server with a single worker
# thread.

# Overall game flow, make sure each step has plumbing here.

# self.game.get_player_revealed_information('player1')
# acknowledge_revealed_info
# self.game.acknowledge_revealed_info('player2')
# self.game.get_player_revealed_information('player3', acknowledge=True)
# self.game.get_player_revealed_information('player4', acknowledge=True)
# self.game.get_player_revealed_information('player5', acknowledge=True)
# self.game.get_player_revealed_information('player6', acknowledge=True)
# self.game.get_player_revealed_information('player7')
# self.game.acknowledge_revealed_info('player7')

# <automatic> after last player acks
# self.game.game_state == GameState.DAY_PHASE_QUESTIONS
# question
# success, id = self.game.add_question('mason2', 'Am I the first question?')
# answer_question
# success, end_of_game = self.game.answer_question(id, AnswerToken.YES)
# question
# success, id = self.game.add_question('werewolf2', 'Is it a squirrel?')
# answer_question
# success, end_of_game = self.game.answer_question(id, AnswerToken.NO)
# question
# success, id = self.game.add_question('villager', 'Chimpanzee?')
# answer_question
# success, end_of_game = self.game.answer_question(id, AnswerToken.CORRECT)
# start_vote
# success, players_needing_to_vote = self.game.start_vote(word_guessed=True)
# self.game.game_status == GameState.VOTING
# get_required_voters
# self.game.get_required_voters()
# vote (game_id, target)
# self.game.vote('werewolf2', 'mason2')
# get_results
# self.game.get_results()
# (Affiliation.VILLAGE,
# ['villager', 'mason2'],
# {'werewolf1': 'villager', 'werewolf2': 'mason2'}))
# <automatic>
# self.game.game_status == GameState.FINISHED
# game_reset_req
# self.game.reset()
# self.game.game_status == GameState.SETUP


from datetime import datetime
import re
from random import choice, randint
from string import ascii_uppercase
from uuid import uuid4

from flask import (Flask, flash, make_response, redirect, render_template,
                   request, session)
from flask_socketio import SocketIO, emit, join_room, leave_room, rooms

import westwords
from westwords.enums import AnswerToken

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['USE_PERMANENT_SESSION'] = True
socketio = SocketIO(app)

# TOP LEVEL TODOs
# TODO: add spectate
# TODO: game lock for players state
# TODO: plumb game state reset functionality


SOCKET_MAP = {}
# TODO: move this off to a backing store.
PLAYERS = {}
# TODO: move this off to a backing store.
GAMES = {}


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

    required_voters = GAMES[game_id].get_required_voters()
    players_needing_to_ack = GAMES[game_id].get_players_needing_to_ack()
    players_needing_to_target = GAMES[game_id].get_players_needing_to_target()

    players = {}
    for player_sid in player_sids:
        player = PLAYERS[player_sid]
        players[player.name] = {}
        for token, count in player.tokens.items():
            players[player.name][token.value] = count

    game_state.update({
        'server_timestamp_millis': int(datetime.now().timestamp() * 1000),
        'players_names_needing_ack': [
            PLAYERS[p].name for p in players_needing_to_ack],
        'player_names_needing_vote': [PLAYERS[p].name for p in required_voters],
        'am_mayor': game_state['mayor'] == session_sid,
        'am_admin': game_state['admin'] == session_sid,
        'am_waiting_for_vote': session['sid'] in required_voters,
        'am_waiting_for_target': session['sid'] in players_needing_to_target,
        'am_waiting_for_ack': session['sid'] in players_needing_to_ack,
        'players': players,
    })

    try:
        # Replace the mayor SID with name
        game_state['mayor'] = PLAYERS[game_state['mayor']].name
    except KeyError:
        # No mayor is yet selected. and this is now a load-bearing string. :|
        game_state['mayor'] = 'No Mayor yet elected'

    if session_sid in player_sids:
        game_state['role'] = str(player_sids[session_sid]).capitalize()
    else:
        game_state['role'] = 'Spectator'

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
    else:
        return redirect(f'/create/{game_id}')
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
    if game_id not in PLAYERS[session['sid']].rooms:
        return redirect(f'/join/{game_id}')

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
    if game_id in GAMES:
        if GAMES[game_id].word:
            return None
        words = GAMES[game_id].get_words()
        if words and GAMES[game_id].mayor == session['sid']:
            return render_template(
                'word_choice.html.j2',
                words=words,
                game_id=game_id,
            )
    return 'Unable to provide word choices.'


# TODO: Move this to use Flask rooms, if useful above current setup
@app.route('/create', methods=['POST', 'GET'], strict_slashes=False)
@app.route('/create/<game_id>', methods=['GET'], strict_slashes=False)
def create_game(game_id: str = None):
    if request.method == 'POST' and request.form['game_id']:
        app.logger.debug(f'POST method found: {request.form}')
        game_id = request.form['game_id']
    if not game_id:
        app.logger.debug(f'No game_id specified')
        return redirect('/')
    app.logger.debug(f'Attempting to check if {game_id} exists')
    if game_id not in GAMES:
        app.logger.debug(f'{game_id} not found; creating')
        GAMES[game_id] = westwords.Game(player_sids=[session['sid']])
    return redirect(f'/join/{game_id}')


@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/logout')
def logout():
    response = make_response(render_template('logout.html'))
    session.clear()
    response.set_cookie(app.config['SESSION_COOKIE_NAME'], expires=0)
    flash('Session destroyed. You are now logged out; redirecting to /')
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
        if room not in rooms():
            app.logger.debug(f'{room} not in list of rooms: {rooms()}')
            join_room(room)
            emit('user_info',
                 f"{PLAYERS[session['sid']].name} joined.", room=room)
        app.logger.debug(f'Rooms for client: {rooms()}')

    app.logger.debug(f'Current socket map: {SOCKET_MAP}')


@socketio.on('disconnect')
def disconnect():
    try:
        SOCKET_MAP[session['sid']] = None
        if PLAYERS[session['sid']].rooms:
            for room in PLAYERS[session['sid']].rooms:
                leave_room(room)
                emit('user_info',
                     f"{PLAYERS[session['sid']].name} left.", room=room)
    except KeyError as e:
        app.logger.debug(
            f"Unable to remove socket mapping for {session['sid']}: {e}")
    app.logger.debug(f'Current socket map: {SOCKET_MAP}')


@socketio.on('question')
def add_question(game_id, question_text):
    if game_id in GAMES:
        app.logger.debug(f'Found game: {game_id}')
        app.logger.debug(f'Listed user: {session["sid"]}')
        success, id = GAMES[game_id].add_question(
            session['sid'], question_text)
        app.logger.debug(f'Success of adding question: {success}')
        app.logger.debug(f'Id of added question: {id}')
        if success:
            emit('new_question', {'game_id': game_id,
                 'question_id': id}, room=game_id)
            app.logger.info(f'Successfully added question to {game_id}')
            return True

    app.logger.error(f'Unable to add question for game {game_id}')
    return False


@socketio.on('get_question')
def get_question(game_id: str, question_id: int):
    # game_id = data['game_id']
    # question_id = data['question_id']
    if game_id in GAMES and int(question_id) < len(GAMES[game_id].questions):
        question = GAMES[game_id].questions[question_id]
        return {
            'status': 'OK',
            'question': render_template(
                'question_layout.html.j2',
                question_object=get_question_info(question, question_id))
        }
    return {'status': 'FAILED', 'question': ''}


@socketio.on('answer_question')
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
        socketio.emit('mayor_error',
                      f'Out of {answer_token.value} tokens',
                      room=game_id)
        return False

    if end_of_game:
        socketio.emit('mayor_error',
                      f'Last token played, Undo or Move to vote.',
                      room=game_id)
    game_status(game_id)


@socketio.on('get_game_state')
def game_status(game_id: str):
    app.logger.debug(
        f'Got game state request for {game_id} from {session["sid"]}')
    if game_id in GAMES:
        socketio.emit('game_state', parse_game_state(game_id, session['sid']))

# Mayor functions


@socketio.on('undo')
def undo(game_id: str):
    app.logger.debug(f'Attempting to undo something for {game_id}')
    if game_id in GAMES and GAMES[game_id].mayor == session['sid']:
        GAMES[game_id].undo_answer()
        game_status(game_id)


@socketio.on('start_vote')
def start_vote(game_id: str):
    if game_id in GAMES and GAMES[game_id].mayor == session['sid']:
        GAMES[game_id].start_vote()
        game_status(game_id)


@socketio.on('nominate_for_mayor')
def nominate_for_mayor(game_id: str):
    if game_id in GAMES and GAMES[game_id].is_player_in_game(session['sid']):
        GAMES[game_id].nominate_for_mayor(session['sid'])
        game_status(game_id)


@socketio.on('set_word_choice_count')
def set_word_choice_count(game_id: str, word_count: int):
    if game_id in GAMES and GAMES[game_id].admin == session['sid']:
        GAMES[game_id].set_word_choice_count(word_count)
        game_status(game_id)

    emit('admin_error', f'Unable to set word count to {word_count}.')


@socketio.on('get_words')
def get_words(game_id: str):
    if game_id in GAMES and GAMES[game_id].mayor == session['sid']:
        if GAMES[game_id].word:
            return {'status': 'FAILED'}
        words = GAMES[game_id].get_words()
        if words and GAMES[game_id].mayor == session['sid']:
            return {
                'status': 'OK',
                'word_html': render_template(
                    'word_choice.html.j2',
                    words=words,
                    game_id=game_id,
                )}
    return 'Unable to provide word choices.'

# Player targetting functions


@socketio.on('set_doppelganger_target')
def set_doppelganger_target(game_id: str, target_sid: str):
    if game_id in GAMES:
        if (isinstance(GAMES[game_id].get_player_role(session['sid']),
                       westwords.Doppelganger) and
                GAMES[game_id].is_player_in_game(target_sid)):
            GAMES[game_id].set_doppelganger_target(target_sid)
            game_status(game_id)


@socketio.on('set_player_target')
def set_player_target(game_id: str, target_sid: str):
    if game_id in GAMES:
        player_role = GAMES[game_id].get_player_role(session['sid'])
        if (player_role and player_role.is_targetting_role()):
            GAMES[game_id].set_player_target(session['sid'], target_sid)
            game_status(game_id)


@socketio.on('acknowledge_revealed_info')
def acknowledge_revealed_info(game_id: str):
    if game_id in GAMES:
        app.logger.debug(f'ACK attempt received for {PLAYERS[session["sid"]].name}')
        GAMES[game_id].acknowledge_revealed_info(session['sid'])
        game_status(game_id)


# TODO: implement all the scenarios around this
# Timer functions
@socketio.on('game_start')
def start_game(game_id: str):
    if game_id in GAMES:
        GAMES[game_id].start_night_phase_word_choice()
        game_status(game_id)


@socketio.on('game_reset')
def reset_game(game_id):
    # Implement game reset feature
    if game_id in GAMES and GAMES[game_id].admin == session['sid']:
        GAMES[game_id].reset()
        game_status(game_id)
    else:
        app.logger.debug('Unable to reset game. User not admin.')


@socketio.on('get_required_voters')
def get_required_voters(game_id: str):
    if game_id in GAMES:
        GAMES[game_id].get_required_voters()
        game_status(game_id)


@socketio.on('vote')
def vote(game_id, target_id):
    app.logger.debug(
        f"{PLAYERS[session['sid']].name} vote for {PLAYERS[target_id].name}")
    if (game_id in GAMES and
            session['sid'] in GAMES[game_id].get_required_voters()):
        GAMES[game_id].vote(session['sid'], target_id)
        game_status(game_id)


@socketio.on('get_results')
def get_results(game_id: str):
    if game_id in GAMES:
        emit('game_results', GAMES[game_id].get_results(), room=game_id)


@socketio.on('get_player_revealed_information')
def get_player_revealed_information(game_id: str):
    if (game_id in GAMES and session['sid'] in
        GAMES[game_id].get_players_needing_to_ack()):
        known_word, players = GAMES[game_id].get_player_revealed_information(session['sid'])
        known_players = []
        for player in players:
            known_players.append(
                {'name': PLAYERS[player].name, 'role': players[player],})
        app.logger.debug(f'Info: {known_word} players: {known_players}')
        return {
            'status': 'OK',
            'reveal_html': render_template(
                'player_reveal.html.j2',
                known_players=known_players,
                known_word=known_word,
                ),
        }
    return {'success': False, 'role': None}


@socketio.on('set_word')
def set_word(game_id: str, word: str):
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

    GAMES[game_id].set_word(word)
    game_status(game_id)


if __name__ == '__main__':
    socketio.run(app)

