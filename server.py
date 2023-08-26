# Westwords 20-questions style game with social deduction and roles.
#
# NOTE: can only use this configuration with a single worker because socketIO
# and gunicorn are unable to handle sticky sessions. Boo. Scaling jobs will need
# to account for a reverse proxy and keeping each server with a single worker
# thread.
#
# Ok, so I mean if I move the data for the rooms and Game and Player objects off
# to a backing store, I think that would effectively solve for the worker thread
# problem.

from collections import UserDict
from datetime import timedelta
import os
import re
from random import randint
import time
from uuid import uuid4

from flask import (Flask, flash, make_response, redirect, render_template,
                   request, send_from_directory, session, url_for)
from flask_socketio import SocketIO, emit, join_room, leave_room, rooms

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
# TODO: Add ability of question asker to remove question if not answered
# TODO: Add ability to kick players
# TODO: Add ability to make others admin
# TODO: Add ability for people to join mid-game.
# TODO: Add known_info text when adding known_players to role this should be
#   like "Esper communicated with you during the night, or Mayor is the Seer,
#   so you are the Seer now."
# TODO: Add a button for "Maybe, but let's not go there."
# TODO: Add timer to vote mechanic

# UI elements
# TODO: Build custom set of questions
# TODO: Stop UI flashing from updates UI elements reloading
# TODO: Increase font
# TODO: Add a frequent set of questions.
# TODO: Display word throughout game for roles that know it
# TODO: Display votes and roles at end of game
# TODO: Add button to refusing to answer question
# TODO: Move the vote/player_target/reveal dialog to hidden divs
# TODO: Make this not flash the screen each time mark_new_update is called.
#   (UI elements reloading)


SOCKET_MAP = {}
# TODO: move this off to a backing store.


class PlayerDict(UserDict):
    def __getitem__(self, key: any) -> westwords.Player:
        return super().__getitem__(key)


class GamesDict(UserDict):
    def __getitem__(self, key: any) -> westwords.Game:
        return super().__getitem__(key)


