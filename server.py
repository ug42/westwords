"""Westwords 20-ish-questions style game with social deduction and roles.

NOTE: can only use this configuration with a single worker because socketIO
and gunicorn are unable to handle sticky sessions. Boo. Scaling jobs will need
to account for a reverse proxy and keeping each server with a single worker
thread.

Ok, so I mean if I move the data for the rooms and Game and Player objects off
to a backing store, I think that would effectively solve for the worker thread
problem.

UPDATED NOTE: This may work for me now because I'm breaking out a lot of state
to move away from general broadcast, except for update notifications. I think
as long as the socket map and other global data store objects are accessible,
it may work.
"""

from collections import UserDict
import os
import re
from random import randint
import time
from uuid import uuid4

from flask import (Flask, flash, make_response, redirect, render_template,
                   request, send_from_directory, session, url_for)
from flask_socketio import SocketIO, emit, join_room, rooms

import westwords
from westwords.enums import AnswerToken
from westwords.game import GameError

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['USE_PERMANENT_SESSION'] = True
socketio = SocketIO(app)

# TOP LEVEL TODOs
# Server mechanics
# TODO: Add auto-destroy of game after some period of no updates.

# Game mechanics
# TODO: Add ability for people to join mid-game.
# TODO: Add known_info text when adding known_players to role this should be
#   like "Esper communicated with you during the night, or Mayor is the Seer,
#   so you are the Seer now."
# Add UI element to show selected roles

# UI mechanics
# TODO: Add ability to add own questions
# TODO: Figure out delete vs answer vs mayor prompt
#   Set delete and answer to be gated as close to state change as possible now.
#   Not mutex locking, so still possible.
#   Mayor questions on deleted questions should be updated.
# TODO: Fix how the refresh timer function interval gets reinitialize many times
#   whenever states refreshes/questions asked, etc.
# TODO: Show current game state so people know why we're waiting for people.
# TODO: Add a timer to the reveal section or do away with the ACK part
# TODO: Remove question from autocomplete if already asked.
# TODO: Remove gap above skip icon (Decrease size of icon maybe?)
# TODO: Allow ability to undo skipped question
# TODO: Add roles to the logged function
# TODO: Reported unable to answer question but still marks question.
#   Also reports success. Possibly getting multiple handlers registered?
#   Could be tied to the multiple timer updaters on game state/question updates
#   Yes, it's sending multiple requests.
# TODO: Move most javascript listeners off to be gated by control vars (set a
# secondary variable to true while running sort of thing.) Nvm, this doesn't
# work, it's like there's global scope, but it doesn't recognize it in other
# threads?

# TODO: move this off to a backing store.
SOCKET_MAP = {}
COMMON_QUESTIONS = [
    'Can it fly?',
    'Can you build it yourself?',
    'Can you build it yourself?',
    'Can you control it?',
    'Can you lift it?',
    'Can you lift it?',
    'Can you nail it?',
    'Can you own more than one?',
    'Can you own one?',
    'Can you purchase it?',
    'Can you safely eat it?',
    'Can you see it?',
    'Can you ship it?',
    'Can you smell it?',
    'Can you touch it?',
    'Do people regularly use it?',
    'Do you have more than one?',
    'Do you have one?',
    'Does it cost more than $20?',
    'Does it have a blade?',
    'Does it have feelings?',
    'Does it have hinge on it?',
    'Does it have opposable digits?',
    'Does it hold something inside it?',
    'Does it run on electricity?',
    'Does it weigh more than 100 lbs?',
    'Does it weigh more than 20 lbs?',
    'Does one exist in the Seattle metro area?',
    'Has it ever been alive?',
    'Is it a body of water?',
    'Is it a building?',
    'Is it a concept?',
    'Is it a game?',
    'Is it a physical thing?',
    'Is it a plant?',
    'Is it a proper noun?',
    'Is it a store?',
    'Is it a thing?',
    'Is it a tool?',
    'Is it alive?',
    'Is it an action?',
    'Is it art?',
    'is it associated with cars?',
    'Is it bigger than a bread box?',
    'Is it bigger than a car?'
    'Is it bigger than a planet?',
    'Is it considered expensive?',
    'Is it edible?',
    'Is it edible?',
    'Is it entertainment?',
    'Is it expensive?',
    'Is it food?',
    'Is it found in a house?',
    'Is it found on Earth?',
    'Is it geographic?',
    'Is it hand-held?',
    'Is it industrial?',
    'Is it larger than a bread box?',
    'Is it larger than a breadbox?',
    'is it larger than a car?',
    'Is it larger than a house?',
    'is it living?',
    'Is it made of metal?',
    'Is it mechanical?',
    'is it motorized?',
    'is it physical?',
    'Is it real?',
    'is it smaller than a car?',
    'Is it something someone can enter?',
    'Is it something that is used daily?',
    'Is it something you go into on a weekly basis?',
    'Is it sports related?',
    'Is it tall?',
    'Is it taught in elementary school?',
    'Is it taught in high school?',
    'Is it transportation related?',
    'Is it used for construction?',
    'Is it used in food preparation?',
    'Is it used outside?',
    'Is it used to make other things?',
    'Is it used with hands?',
    'Is it usually made of metal?',
    'Is it usually made of plastic?',
    'Is it usually made of wood?',
    'Is the person alive?',
    'It is exercise-related?',
    'Was it ever alive?',
    'Will i find it at a hardware store?',
    'Would a typical person own one?',
    'Would people use it regularly?',
    'Would someone have more than one?',
    'Would you find it in a garage?',
    'Would you find it somewhere other than a garage?',
    'Would you hold it to use it?',
]


