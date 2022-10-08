# Game and player-related classes
from enum import Enum
from datetime import datetime


class GameState(Enum):
    SETUP = 1
    STARTED = 2
    PAUSED = 3
    VOTING = 4
    FINISHED = 5


class AnswerToken(Enum):
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
        # TODO: change this to use the AnswerToken enum
        self.answer = ''

    def __repr__(self):
        return f'Question({self.player_sid}, {self.question_text})'

    # def __str__(self):
    #     return f'{PLAYERS[self.player_sid].name}: {self.question_text} ({self.answer})'

    # def get_player_name(self, PLAYERS={}):
    #     return PLAYERS[self.player_sid].name

    def html_format(self):
        # id and player name are held outside this scope.
        return ('<div class="question"'
                'id="q{id}">'
                '{player_name}'
                f': {self.question_text}'
                '<div id="q{id}a" style="display: inline">'
                f'  ({self.answer})</div></div>')

    def get_question(self, PLAYERS={}):
        return [PLAYERS[self.player_sid].name, self.question_text, self.answer]


class Game(object):
    """Simple game object for recording status of game.
        12 roles
        36 Yes/No tokens
        10 Maybe tokens
        1 So Close token
        1 Correct token
    """

    def __init__(self, timer=300, player_sids=[], admin=None):
        # TODO: Add concept of a game admin and management of users in that space
        self.game_state = GameState.SETUP
        self.timer = timer
        self.time = datetime.now()
        # TODO: Plumb in user objects to this
        self.admin = admin
        # TODO: Make this to a dict so it can contain roles
        self.player_sids = player_sids
        # TODO: Move this to use the AnswerToken Enum and update remove_token()
        self.tokens = {
            'yes_no': 36,
            'maybe': 10,
            'so_close': 1,
            'so_far': 1,
            # Purpose is generally unknown even by lar.
            'laramie': 1,
            'correct': 1,
        }
        # TODO: Make the reset function reset the token count or make the Enum
        # value associated with AnswerToken count up to limits rather than
        # counting down in tokens
        self.mayor = None
        self.questions = []

    def __repr__(self):
        return f'Game({self.timer}, {self.player_sids})'

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

    def get_state(self, game_id):
        """Returns a dict of the current game state.

        Args:
            game_id: A string representing the associated game to include.

        Returns:
            A tuple with a a dict representing the current GameState enum name
            value, the current timer as seen from the Game, and the game id, 
            list of player_sids, and a list of Question objects.
        """
        game_status = {
            'game_state': self.game_state.name,
            # 'players': self.player_sids,
            'time': self.timer,
            # 'questions': self.questions,
            'game_id': game_id,
        }
        # DEBUG statements
        print(datetime.now())
        print(f'DEBUG ENABLED! Current game state: {game_status} {self.player_sids}')
        return (game_status, self.questions, self.player_sids)

    # def get_questions(self):
    #     return [self.questions.html_format().format() for id in range(len(self.questions))]

    def get_player_names(self, PLAYERS={}):
        return [PLAYERS[sid].name for sid in self.player_sids]

    def remove_token(self, token):
        self.tokens[token.value] -= 1


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