# TODO: move this off to a backing store.
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
            'player_is_admin', a str 'question_html' of formatted questions, a
            list of str 'players' names, and a str 'role' for the player, a list of str .
    """
    # TODO: Move this whole thing to a damned GameStatus class cuz wow.
    if not game_id:
        GAMES[None] = westwords.Game(timer=0, player_sids=[])
    game_state = GAMES[game_id].get_state(game_id)
    questions = GAMES[game_id].get_questions()
    player_sids = GAMES[game_id].get_players()

    game_state['update_timestamp'] = GAMES[game_id].get_update_timestamp()

    game_state['question_html'] = ''

    for id, question in enumerate(questions):
        if not question.is_deleted():
            question_info = get_question_info(question, id)
            game_state['question_html'] = render_template(
                'question_layout.html.j2',
                question_object=question_info,
                player_is_mayor=GAMES[game_id].mayor == session_sid,
                own_question=question.player_sid == session_sid,
                game_id=game_id,
            ) + game_state['question_html']

    required_voters = GAMES[game_id].get_required_voters()
    players_needing_to_ack = GAMES[game_id].get_players_needing_to_ack()
    players_needing_to_target = GAMES[game_id].get_players_needing_to_target()
    spectators = GAMES[game_id].get_spectators()

    players = {}
    for player_sid in player_sids:
        player = PLAYERS[player_sid]
        players[player.name] = {}
        for token, count in GAMES[game_id].get_player_token_count(
                player_sid).items():
            players[player.name][token.value] = count

    game_state.update({
        'players_names_needing_ack': [
            PLAYERS[p].name for p in players_needing_to_ack],
        'player_names_needing_vote': [PLAYERS[p].name for p in required_voters],
        'player_is_mayor': game_state['mayor'] == session_sid,
        'player_is_admin': game_state['admin'] == session_sid,
        'player_is_waiting_for_vote': session['sid'] in required_voters,
        'player_is_waiting_for_target': session['sid'] in players_needing_to_target,
        'player_is_waiting_for_ack': session['sid'] in players_needing_to_ack,
        'spectating': session_sid in spectators,
        'players': players,
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

    if session_sid in player_sids:
        game_state['role'] = str(player_sids[session_sid]).capitalize()
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


def get_question_info(question: westwords.Question, id: int):
    return {
        'id': id,
        'question': question.question_text,
        'player': PLAYERS[question.player_sid].name,
        'answer': question.get_answer(),
    }


def username_taken(username: str, user_sid: str):
    for player in PLAYERS:
        if (PLAYERS[player].name.upper() == username.upper() and
                player != user_sid):
            return True
    return False


def check_session_config():
    if 'sid' not in session:
        session['sid'] = str(uuid4())
    if 'username' not in session:
        u = f'Not_a_wolf_{randint(1000,9999)}'
        while username_taken(u, session['sid']):
            u = f'Not_a_wolf_{randint(1000,9999)}'
            app.logger.debug(f"{u} username taken, trying again")
        session['username'] = u
        session['requesting_url'] = request.url
        return redirect(url_for('login'))
    if session['sid'] not in PLAYERS:
        PLAYERS[session['sid']] = westwords.Player(session['username'])


@app.route('/')
def index():
    check_session_config()
    return render_template('index.html.j2')


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/username', methods=['POST'])
def username():
    check_session_config()
    if request.method == 'POST' and request.form.get('username'):
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


@app.route('/join/<game_id>', strict_slashes=False)
@app.route('/join?game_name=<game_id>', strict_slashes=False)
def join_game(game_id: str):
    check_session_config()
    app.logger.debug(
        f"{PLAYERS[session['sid']].name} attempting to join {game_id}")
    if game_id in GAMES:
        app.logger.debug(f"game_id found: {game_id}")
        GAMES[game_id].add_player(session['sid'])
        PLAYERS[session['sid']].join_room(game_id)
        mark_new_update(game_id)
        socketio.emit('user_info', f"{PLAYERS[session['sid']].name} joined.",
                      room=game_id)
    else:
        return redirect(f'/create/{game_id}')
    return redirect(f'/game/{game_id}')


@app.route('/leave/<game_id>', strict_slashes=False)
@app.route('/leave', strict_slashes=False)
def leave_game(game_id: str = None):
    check_session_config()
    if game_id:
        if game_id in GAMES:
            GAMES[game_id].remove_player(session['sid'])
            GAMES[game_id].remove_spectator(session['sid'])
            if (len(GAMES[game_id].get_players()) == 0 and
                    len(GAMES[game_id].get_spectators()) == 0):
                del GAMES[game_id]
    else:
        for room in PLAYERS[session['sid']].get_rooms():
            if room in GAMES:
                GAMES[game_id].remove_player(session['sid'])
                GAMES[game_id].remove_spectator(session['sid'])
                if len(GAMES[game_id].get_players()) == 0:
                    del GAMES[game_id]
            PLAYERS[session['sid']].leave_room(room)
            leave_room(room)
    mark_new_update(game_id)
    return redirect('/')


@app.route('/spectate/<game_id>')
def spectate_game(game_id: str):
    check_session_config()
    if game_id and game_id in GAMES:
        # this should keep the player in the room for broadcast state, but not
        # game mechanics.
        GAMES[game_id].remove_player(session['sid'])
        GAMES[game_id].add_spectator(session['sid'])
        mark_new_update(game_id)
        return redirect(f'/game/{game_id}')
    flash(f'Unable to find game: {game_id}')
    return redirect('/')


@app.route('/game/<game_id>', strict_slashes=False)
def game_index(game_id: str, spectate: str = None):
    check_session_config()
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

    return render_template(
        'game.html.j2',
        question_html=game_state['question_html'],
        players=game_state['players'],
        game_name=game_state['game_id'],
        game_state=game_state['game_state'],
        mayor=game_state['mayor'],
        tokens=game_state['tokens'],
        player_is_mayor=game_state['player_is_mayor'],
        player_is_admin=game_state['player_is_admin'],
        role=game_state['role'],
        game_id=game_id,
        # Remove this when done poking at things. :P
        DEBUG=app.config['DEBUG'],
    )


@app.route('/get_words/<game_id>')
def get_words(game_id: str):
    check_session_config()
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
    check_session_config()
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
    check_session_config()
    return render_template('login.html')


@app.route('/logout')
def logout():
    check_session_config()
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
    # TODO: Fix username KeyError on initial connect
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
            mark_new_update(game_id)
            return True

    app.logger.error(f'Unable to add question for game {game_id}')
    return False


@socketio.on('get_questions')
def get_questions(game_id: str, question_id: int):
    if game_id in GAMES and int(question_id) < len(GAMES[game_id].questions):
        question = GAMES[game_id].questions[question_id]
        return {
            'status': 'OK',
            'question': render_template(
                'question_layout.html.j2',
                question_object=get_question_info(question, question_id),
                player_is_mayor=GAMES[game_id].mayor == session['sid'],
                game_id=game_id
            )
        }
    return {'status': 'FAILED', 'question': ''}


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
                      error,
                      room=game_id)
        return False

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
    return {'status': 'FAILED', 'game_state': ''}


# Mayor functions
@socketio.on('undo')
def undo(game_id: str):
    app.logger.debug(f'Attempting to undo something for {game_id}')
    if game_id in GAMES and GAMES[game_id].mayor == session['sid']:
        GAMES[game_id].undo_answer()
        mark_new_update(game_id)


@socketio.on('start_vote')
def start_vote(game_id: str):
    app.logger.debug('Attempting to start vote. Surely this won\'t fail.')
    if game_id in GAMES and GAMES[game_id].mayor == session['sid']:
        success = GAMES[game_id].start_vote()
   
        if not success:
            socketio.emit('mayor_error',
                          f'Unable to finish game and start vote.',
                          room=game_id)
            return
        mark_new_update(game_id)


@socketio.on('nominate_for_mayor')
def nominate_for_mayor(game_id: str):
    if game_id in GAMES and GAMES[game_id].is_player_in_game(session['sid']):
        GAMES[game_id].nominate_for_mayor(session['sid'])
        socketio.emit('user_info', f"You are running for mayor.",
                      to=SOCKET_MAP[session['sid']])


@socketio.on('set_word_choice_count')
def set_word_choice_count(game_id: str, word_count: int):
    if game_id in GAMES and GAMES[game_id].admin == session['sid']:
        GAMES[game_id].set_word_choice_count(word_count)
        mark_new_update(game_id)

    socketio.emit('admin_error',
                  f'Unable to set word count to {word_count}.',
                  room=game_id)


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
            mark_new_update(game_id)


@socketio.on('set_player_target')
def set_player_target(game_id: str, target_sid: str):
    if game_id in GAMES:
        player_role = GAMES[game_id].get_player_role(session['sid'])
        if (player_role and player_role.is_targetting_role()):
            GAMES[game_id].set_player_target(session['sid'], target_sid)
            if len(GAMES[game_id].get_players_needing_to_target()) == 0:
                mark_new_update(game_id)


@socketio.on('acknowledge_revealed_info')
def acknowledge_revealed_info(game_id: str):
    if game_id in GAMES:
        app.logger.debug(
            f'ACK attempt received for {PLAYERS[session["sid"]].name}')
        GAMES[game_id].acknowledge_revealed_info(session['sid'])
        if len(GAMES[game_id].get_players_needing_to_ack()) == 0:
            mark_new_update(game_id)


# Timer functions
@socketio.on('set_timer')
def set_timer(game_id: str, timer_seconds: int):
    if game_id in GAMES:
        GAMES[game_id].set_timer(timer_seconds)
        mark_new_update(game_id)


@socketio.on('game_start')
def start_game(game_id: str):
    if game_id in GAMES:
        try:
            GAMES[game_id].start_night_phase_word_choice()
            mark_new_update(game_id)
        except GameError as e:
            socketio.emit('user_info', f"Game start failed. {e}")


@socketio.on('game_reset')
def reset_game(game_id):
    # Implement game reset feature
    if game_id in GAMES and GAMES[game_id].admin == session['sid']:
        GAMES[game_id].reset()
        mark_new_update(game_id)
    else:
        app.logger.debug('Unable to reset game. User not admin.')


@socketio.on('get_required_voters')
def get_required_voters(game_id: str):
    if game_id in GAMES:
        GAMES[game_id].get_required_voters()
        mark_new_update(game_id)


@socketio.on('vote')
def vote(game_id, target_id):
    if target_id in PLAYERS:
        app.logger.debug(
            f"{PLAYERS[session['sid']].name} vote for "
            f"{PLAYERS[target_id].name}, game id: {game_id}")
        if game_id in GAMES:
            app.logger.debug(f'Attempting to vote for {target_id}')
            try:
                GAMES[game_id].vote(session['sid'], target_id)
            except GameError as e:
                if session['sid'] in SOCKET_MAP:
                    socketio.emit('user_info',
                                  f'Vote failed: {e}',
                                  to=SOCKET_MAP[session['sid']])
                else:
                    app.logger.error(
                        f"Error delivery to {PLAYERS[session['sid']].name} failed.")
            mark_new_update(game_id)
    else:
        app.logger.debug(f'Unknown player SID {target_id}')


@socketio.on('get_results')
def get_results(game_id: str):
    if game_id in GAMES:
        winner, killed_sids, votes = GAMES[game_id].get_results()
        role = GAMES[game_id].get_player_role(session['sid'])
        player_won = role.get_affiliation() == winner
        vote_information = []
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
                # killed_names=killed_names,
                vote_count=vote_count,
                # vote_information=vote_information,
                mayor=PLAYERS[GAMES[game_id].mayor].name,
            ),
        }
    return {'status': 'BAD', 'results_html': None}


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
        app.logger.debug(f'Info: {known_word} players: {known_players}')
        role = GAMES[game_id].get_player_role(session['sid'])
        return {
            'status': 'OK',
            'reveal_html': render_template(
                'player_reveal.html.j2',
                player_role=str(role),
                image=role.get_image_name(),
                known_players=known_players,
                known_word=known_word,
                word_is_known=known_word is not None,
                mayor=PLAYERS[GAMES[game_id].mayor].name,
                role_description=role.get_role_description().strip(),
            ),
        }
    return {'status': 'BAD', 'reveal_html': None}


@socketio.on('get_voting_page')
def get_voting_information(game_id: str):
    if (game_id in GAMES and session['sid']):
        voter_sids, votes, word_guessed, candidate_sids = GAMES[game_id].voting_info(
        )
        if not voter_sids:
            socketio.emit('mayor_error',
                          f'No voting players found for game {game_id}')
            return
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

        vote = None
        if session['sid'] in votes:
            vote = votes[session['sid']]
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
                    voters=voters,
                    vote=vote,
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
                    voters=voters,
                    vote=None,
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
    return {'status': False, 'night_action_html': None}


@socketio.on('set_word')
def set_word(game_id: str, word: str):
    """Set the chosen word for the provided game ID.

    Args:
        game_id: String game ID referencing the game.
        word: String word referencing the word to set as the chosen word for the
            game.
    """
    if game_id not in GAMES:
        socketio.emit('mayor_error', f'Unable to set word for game {game_id}.')
        return

    if session['sid'] != GAMES[game_id].mayor:
        socketio.emit('mayor_error',
                      f'Word set attempt failed. User is not mayor.')
        return

    GAMES[game_id].set_word(word)
    mark_new_update(game_id)


@socketio.on('delete_question')
def delete_question(game_id: str, question_id: int):
    if game_id in GAMES:
        q = GAMES[game_id].get_question(question_id)
        if session['sid'] == q.player_sid:
            try:
                GAMES[game_id].delete_question(question_id)
                mark_new_update(game_id)
            except GameError as e:
                socketio.emit('user_info',
                              e,
                              to=SOCKET_MAP[session['sid']])
                


if __name__ == '__main__':
    socketio.run(app)