class PlayerDict(UserDict):
    def __getitem__(self, key: any) -> westwords.Player:
        return super().__getitem__(key)


class GamesDict(UserDict):
    def __getitem__(self, key: any) -> westwords.Game:
        return super().__getitem__(key)


PLAYERS = PlayerDict()
GAMES = GamesDict()


def parse_game_state(game_id: str, session_sid: str):
    """Parses the initial game state dict + tuple into a dict with player info.

    Args:
        game_id: String game id on which to get game state.
        session_id: String session ID of requesting user.

    Returns:
        game_state: a dict of str 'game_state', int 'timer', str 'game_id',
            str 'mayor' name, str 'admin' name, bool 'player_is_mayor', bool
            'player_is_admin', a str 'role' for the player
    """
    # TODO: Move this whole thing to a damned GameStatus class cuz wow.
    if not game_id:
        GAMES[None] = westwords.Game(timer=0, player_sids=[])
    game_state = GAMES[game_id].get_state(game_id)
    game_state['update_timestamp'] = GAMES[game_id].get_update_timestamp()
    required_voters = GAMES[game_id].get_required_voters()
    players_needing_to_ack = GAMES[game_id].get_players_needing_to_ack()
    players_needing_to_target = GAMES[game_id].get_players_needing_to_target()
    spectators = GAMES[game_id].get_spectators()
    nominated_for_mayor = session['sid'] in GAMES[game_id].get_mayor_nominees()

    game_state.update({
        'players_names_needing_ack': [
            PLAYERS[p].name for p in players_needing_to_ack],
        'player_names_needing_vote': [PLAYERS[p].name for p in required_voters],
        'player_is_mayor': game_state['mayor'] == session_sid,
        'player_is_admin': game_state['admin'] == session_sid,
        'player_is_waiting_for_vote': session['sid'] in required_voters,
        'player_is_waiting_for_target': session['sid'] in players_needing_to_target,
        'player_is_waiting_for_ack': session['sid'] in players_needing_to_ack,
        'nominated_for_mayor': nominated_for_mayor,
        'spectating': session_sid in spectators,
        'spectators': [PLAYERS[p].name for p in spectators],
    })

    try:
        # Replace the mayor SID with name
        game_state['mayor'] = PLAYERS[game_state['mayor']].name
    except KeyError:
        game_state['mayor'] = None

    try:
        game_state['admin'] = PLAYERS[GAMES[game_id].admin].name
    except KeyError:
        game_state['admin'] = None

    players = GAMES[game_id].get_players()
    if session_sid in players:
        game_state['role'] = str(players[session_sid]).capitalize()
    else:
        game_state['role'] = 'Spectator'

    return game_state


def update_all_games_for_player(player_sid: str) -> None:
    if player_sid in PLAYERS:
        for game_id in PLAYERS[player_sid].get_rooms():
            mark_new_update(game_id)


def mark_new_update(game_id: str) -> None:
    if game_id in GAMES:
        new_timestamp = int(time.time() * 1000)
        GAMES[game_id].set_update_timestamp(new_timestamp)
        socketio.emit('game_state_update',
                      {'game_id': game_id, 'timestamp': new_timestamp},
                      room=game_id)


def mark_new_role_count(game_id: str, role: str) -> None:
    if game_id in GAMES:
        socketio.emit('role_update',
                      {'game_id': game_id, 'role': role},
                      room=game_id)


def refresh_players(game_id: str) -> None:
    if game_id in GAMES:
        socketio.emit('refresh_players', game_id)


def get_question_info(question: westwords.Question, id: int) -> dict[str, any]:
    return {
        'id': id,
        'question': question.question_text,
        'player': PLAYERS[question.player_sid].name,
        'answer': question.get_answer(),
        'skipped': question.skipped,
    }


def username_taken(username: str, user_sid: str) -> bool:
    for player in PLAYERS:
        if (PLAYERS[player].name.upper() == username.upper() and
                player != user_sid):
            return True
    return False


def log_game_state(game_id: str) -> None:
    app.logger.info(GAMES[game_id].print_log())


def check_session_config() -> str:
    if 'sid' not in session:
        app.logger.debug('adding SID')
        session['sid'] = str(uuid4())
    if 'autocomplete_enabled' not in session:
        session['autocomplete_enabled'] = False
    if 'username' not in session:
        app.logger.debug('adding username')
        u = f'Not_a_wolf_{randint(1000,9999)}'
        while username_taken(u, session['sid']):
            u = f'Not_a_wolf_{randint(1000,9999)}'
            app.logger.debug(f"{u} username taken, trying again")
        session['username'] = u
        if request.url and 'requesting_url' not in session:
            app.logger.debug(f'Adding redirect URL: {request.url}')
            session['requesting_url'] = request.url
        return '/login'

    if session['sid'] not in PLAYERS:
        app.logger.debug('Adding PLAYERS entry')
        PLAYERS[session['sid']] = westwords.Player(session['username'])

    PLAYERS[session['sid']].name = session['username']

    return ''


