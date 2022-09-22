from datetime import datetime
import enum
from telnetlib import GA
from flask import Flask, render_template, request, jsonify, make_response
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['DEBUG'] = True
socketio = SocketIO(app)


class GameState(enum.Enum):
    SETUP = 1
    STARTED = 2
    PAUSED = 3
    VOTING = 4
    FINISHED = 5


class Game(object):
    """Simple game object for recording status of game."""

    def __init__(self, timer=300, players=[]):
        # TODO: Add concept of a game admin and management of users in that space
        self.game_state = GameState.SETUP
        self.timer = timer
        self.time_start = None
        # TODO: Plumb in user objects to this
        self.admin = 'all'
        # TODO: Make this to a dict so it can contain roles
        self.players = players

    def start(self):
        self.game_state = GameState.STARTED

    def pause(self):
        self.game_state = GameState.PAUSED

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
            'players': self.players,
            'time': self.timer,
        }
        if app.config['DEBUG'] == True:
            print(game_status)
        return game_status

    def set_state(self, json):
        # TODO: parse and set the game state based on this.
        # Could be used for future updates to write out to data store
        pass


Games = {
    'defaultgame': Game(),
}


@app.route('/')
def game():
    return render_template('game.html')


@socketio.on('connect')
def connect(auth):
    emit('my response', {'data': 'Connected'})
    print('Client connected')
    if auth:
        print('Auth details: ' + str(auth))


@socketio.on('disconnect')
def disconnect():
    print('Client disconnected')


@socketio.on('question')
def question(json):
    print('got a question: ' + str(json))
    emit('mayor question', json, broadcast=True)

# Add a jquery function that will return tableData as a JSON of the game state
# for each connected user. Ideally with some logic to find the mayor, werewolfs,
# seer, etc.
# Supposedly we can then add this to js?
# See https://stackoverflow.com/questions/61458593/how-to-pass-data-from-flask-to-javascript
# $.getJSON(url_of_flask_script, function(tableData) {
#     table.setData(tableData)
#     .then(function(){
#         //run code after table has been successfuly updated
#     })
#     .catch(function(error){
#         //handle error loading data
#     });
# });


@socketio.on('create_game')
def create_game():
    # Guaranteed to be random blah blah blah. Update this later.
    game_id = 4
    # encapsulate this in a JSON, maybe convert dict to JSON?
    emit('room_data', 'blah')


@socketio.on('update_game')
def update_game(game_updates, game_id):
    if (game_id in Games) and Games[game_id].admin == 'all':
        Games[game_id].update_state_json(game_updates)

@socketio.on('get_game_state')
def game_status(game_id):
    socketio.emit('game_state', Games[game_id].get_state())

@socketio.on('game_start')
def start_game(game_id):
    Games[game_id].start()

@socketio.on('game_pause')
def start_game(game_id):
    Games[game_id].pause()

@socketio.on('game_reset')
def start_game(game_id):
    Games[game_id].reset()


if __name__ == '__main__':
    socketio.run(app)
