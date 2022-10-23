# Game and player-related classes
from datetime import datetime
from random import shuffle, choice

from westwords.question import QuestionError

from .enums import AnswerToken, GameState
from .role import (Apprentice, Beholder, Doppelganger, FortuneTeller, Mason,
                   Minion, Seer, Tapper, Villager, Werewolf)


ROLES = {
    'apprentice': Apprentice(),
    'beholder': Beholder(),
    'doppelganger': Doppelganger(),
    'fortuneteller': FortuneTeller(),
    'mason': Mason(),
    'minion': Minion(),
    'seer': Seer(),
    'tapper': Tapper(),
    'villager': Villager(),
    'werewolf': Werewolf(),
}


class Game(object):
    """Game object for recording status of game.

    Args:
        timer: An integer starting value of timer in seconds
        player_sids: A dict of string keys for player session IDs to Role
            objects.
        admin: A string player session ID of the admin for the game
    """

    def __init__(self, timer=300, player_sids=[]):
        # TODO: Add concept of a game admin and management of users in that space
        self.game_state = GameState.SETUP
        self.timer = timer
        self.start_time = None
        # TODO: Make this to a dict so it can contain roles
        self.player_sids = {}
        for player_sid in player_sids:
            self.player_sids[player_sid] = None
        self.spectators = []
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
        self.tokens = self.token_defaults.copy()
        self.mayor = None
        self.questions = []
        self.selected_roles = []
        self.mayor_nominees = []
        self._choose_admin()
        # This should be implemented so we can undo last action in case it was
        # done accidentally.
        self.last_answered = None

    def __repr__(self):
        return f'Game(timer={self.timer},player_sids={self.player_sids.keys()})'

    # Game state functions
    def start(self):
        """Start the game.

        Returns:
            A tuple of bool status on successful start of game and a message of
            any applicable errors.
        """
        if sum(self.selected_roles) != len(self.player_sids):
            print('Unable to start game. Role/Player count mismatch.')

            print(f'{sum(self.selected_roles)} vs {len(self.player_sids)}')
            return (False, 'Not enough selected roles!')

        # Set the player roles by shuffling the selected roles and assigning
        roles = self.selected_roles.copy()
        shuffle(roles)
        for player_sid in self.player_sids:
            self.player_sids[player_sid] = roles.pop()

        # Find the mayor from nominated mayors or all players if no nominations
        if not self.mayor_nominees:
            self.mayor_nominees = list(self.player_sids.keys())
        self.mayor = choice(self.mayor_nominees)

        self.game_state = GameState.STARTED
        return (True, None)

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
        self.tokens = self.token_defaults.copy()
        self.mayor = None
        self.questions = []
        self.last_answered = None

    def get_tokens(self):
        return ' '.join([f'{token.name}: {self.tokens[token]}'
                        for token in self.tokens])

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
            'admin': self.admin,
            'tokens': self.get_tokens(),
        }
        return (game_status, self.questions, self.player_sids)

    # Player and Role functions
    def get_player_role(self, sid):
        """Returns a string format version of the player's role."""
        return str(self.player_sids[sid])

    def _choose_admin(self):
        if self.player_sids and not admin:
            self.admin = next(iter(self.player_sids))
        if self.player_sids and self.admin not in self.player_sids:
            # Get the first key by getting "next" [read: first] key value in
            # epxlicitly interable handler for dict
            self.admin = next(iter(self.player_sids))
        else:
            self.admin = None

    def nominate_for_mayor(self, sid):
        if sid in self.player_sids and sid not in self.mayor_nominees:
            self.mayor_nominees.append(sid)
            print(f'Adding {sid} to mayor nominees')

    def add_player(self, sid):
        if sid not in self.player_sids:
            self.player_sids[sid] = None
        else:
            print(f'ADD: User {sid} already in game')

    def remove_player(self, sid):
        if sid not in self.player_sids:
            del self.player_sids[sid]
            if self.admin not in self.player_sids:
                self.admin = next(iter(self.player_sids))
        else:
            print(f'DELETE: User {sid} not in game')

    def _current_role_instances(self, role):
        """Returns the number of instances of provided role in selected roles.
        
        Args:
            A string role to lookup that matches an existing role value.

        Returns:
            An integer value of number instances.
        """
        if role in ROLES:
            return len([r for r in self.selected_roles if r == role])
        print(f'Role {role} not found.')
        return 0
    
    def _get_role_info(self, role):
        """Return a dict of information on a given role.
        
        Args:
            A string role to lookup that matches an existing role value.
            
        Returns:
            A dict of an integer required_players, bool is_required, integer
            max_instances, and integer current_instances, if role found. Empty
            dict otherwise.
        """
        try:
            role = role.lower()
            role_info = {
                'required_players': ROLES[role].get_required_players(),
                'is_required': ROLES[role].is_required(),
                'max_instances': ROLES[role].get_max_instances(),
                'current_instances': self._current_role_instances(role),
            }
            return role_info
        except KeyError as e:
            print(f'Unable to find role: {role}')
            return {}


    def add_role(self, role):
        """Add the selected role to game.

        Args:
            role: a string role name to be added.

        Returns:
            True if role is known and able to be added; False otherwise.
        """
        if self.game_state.name != GameState.SETUP:
            return False

        role = role.lower()
        role_info = self._get_role_info(role)
        if not role_info:
            return False
        if role_info['current_instances'] >= role_info['max_instances']:
            print(f'Unable to add {role}: too many of that role.')
            return False
        if len(self.player_sids) < role['required_players']:
            print(f'Unable to add {role}: too few players.')
        
        # Fall through to success against my better judgement.
        self.selected_roles.append(role)
        return True
    
    def remove_role(self, role):
        """Remove the provided role from the game.
        
        Args:
            role: a string role name to be removed.
        
        Returns:
            True if able to remove role, False otherwise.
        """
        if self.game_state.name != GameState.SETUP:
            return False

        role = role.lower()
        role_info = self._get_role_info(role)
        if not role_info:
            return False
        if role['is_required'] and role_info['current_instances'] == 1:
            print(f'Unable to remove {role} as it is required.')
            return False
        if role['current_instances'] < 1:
            print(f'Unable to remove role {role} as it is not selected.')
            return False
        
        for i in range(len(self.selected_roles)):
            if self.selected_roles[i] == role:
                removed_role = self.selected_roles[i].pop()
                print(f'Removed role: {removed_role}')
                return True
        
        # In case I missed something :)
        return False

    def get_selected_roles(self):
        """Gets the list of roles that are currently selected.

        Returns:
            A list of strings representing each role's name in the amount of """
        return sorted(self.selected_roles)

    def get_possible_roles(self):
        """Get all possible roles for this game.

        Returns a list of strings enumerating each possible role invocation.
        """
        roles = []
        for role in ROLES:
            for _ in range(role.get_max_instances()):
                roles.append(role)
        return roles

    # Question functions
    def answer_question(self, question_id: int, answer: AnswerToken):
        self.questions[question_id].answer_question(answer)
        self.last_answered = question_id

    def undo_answer(self):
        try:
            if self.last_answered is not None and self.last_answered < len(self.questions):
                print(f'Undoing answer for question id {self.last_answered}')
                token = self.questions[self.last_answered].clear_answer()
                self._add_token(token)
                self.last_answered = None
                return
        except (TypeError, KeyError) as e:
            print(f'Encountered error: {e}')
        print(f'No answer to undo for question id: {self.last_answered}')

    def _add_token(self, token: AnswerToken):
        self.tokens[token] += 1

    def remove_token(self, token: AnswerToken):
        """Decrement the token counter

        Args:
            token: An AnswerToken object for the token to decrement.

        Returns:
            A dict of booleans for 'success' on removal of token from pool, and
            'end_of_game' to denote if it was the last token to play.
        """
        if self.tokens[token] > 0:
            if token in [AnswerToken.NO, AnswerToken.YES]:
                self.tokens[AnswerToken.NO] -= 1
                self.tokens[AnswerToken.YES] -= 1
                if self.tokens[token] < 1:
                    return {'success': True, 'end_of_game': True}
            else:
                self.tokens[token] -= 1
                if token == AnswerToken.CORRECT:
                    return {'success': True, 'end_of_game': True}
            return {'success': True, 'end_of_game': False}

        return {'success': False, 'end_of_game': False}