@app.route('/')
def index():
    redirect_url = check_session_config()
    if redirect_url:
        return redirect(redirect_url)
    return render_template('index.html.j2')


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/username', methods=['POST'])
def username():
    redirect_url = check_session_config()
    if redirect_url:
        return redirect(redirect_url)

    if request.method == 'POST' and request.form.get('username'):
        if request.form.get("requesting_url"):
            if 'requesting_url' not in session:
                session['requesting_url'] = request.form.get("requesting_url")
        if username_taken(request.form.get('username'), session['sid']):
            flash(f'Username {request.form.get("username")} taken.')
            return redirect(url_for('login'))
        if re.search(r'mayor', request.form.get('username').casefold()):
            flash('Cute, smartass.')
            if 'requesting_url' in session:
                return redirect(session.pop('requesting_url'))

        session['username'] = request.form.get('username')
        PLAYERS[session['sid']].name = session['username']
        update_all_games_for_player(session['sid'])

    if 'requesting_url' in session:
        return redirect(session.pop('requesting_url'))
    return redirect('/')


@app.route('/privacy_policy')
def privacy_policy():
    return render_template('privacy_policy.html.j2')


@app.route('/join/<game_id>', strict_slashes=False)
@app.route('/join?game_name=<game_id>', strict_slashes=False)
def join_game(game_id: str):
    redirect_url = check_session_config()
    if redirect_url:
        return redirect(redirect_url)

    game_id = game_id.casefold()
    app.logger.debug(
        f"{PLAYERS[session['sid']].name} attempting to join {game_id}")
    if game_id in GAMES:
        app.logger.debug(f"game_id found: {game_id}")
        GAMES[game_id].add_player(session['sid'])
        PLAYERS[session['sid']].join_room(game_id)
        mark_new_update(game_id)
        GAMES[game_id].log(f'{PLAYERS[session["sid"]].name} joined {game_id}')
    else:
        return redirect(f'/create/{game_id}')
    return redirect(f'/game/{game_id}')


@app.route('/leave/<game_id>', strict_slashes=False)
def leave_game(game_id: str):
    redirect_url = check_session_config()
    if redirect_url:
        return redirect(redirect_url)

    game_id = game_id.casefold()
    if game_id in GAMES:
        GAMES[game_id].remove_player(session['sid'])
        GAMES[game_id].remove_spectator(session['sid'])
        GAMES[game_id].log(f'{PLAYERS[session["sid"]].name} left {game_id}')
        if (len(GAMES[game_id].get_players()) == 0 and
                len(GAMES[game_id].get_spectators()) == 0):
            GAMES[game_id].log(
                f'{PLAYERS[session["sid"]].name} is final player for {game_id};'
                ' destroying game')
            log_game_state(game_id)
            del GAMES[game_id]
    mark_new_update(game_id)
    return redirect('/')


@app.route('/spectate/<game_id>')
def spectate_game(game_id: str):
    redirect_url = check_session_config()
    if redirect_url:
        return redirect(redirect_url)

    game_id = game_id.casefold()
    if game_id in GAMES:
        # this should keep the player in the room for broadcast state, but not
        # game mechanics.
        GAMES[game_id].remove_player(session['sid'])
        GAMES[game_id].add_spectator(session['sid'])
        GAMES[game_id].log(
            f'{PLAYERS[session["sid"]].name} started spectating {game_id}')
        mark_new_update(game_id)
        return redirect(f'/game/{game_id}')
    flash(f'Unable to find game: {game_id}')
    return redirect('/')


@app.route('/game/<game_id>', strict_slashes=False)
def game_index(game_id: str):
    redirect_url = check_session_config()
    if redirect_url:
        return redirect(redirect_url)

    game_id = game_id.casefold()
    if game_id not in GAMES:
        return redirect(f'/create/{game_id}')
    if 'sid' not in session:
        session['sid'] = str(uuid4())
    if 'username' not in session:
        session['username'] = f'Not_a_wolf_{randint(1000,9999)}'
        session['requesting_url'] = request.url
        return redirect(url_for('login'))
    if session['sid'] not in PLAYERS:
        PLAYERS[session['sid']] = westwords.Player(session['username'])
    if session['sid'] not in (list(GAMES[game_id].get_players().keys()) +
                              list(GAMES[game_id].get_spectators())):
        return redirect(f'/join/{game_id}')

    if game_id in GAMES:
        game_state = parse_game_state(game_id, session['sid'])
    else:
        game_state = parse_game_state(None, session['sid'])

    if 'autocomplete_enabled' not in session:
        autocomplete_enabled = False
    else:
        autocomplete_enabled = session['autocomplete_enabled']

    return render_template(
        'game.html.j2',
        game_id=game_id,
        game_state=game_state['game_state'],
        game_timer=game_state['timer'],
        mayor=game_state['mayor'],
        player_is_mayor=game_state['player_is_mayor'],
        player_is_admin=game_state['player_is_admin'],
        role=game_state['role'],
        autocomplete_enabled=autocomplete_enabled,
        common_questions=COMMON_QUESTIONS,
        # Remove this when done poking at things. :P
        DEBUG=app.config['DEBUG'],
    )


