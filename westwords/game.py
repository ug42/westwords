# Game and player-related classes
from datetime import datetime
from .enums import GameState, AnswerToken
from .role import (Affiliation, Role, Mayor, Doppelganger, Spectator,
                   Werewolf, Villager, Seer, Apprentice)


class Game(object):
    """Game object for recording status of game.
    
    Args:
        timer: An integer starting value of timer in seconds
        player_sids: A list of strings for player session IDs
        admin: A string player session ID of the admin for the game
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
        self.token_defaults = {
            # YES and NO share the same token count
            AnswerToken.YES.name: 36,
            AnswerToken.MAYBE.name: 10,
            AnswerToken.SO_CLOSE.name: 1,
            AnswerToken.SO_FAR.name: 1,
            # Purpose is generally unknown even by lar.
            AnswerToken.LARAMIE.name: 1,
            AnswerToken.CORRECT.name: 1,
        }
        self.tokens = self.token_defaults
        self.mayor = None
        self.questions = []

    def __repr__(self):
        return f'Game({self.timer}, {self.player_sids}, {self.admin})'

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
            list of player_sids, and a list of question.Question objects.
        """
        game_status = {
            'game_state': self.game_state.name,
            'time': self.timer,
            'game_id': game_id,
        }
        return (game_status, self.questions, self.player_sids)

    def get_player_names(self, PLAYERS={}):
        return [PLAYERS[sid].name for sid in self.player_sids]

    def remove_token(self, token):
        self.tokens[token.value] -= 1