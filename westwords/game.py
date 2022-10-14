# Game and player-related classes
from datetime import datetime

from westwords.question import QuestionError
from .enums import GameState, AnswerToken
from .role import (Affiliation, Role, Mayor, Doppelganger, Spectator, Mason,
                   Werewolf, Villager, Seer, FortuneTeller, Apprentice, Thing,
                   Beholder, Minion)


class Game(object):
    """Game object for recording status of game.

    Args:
        timer: An integer starting value of timer in seconds
        player_sids: A dict of string keys for player session IDs to Role
            objects.
        admin: A string player session ID of the admin for the game
    """

    def __init__(self, timer=300, player_sids=[], admin=None):
        # TODO: Add concept of a game admin and management of users in that space
        self.game_state = GameState.SETUP
        self.timer = timer
        self.start_time = None
        # TODO: Plumb in user objects to this
        self.admin = admin
        # TODO: Make this to a dict so it can contain roles
        self.player_sids = {}
        for player_sid in player_sids:
            self.player_sids[player_sid] = None
        # TODO: Move this to use the AnswerToken Enum and update remove_token()
        self.token_defaults = {
            # YES and NO share the same token count
            AnswerToken.YES: 36,
            AnswerToken.NO: 36,
            AnswerToken.MAYBE: 10,
            AnswerToken.SO_CLOSE: 1,
            AnswerToken.SO_FAR: 1,
            # Purpose is generally unknown even by lar.
            AnswerToken.LARAMIE: 1,
            AnswerToken.CORRECT: 1,
        }
        self.tokens = self.token_defaults
        self.mayor = None
        self.questions = []
        # This should be implemented so we can undo last action in case it was
        # done accidentally.
        self.last_answered = None

    def __repr__(self):
        return f'Game({self.timer}, {self.player_sids.keys()}, {self.admin})'

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
        self.game_state = GameState.SETUP
        self.tokens = self.token_defaults
        self.mayor = None
        self.questions = []
        self.last_answered = None

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
            'mayor': self.mayor,
            'tokens': {i.name: self.tokens[i] for i in self.tokens},
        }
        return (game_status, self.questions, self.player_sids)

    def get_player_role(self, sid):
        """Returns a string format version of the player's role."""
        return str(self.player_sids[sid])

    def add_player(self, sid):
        if sid not in self.player_sids:
            self.player_sids[sid] = None
        else:
            print(f'ADD: User {sid} already in game')

    def remove_player(self, sid):
        if sid not in self.player_sids:
            del self.player_sids[sid]
        else:
            print(f'DELETE: User {sid} not in game')

    def get_player_names(self, PLAYERS={}):
        return [PLAYERS[sid].name for sid in self.player_sids.keys()]

    def answer_question(self, question_id: int, answer: AnswerToken):
        self.questions[question_id].answer_question(answer)
        self.last_answered = question_id

    def undo_answer(self):
        if self.last_answered and self.last_answered < len(self.questions):
            self.questions[self.last_answered].clear_answer()
        else:
            print(f'No answer to undo for question id: {self.last_answered}')

    def remove_token(self, token: AnswerToken):
        """Decrement the token counter

        Args:
            token: An AnswerToken object for the token to decrement.

        Returns:
            A dict of booleans for 'success' on removal of token from pool, and
            'end_of_game' to denote if it was the last token to play.
        """
        print(f'tokens before: {self.tokens}')

        if self.tokens[token] > 0:
            if token in [AnswerToken.NO, AnswerToken.YES]:
                self.tokens[AnswerToken.NO] -= 1
                self.tokens[AnswerToken.YES] -= 1
                if self.tokens[token] < 1:
                    return {'success': True, 'end_of_game': True}    
            else:
                self.tokens[token] -= 1
            return {'success': True, 'end_of_game': False}

        return {'success': False, 'end_of_game': False}