@app.route('/create', methods=['POST', 'GET'], strict_slashes=False)
@app.route('/create/<game_id>', methods=['GET'], strict_slashes=False)
def create_game(game_id: str = None):
    redirect_url = check_session_config()
    if redirect_url:
        return redirect(redirect_url)

    if request.method == 'POST' and request.form['game_id']:
        game_id = request.form['game_id']
    if not game_id:
        app.logger.debug(f'No game_id specified')
        return redirect('/')
    game_id = game_id.casefold()
    if game_id not in GAMES:
        GAMES[game_id] = westwords.Game(player_sids=[session['sid']])
        GAMES[game_id].log(
            f'{PLAYERS[session["sid"]].name} created game {game_id}')

    return redirect(f'/join/{game_id}')


@app.route('/toggle_autocomplete', methods=['POST'])
def toggle_autocomplete():
    check_session_config()
    session['autocomplete_enabled'] = not session['autocomplete_enabled']
    if request.form.get('requesting_url') and 'requesting_url' not in session:
        session['requesting_url'] = request.form.get("requesting_url")

    if 'requesting_url' in session:
        return redirect(session.pop('requesting_url'))
    return redirect('/')


@app.route('/settings', methods=['GET'])
def settings(setting: str = None):
    redirect_url = check_session_config()
    if redirect_url:
        return redirect(redirect_url)
    return render_template('settings.html.j2',
                           autocomplete_enabled=session['autocomplete_enabled'])


@app.route('/login')
def login():
    redirect_url = check_session_config()
    if redirect_url:
        return redirect(redirect_url)

    return render_template('login.html')


@app.route('/logout')
def logout():
    redirect_url = check_session_config()
    if redirect_url:
        return redirect(redirect_url)

    # storing this so we can destroy the session then disassociate the player
    s = session['sid']
    response = make_response(render_template('logout.html'))
    session.clear()
    response.set_cookie(app.config['SESSION_COOKIE_NAME'], expires=0)

    # Remove player and disassociate references to them
    update_all_games_for_player(s)
    del PLAYERS[s]

    flash('Session destroyed. You are now logged out; redirecting to /')
    return response


# Socket control functions
@socketio.on('connect')
def connect(auth: str):
    if 'sid' not in session:
        session['sid'] = str(uuid4())
    if session['sid'] not in PLAYERS:
        PLAYERS[session['sid']] = westwords.Player(session['username'])
    SOCKET_MAP[session['sid']] = request.sid
    for room in PLAYERS[session['sid']].get_rooms():
        if room not in rooms():
            join_room(room)


@socketio.on('disconnect')
def disconnect():
    try:
        del SOCKET_MAP[session['sid']]
    except KeyError as e:
        app.logger.debug(
            f"Unable to remove socket mapping for {session['sid']}: {e}")


@socketio.on('question')
def add_question(game_id: str, question_text: str):
    if game_id in GAMES:
        try:
            success, _ = GAMES[game_id].add_question(
                session['sid'], question_text)
        except GameError as e:
            app.logger.debug(e)
            app.logger.error(f'Unable to add question for game {game_id}')
            return False
        if success:
            GAMES[game_id].log(
                f'{PLAYERS[session["sid"]].name} asked question: '
                f'{question_text}'
            )
            mark_new_update(game_id)
            return True

    app.logger.error(f'Unable to add question for game {game_id}')
    return False


@socketio.on('get_questions')
def get_questions(game_id: str):
    if game_id in GAMES:
        questions = GAMES[game_id].get_questions()
        questions_html = ''
        tokens = [
            token for token in GAMES[game_id].tokens if GAMES[game_id].tokens[token] > 0]
        for id, question in enumerate(questions):
            if not question.is_deleted():
                question_info = get_question_info(question, id)
                questions_html = render_template(
                    'question_layout.html.j2',
                    question_object=question_info,
                    player_is_mayor=GAMES[game_id].mayor == session['sid'],
                    own_question=question.player_sid == session['sid'],
                    game_id=game_id,
                    tokens=tokens,
                ) + questions_html
        return {
            'status': 'OK',
            'questions_html': questions_html,
        }
    return {'status': 'ERROR', 'question': ''}


@socketio.on('get_next_unanswered_question')
def get_mayor_question(game_id: str) -> None:
    if game_id in GAMES:
        if session['sid'] != GAMES[game_id].mayor:
            return {'status': 'NONE', 'question_html': ''}
        questions = GAMES[game_id].get_questions()
        tokens = []
        for token in GAMES[game_id].tokens:
            if GAMES[game_id].tokens[token] > 0:
                tokens.append(token)
        for id, question in enumerate(questions):
            if not question.get_answer() and not (
                    question.is_skipped() or question.is_deleted()):
                question_info = get_question_info(question, id)
                return {'status': 'OK',
                        'question_html': render_template(
                            'mayor_question_layout.html.j2',
                            game_id=game_id,
                            question_object=question_info,
                            question_id=id,
                            tokens=tokens,),
                        }
    return {'status': 'NO_DATA', 'question_html': ''}


@socketio.on('get_players')
def get_players(game_id: str):
    if game_id in GAMES:
        player_sids = GAMES[game_id].get_players()
        admin = GAMES[game_id].admin
        mayor = GAMES[game_id].mayor
        mayor_tokens = GAMES[game_id].tokens
        mayor_token_count = []
        mayor_token_count.append({
            'token': {
                'token_text': 'Yes/No',
                'token_icon': AnswerToken.YES.token_icon,
            },
            'count': mayor_tokens[AnswerToken.YES],
        })
        for token in mayor_tokens:
            if token not in [AnswerToken.YES, AnswerToken.NO]:
                mayor_token_count.append(
                    {'token': token, 'count': mayor_tokens[token]}
                )

        players = []
        for player_sid in player_sids:
            tokens = GAMES[game_id].get_player_token_count(player_sid)
            token_count = []
            voted = False
            spectators = []
            for spectator in GAMES[game_id].get_spectators():
                spectators.append(PLAYERS[spectator].name)
            if GAMES[game_id].is_voting():
                voted = (player_sid in
                         GAMES[game_id].get_players_needing_to_vote())
            for token in tokens:
                token_count.append({'token': token, 'count': tokens[token]})
            players.append({
                'name': PLAYERS[player_sid].name,
                'token_count': token_count,
                'mayor': player_sid == mayor,
                'admin': player_sid == admin,
                'voted': voted,
            })
        players_html = render_template(
            'player_layout.html.j2',
            players=players,
            spectators=spectators,
            mayor_token_count=mayor_token_count)
        return {
            'status': 'OK',
            'players_html': players_html,
        }
    return {'status': 'ERROR', 'question': ''}


@socketio.on('answer_question')
def answer_question(game_id: str, question_id: int, answer: str):
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
    error = GAMES[game_id].answer_question(question_id,
                                           answer_token)
    if error:
        socketio.emit('mayor_error',
                      (error +
                       '<br><button type="button" class="mdl-button close"'
                       ' onclick="close_dialog()">OK</button>'),
                      room=game_id)
        return False

    GAMES[game_id].log(
        f'Mayor {PLAYERS[session["sid"]].name} answered the question '
        f'"{str(GAMES[game_id].get_question(question_id))}" with '
        f'"{answer_token.token_text}".')
    mark_new_update(game_id)


@socketio.on('get_game_state')
def game_status(game_id: str, timestamp: int):
    if game_id in GAMES:
        if GAMES[game_id].get_update_timestamp() == timestamp:
            return {
                'status': 'NO_UPDATE',
                'game_state': '',
            }
        return {
            'status': 'OK',
            'game_state': parse_game_state(game_id, session['sid']),
        }
    return {'status': 'ERROR', 'game_state': ''}


# Mayor functions
@socketio.on('undo')
def undo(game_id: str):
    app.logger.debug(f'Attempting to undo answer for {game_id}')
    if game_id in GAMES and GAMES[game_id].mayor == session['sid']:
        GAMES[game_id].log(
            f'{PLAYERS[session["sid"]].name} attempting to undo last answer.')
        GAMES[game_id].undo_answer()

        mark_new_update(game_id)


@socketio.on('start_vote')
def start_vote(game_id: str):
    app.logger.debug(
        f'Attempting to start vote from {PLAYERS[session["sid"]].name}.')
    if game_id in GAMES and GAMES[game_id].mayor == session['sid']:
        GAMES[game_id].log(
            f'{PLAYERS[session["sid"]].name} attempting to start voting.')
        success = GAMES[game_id].start_vote()
        if success:
            GAMES[game_id].log('Voting is started.')
            mark_new_update(game_id)
            return {'status': 'OK'}
    return {'status': 'ERROR'}


@socketio.on('nominate_for_mayor')
def nominate_for_mayor(game_id: str):
    if game_id in GAMES and GAMES[game_id].is_player_in_game(session['sid']):
        if GAMES[game_id].nominate_for_mayor(session['sid']):
            app.logger.debug(f'{PLAYERS[session["sid"]].name} ran for mayor')
            GAMES[game_id].log(
                f'{PLAYERS[session["sid"]].name} runs for mayor')
            return {'status': 'OK'}
    return {'status': 'ERROR'}


@socketio.on('set_word_choice_count')
def set_word_choice_count(game_id: str, word_count: int):
    if game_id in GAMES and GAMES[game_id].admin == session['sid']:
        GAMES[game_id].log(
            f'{PLAYERS[session["sid"]].name} setting word choice count to '
            f'{word_count}')
        GAMES[game_id].set_word_choice_count(word_count)
        mark_new_update(game_id)

    socketio.emit('admin_error',
                  (f'Unable to set word count to {word_count}.'
                   '<br><button type="button" class="mdl-button close"'
                   ' onclick="close_dialog()">OK</button>'),
                  room=game_id)


@socketio.on('get_words')
def get_words(game_id: str):
    if game_id in GAMES and GAMES[game_id].mayor == session['sid']:
        if GAMES[game_id].word:
            return {'status': 'ERROR'}
        words = GAMES[game_id].get_words()
        role = GAMES[game_id].get_player_role(session['sid'])
        if words and GAMES[game_id].mayor == session['sid']:
            GAMES[game_id].log(
                f'{PLAYERS[session["sid"]].name} retrieve word choices: '
                f'{words}')
            return {
                'status': 'OK',
                'word_html': render_template(
                    'word_choice.html.j2',
                    words=words,
                    player_role=str(role),
                    image=role.get_image_name(),
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
            success = GAMES[game_id].set_doppelganger_target(target_sid)
            if success:
                GAMES[game_id].log(
                    f'{PLAYERS[session["sid"]].name}, as doppelganger, '
                    f'targetted {PLAYERS[target_sid].name}, becoming a '
                    f'{str(GAMES[game_id].get_player_role(target_sid))}'
                )
                mark_new_update(game_id)


@socketio.on('set_player_target')
def set_player_target(game_id: str, target_sid: str):
    if game_id in GAMES:
        player_role = GAMES[game_id].get_player_role(session['sid'])
        if (player_role and player_role.is_targetting_role()):
            if GAMES[game_id].set_player_target(session['sid'], target_sid):
                GAMES[game_id].log(
                    f'{PLAYERS[session["sid"]].name}, as {str(player_role)}, '
                    f'targetted {PLAYERS[target_sid].name} in the night.'
                )
                if len(GAMES[game_id].get_players_needing_to_target()) == 0:
                    mark_new_update(game_id)


@socketio.on('acknowledge_revealed_info')
def acknowledge_revealed_info(game_id: str):
    if game_id in GAMES:
        app.logger.debug(
            f'ACK attempt received for {PLAYERS[session["sid"]].name}')
        GAMES[game_id].acknowledge_revealed_info(session['sid'])
        GAMES[game_id].log(
            f'{PLAYERS[session["sid"]].name} hit OK on their role information')
        if len(GAMES[game_id].get_players_needing_to_ack()) == 0:
            mark_new_update(game_id)


# Timer functions
@socketio.on('set_timer')
def set_timer(game_id: str, timer_seconds: int):
    if game_id in GAMES:
        if GAMES[game_id].admin == session['sid']:
            GAMES[game_id].set_timer(int(timer_seconds))
            GAMES[game_id].log(
                f'{PLAYERS[session["sid"]].name} set timer for {game_id} to '
                f'{timer_seconds} seconds')
            mark_new_update(game_id)


@socketio.on('set_vote_timer')
def set_vote_timer(game_id: str, vote_timer_seconds: int):
    if game_id in GAMES:
        GAMES[game_id].set_vote_timer(vote_timer_seconds)
        GAMES[game_id].log(
            f'{PLAYERS[session["sid"]].name} set vote timer for {game_id} to '
            f'{vote_timer_seconds} seconds')


@socketio.on('game_start')
def start_game(game_id: str):
    if game_id in GAMES:
        try:
            GAMES[game_id].start_night_phase_word_choice()
            GAMES[game_id].log(
                f'{PLAYERS[session["sid"]].name} started game named {game_id}')
            mark_new_update(game_id)
        except GameError as e:
            socketio.emit('user_info', f"Game start failed. {e}")


@socketio.on('game_reset')
def reset_game(game_id):
    if game_id in GAMES and GAMES[game_id].admin == session['sid']:
        GAMES[game_id].log(
            f'{PLAYERS[session["sid"]].name} reset game {game_id}')
        log_game_state(game_id)
        GAMES[game_id].reset()
        mark_new_update(game_id)
    else:
        app.logger.debug('Unable to reset game. User not admin.')


@socketio.on('vote')
def vote(game_id, target_id):
    if target_id in PLAYERS:
        app.logger.debug(
            f"{PLAYERS[session['sid']].name} vote for "
            f"{PLAYERS[target_id].name}, game id: {game_id}")
        if game_id in GAMES:
            app.logger.debug(f'Attempting to vote for {target_id}')
            try:
                if GAMES[game_id].vote(session['sid'], target_id):
                    GAMES[game_id].log(
                        f'{PLAYERS[session["sid"]].name} voted for '
                        f'{PLAYERS[target_id].name}')
                    if len(GAMES[game_id].get_players_needing_to_vote()) == 0:
                        mark_new_update(game_id)
                    else:
                        refresh_players(game_id)
            except GameError as e:
                if session['sid'] in SOCKET_MAP:
                    socketio.emit('user_info',
                                  f'Vote failed: {e}',
                                  to=SOCKET_MAP[session['sid']])

    else:
        app.logger.debug(f'Unknown player SID {target_id}')


@socketio.on('get_results')
def get_results(game_id: str):
    if game_id in GAMES:
        winner, killed_sids, votes, player_sids = GAMES[game_id].get_results()
        role = GAMES[game_id].get_player_role(session['sid'])
        player_won = role.get_affiliation() == winner
        vote_information = []
        non_voting_players = []
        for player_sid in player_sids:
            if player_sid not in votes:
                non_voting_players.append({
                    'player': PLAYERS[player_sid].name,
                    'role': str(player_sids[player_sid]),
                })
        for voter_sid in votes:
            vote_information.append({
                'voter': PLAYERS[voter_sid].name,
                'voter_role': str(GAMES[game_id].get_player_role(voter_sid)),
                'target': PLAYERS[votes[voter_sid]].name,
                'target_role': str(GAMES[game_id].get_player_role(votes[voter_sid])),
            })
        v = {}
        for vote in votes:
            if votes[vote] not in v:
                v[votes[vote]] = 0
            v[votes[vote]] += 1
        vote_count = []
        for target in v:
            vote_count.append({'name': PLAYERS[target].name,
                               'role': str(player_sids[target]),
                               'count': v[target],
                               'killed': target in killed_sids})

        killed_names = []
        for killed_sid in killed_sids:
            killed_names.append(PLAYERS[killed_sid].name)
        return {
            'status': 'OK',
            'results_html': render_template(
                'results.html.j2',
                winner=winner.value,  # This should be the capitalized string
                player_won=player_won,
                role=role,
                vote_count=vote_count,
                vote_information=vote_information,
                non_voting_players=non_voting_players,
                mayor=PLAYERS[GAMES[game_id].mayor].name,
            ),
        }
    return {'status': 'ERROR', 'results_html': None}


@socketio.on('get_player_revealed_information')
def get_player_revealed_information(game_id: str):
    if (game_id in GAMES and session['sid'] in
            GAMES[game_id].get_players_needing_to_ack()):
        known_word, players = GAMES[game_id].get_player_revealed_information(
            session['sid'])
        known_players = []
        for player in players:
            known_players.append(
                {'name': PLAYERS[player].name, 'role': players[player], })
        role = GAMES[game_id].get_player_role(session['sid'])
        return {
            'status': 'OK',
            'reveal_html': render_template(
                'player_reveal.html.j2',
                player_role=str(role),
                image=role.get_image_name(),
                known_players=known_players,
                known_word=known_word,
                mayor=PLAYERS[GAMES[game_id].mayor].name,
                role_description=role.get_role_description().strip(),
            ),
        }
    return {'status': 'ERROR', 'reveal_html': None}


@socketio.on('get_voting_page')
def get_voting_information(game_id: str):
    if (game_id in GAMES and session['sid']):
        voter_sids, votes, word_guessed, candidate_sids = GAMES[game_id].voting_info(
        )
        if not voter_sids:
            socketio.emit('mayor_error',
                          (f'No voting players found for game {game_id}'
                           '<br><button type="button" class="mdl-button close"'
                           ' onclick="close_dialog()">OK</button>'),)
            return {'status': 'ERROR', 'voting_html': None}
        voters = []
        for voter_sid in voter_sids:
            if voter_sid not in votes:
                voters.append(PLAYERS[voter_sid].name)
        candidates = []
        for candidate_sid in candidate_sids:
            if candidate_sid != session['sid']:
                candidates.append(
                    {'sid': candidate_sid,
                     'name': PLAYERS[candidate_sid].name})

        if word_guessed:
            voting_text = ('Werewolf team! find the Seer, Intern or Fortune '
                           'Teller!')
        else:
            voting_text = ('Everyone! Find a Werewolf or Minion!')

        try:
            word = GAMES[game_id].get_word()
            required_voters = GAMES[game_id].get_required_voters()
        except GameError as e:
            socketio.emit(
                'user_info', f'Failed to get word: {e}', room=game_id)
            return {'status': 'ERROR', 'voting_html': None}

        if session['sid'] in required_voters:
            return {
                'status': 'OK',
                'voting_html': render_template(
                    'voting.html.j2',
                    word=word,
                    game_id=game_id,
                    voting_text=voting_text,
                    candidates=candidates,
                ),
            }
        else:
            return {
                'status': 'OK',
                'voting_html': render_template(
                    'voting.html.j2',
                    word=word,
                    game_id=game_id,
                    voting_text=voting_text,
                    candidates=[],
                ),
            }
    return {'status': 'ERROR', 'voting_html': None}


@socketio.on('get_night_action_page')
def get_night_action_page(game_id: str):
    if (game_id in GAMES and
        session['sid'] and
            GAMES[game_id].is_night_action_phase()):
        if session['sid'] not in GAMES[game_id].get_players_needing_to_target():
            return {'status': 'NO_ACTION', 'voting_html': None}

        candidate_sids = GAMES[game_id].get_players()
        candidates = []
        for candidate_sid in candidate_sids:
            if candidate_sid != session['sid']:
                candidates.append(
                    {'sid': candidate_sid,
                     'name': PLAYERS[candidate_sid].name})

        role = GAMES[game_id].get_player_role((session['sid']))
        night_action_description = role.get_night_action_description()
        if str(role) == 'Doppelganger':
            js_function = 'set_doppelganger_target'
        else:
            js_function = 'set_player_target'

        return {
            'status': 'OK',
            'night_action_html': render_template(
                'night_action.html.j2',
                js_function=js_function,
                role=str(role),
                game_id=game_id,
                candidates=candidates,
                night_action_text=night_action_description,
            ),
        }
    return {'status': 'ERROR', 'night_action_html': None}


@socketio.on('set_word')
def set_word(game_id: str, word: str):
    """Set the chosen word for the provided game ID.

    Args:
        game_id: String game ID referencing the game.
        word: String word referencing the word to set as the chosen word for the
            game.
    """
    if game_id not in GAMES:
        socketio.emit('mayor_error',
                      (f'Unable to set word for game {game_id}.'
                       '<br><button type="button" class="mdl-button close"'
                       ' onclick="close_dialog()">OK</button>'),
                      )
        return

    if session['sid'] != GAMES[game_id].mayor:
        socketio.emit('mayor_error',
                      (f'Word set attempt failed. User is not mayor.'
                       '<br><button type="button" class="mdl-button close"'
                       ' onclick="close_dialog()">OK</button>'),)
        return

    words = GAMES[game_id].get_words()
    if GAMES[game_id].set_word(word):
        GAMES[game_id].log(f'Mayor {PLAYERS[session["sid"]].name} chose word '
                           f'"{word}". Possible options are {words}')
        mark_new_update(game_id)


@socketio.on('delete_question')
def delete_question(game_id: str, question_id: int):
    if game_id in GAMES:
        q = GAMES[game_id].get_question(question_id)
        if session['sid'] == q.player_sid:
            try:
                GAMES[game_id].delete_question(question_id)
                GAMES[game_id].log(
                    f'{PLAYERS[session["sid"]].name} deleted question: '
                    f'{str(GAMES[game_id].get_question(question_id))}')
                mark_new_update(game_id)
            except GameError as e:
                socketio.emit('user_info',
                              e,
                              to=SOCKET_MAP[session['sid']])


@socketio.on('finish_vote')
def finish_vote(game_id: str):
    if game_id in GAMES:
        if session['sid'] == GAMES[game_id].mayor:
            if GAMES[game_id].finish_game():
                log_game_state(game_id)
                mark_new_update(game_id)


@socketio.on('get_footer')
def get_footer(game_id: str):
    if game_id in GAMES:
        known_word, players = GAMES[game_id].get_player_revealed_information(
            session['sid'])
        known_players = []
        if players:
            for player in players:
                known_players.append(
                    {'name': PLAYERS[player].name, 'role': players[player], })
        role = GAMES[game_id].get_player_role(session['sid'])
        game_state = GAMES[game_id].game_state.name
        mayor = ''
        if GAMES[game_id].mayor:
            mayor = PLAYERS[GAMES[game_id].mayor].name
        voters = []
        for voter in GAMES[game_id].get_players_needing_to_vote():
            voters.append(PLAYERS[voter].name)
        return {
            'status': 'OK',
            'footer_html': render_template(
                'footer.html.j2',
                game_state=game_state,
                player_role=str(role),
                known_players=known_players,
                known_word=known_word,
                mayor=mayor,
                admin=PLAYERS[GAMES[game_id].admin].name,
            ),
        }
    return {'status': 'NO_DATA', 'footer_html': None}


@socketio.on('skip_question')
def skip_question(game_id: str, question_id: int) -> None:
    app.logger.debug('Attempting to skip question')
    if game_id in GAMES:
        if GAMES[game_id].skip_question(game_id, question_id):
            GAMES[game_id].log(
                f'{PLAYERS[session["sid"]].name} skipped question '
                f'"{str(GAMES[game_id].get_question(question_id))}" skipped')
            mark_new_update(game_id)


@socketio.on('get_bootable_players')
def get_bootable_players(game_id: str) -> None:
    if game_id in GAMES:
        if session['sid'] == GAMES[game_id].admin:
            player_sids = GAMES[game_id].get_players()
            players = []
            for player_sid in player_sids:
                players.append(
                    {'sid': player_sid, 'name': PLAYERS[player_sid].name})
            return {'status': 'OK',
                    'html': render_template('boot_player.html.j2',
                                            players=players,
                                            game_id=game_id),
                    }
    return {'status': 'NO_DATA', 'html': ''}


@socketio.on('boot_player')
def boot_player(game_id: str, player_sid: str):
    app.logger.debug(f'Attempting to boot player: {PLAYERS[player_sid].name}')

    if game_id in GAMES:
        if (session['sid'] == GAMES[game_id].admin and
                player_sid in GAMES[game_id].get_players()):
            GAMES[game_id].remove_player(player_sid)
            GAMES[game_id].add_spectator(player_sid)
            GAMES[game_id].log(
                f'{PLAYERS[session["sid"]].name} booted '
                f'{PLAYERS[player_sid].name}')
            mark_new_update(game_id)


@socketio.on('get_role_page')
def get_roles(game_id: str):
    if game_id in GAMES:
        player_is_admin = session['sid'] == GAMES[game_id].admin
        roles = GAMES[game_id].get_roles()
        return {
            'status': 'OK',
            'role_html': render_template('role_layout.html.j2',
                                         game_id=game_id,
                                         roles=roles,
                                         player_is_admin=player_is_admin,
                                         )
        }


@socketio.on('add_role')
def add_role(game_id: str, role: str):
    if game_id in GAMES:
        if GAMES[game_id].add_role(role):
            GAMES[game_id].log(f'Added {role} to game.')
            mark_new_role_count(game_id, role)


@socketio.on('remove_role')
def remove_role(game_id: str, role: str):
    if game_id in GAMES:
        if GAMES[game_id].remove_role(role):
            GAMES[game_id].log(f'Removed {role} to game.')
            mark_new_role_count(game_id, role)


@socketio.on('get_role_count')
def get_role_count(game_id: str, role: str):
    if game_id in GAMES:
        return {
            'status': 'OK',
            'count': GAMES[game_id].get_role_count(role),
            'element_id': GAMES[game_id].get_role_element_id(role),
        }
    return {'status': 'ERROR', 'count': '', 'element_id': ''}


if __name__ == '__main__':
    socketio.run(app)
