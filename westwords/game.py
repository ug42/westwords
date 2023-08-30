# Game and player-related classes
import logging
import math
import time
from collections import UserDict, UserList
from copy import deepcopy
from datetime import datetime, timedelta
from random import choice, choices, shuffle
from typing import Any

from westwords.enums import AnswerToken
from westwords.question import Question, QuestionError
from westwords.role import Role

from .enums import Affiliation, AnswerToken, GameState
from .role import (DEFAULT_ROLES_BY_PLAYER_COUNT, Beholder, Doppelganger,
                   Esper, FortuneTeller, Intern, Mason, Minion, Seer, Villager,
                   Werewolf)
from .wordlists import WORDLISTS

logging.basicConfig(level=logging.DEBUG)


class RoleDict(UserDict):
    def __getitem__(self, key: Any) -> Role:
        return super().__getitem__(key)


ROLES = RoleDict({
    'intern': Intern(),
    'beholder': Beholder(),
    'doppelganger': Doppelganger(),
    'fortuneteller': FortuneTeller(),
    'mason': Mason(),
    'minion': Minion(),
    'seer': Seer(),
    'esper': Esper(),
    'villager': Villager(),
    'werewolf': Werewolf(),
})


def logging_func(e: str):
    print(e)


class GameError(Exception):

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class Game(object):
    """Game object for recording status of game.

    Args:
        timer: An integer starting value of timer in seconds
        player_sids: A dict of string keys for player session IDs to Role
            objects.
        admin: A string player session ID of the admin for the game
    """

    def __init__(self, timer=10, player_sids=[]):
        self.timer = timer
        self.vote_timer = 60
        self.end_vote_timestamp_ms = 0
        self.update_timestamp = int(time.time() * 1000)
        self.player_sids = RoleDict()
        for player_sid in player_sids:
            self.player_sids[player_sid] = None
        self.spectators = []
        self.word_choice_count = 5
        self.word_difficulty = 'medium'
        self.token_defaults = {
            # YES and NO share the same token count
            AnswerToken.YES: 36,
            AnswerToken.NO: 36,
            AnswerToken.MAYBE: 10,
            AnswerToken.SO_CLOSE: 1,
            AnswerToken.SO_FAR: 1,
            # Custom-built for anyone to contribute meaning.
            AnswerToken.LARAMIE: 1,
            AnswerToken.BRONEY: 1,
            # AnswerToken.MICHAEL: 1,
            # AnswerToken.MATT: 1,
            # AnswerToken.JOHANNA: 1,
            AnswerToken.CORRECT: 1,
        }
        self.reset()

    def __repr__(self):
        return f'Game(timer={self.timer},player_sids={list(self.player_sids.keys())})'

    @property
    def tokens(self) -> dict[AnswerToken, int]:
        return self._tokens

    # Game state functions
    def start_night_phase_word_choice(self):
        """Start the night phase of game.

        Returns:
            True if successful; False otherwise.
        """
        if self.game_state != GameState.SETUP:
            logging_func(f'Game not in SETUP state: {self.game_state}')
            return False
        # TODO: Remove this in favor of choosing roles
        try:
            if not self.selected_roles:
                self.selected_roles = deepcopy(DEFAULT_ROLES_BY_PLAYER_COUNT[
                    str(len(self.player_sids))])
        except KeyError:
            raise GameError('No role configuration available for '
                            f'{len(self.player_sids)} players')
        if len(self.selected_roles) != len(self.player_sids):
            raise GameError(
                'Unable to start game. Role/Player count mismatch: '
                f'{sum(self.selected_roles)} vs {len(self.player_sids)}')

        # Set the player roles by shuffling the selected roles and assigning
        roles = deepcopy(self.selected_roles)
        shuffle(roles)
        for player_sid in self.player_sids:
            self.player_sids[player_sid] = roles.pop()

        # Find the mayor from nominated mayors or all players if no nominations
        if not self.mayor_nominees:
            self.mayor_nominees = list(self.player_sids.keys())
        self.mayor = choice(self.mayor_nominees)

        self.game_state = GameState.NIGHT_PHASE_WORD_CHOICE
        return True

    def _start_night_phase_targetting(self):
        if (self.game_state in [
            GameState.NIGHT_PHASE_WORD_CHOICE,
            GameState.NIGHT_PHASE_DOPPELGANGER,
        ] and self.word is not None):
            self.night_actions_required = [
                p for p in self.player_sids if self.player_sids[p].targetting_role]
            self.game_state = GameState.NIGHT_PHASE_TARGETTING
            if not self.night_actions_required:
                self._start_night_phase_reveal()
                return True
        return False

    def _start_night_phase_reveal(self):
        if (self.game_state == GameState.NIGHT_PHASE_TARGETTING and
                not self.night_actions_required):
            self.reveal_ack_required = list(self.player_sids)
            self.game_state = GameState.NIGHT_PHASE_REVEAL
            return True
        return False

    def get_player_revealed_information(self, player_sid, acknowledge=False):
        """Return information known by the provided player SID.

        Args:
            player_sid: A string player SID for which to retrieve known
                information.

        Returns:
            A dict of known information about each player
        """
        # If the player SID is in the list and has a role assigned.
        if player_sid in self.player_sids and self.player_sids[player_sid]:

            if acknowledge:
                self.acknowledge_revealed_info(player_sid)

            return self.player_sids[player_sid].get_night_action_info(
                player_sid, self.player_sids, self.mayor, self.word)

        return (None, None)

    def acknowledge_revealed_info(self, player_sid):
        """Acknoledge that player has seen the revealed information.

        Args:
            player_sid: A string player SID for which to acknowledge the info.

        Returns:
            True if successfully acknowledged; False otherwise."""
        if self.game_state != GameState.NIGHT_PHASE_REVEAL:
            return False
        if player_sid in self.reveal_ack_required:
            self.reveal_ack_required.remove(player_sid)
            if not self.reveal_ack_required:
                # No more acks needed
                self._start_day_phase()
            return True
        return False

    def voting_info(self):
        """Returns voting options.

        Returns:
            A list of str player SIDs that are required to vote, a dict of str
            player SIDs that have voted and the str target player SID for whom
            they voted, a bool whether word was guessed, and a list of possible
            targets."""
        if self.game_state == GameState.VOTING:
            if self.word_guessed:
                candidates = [p for p in self.player_sids
                              if str(self.player_sids[p]) != str(Werewolf)]
            else:
                candidates = self.player_sids
            return (self.required_voters, self.votes, self.word_guessed,
                    candidates)
        return None, None, None, None

    def set_player_target(self, player_sid, target_sid):
        """Set the target of player's night action.

        Args:
            player_sid: String player SID that is doing the targetting.
            target_sid: String player SID of the targetted player.

        Returns:
            True if successful set; False otherwise."""
        if (self.is_night_action_phase() and
            player_sid in self.night_actions_required and
                target_sid in self.player_sids):
            if str(self.player_sids[player_sid]) == 'Doppelganger':
                return self.set_doppelganger_target(player_sid, target_sid)

            if self.player_sids[player_sid].target_player(
                    player_sid, target_sid, self.player_sids):
                if player_sid in self.night_actions_required:
                    self.night_actions_required.remove(player_sid)
                if not self.night_actions_required:
                    # All night actions are completed.
                    self._start_night_phase_reveal()
                return True

        return False

    def get_players_needing_to_target(self):
        return self.night_actions_required
    
    def get_players_needing_to_ack(self):
        """Returns a list of player SIDs needing to ack the reveal info."""
        if self.game_state != GameState.NIGHT_PHASE_REVEAL:
            return []
        return self.reveal_ack_required

    def get_players_needing_to_vote(self) -> list[str]:
        if self.game_state != GameState.VOTING:
            return []
        return list(set(self.required_voters) - set(self.votes))

    def get_required_voters(self) -> list[str]:
        if self.game_state != GameState.VOTING:
            return []
        return self.required_voters

    def get_players(self) -> RoleDict:
        return self.player_sids

    def get_spectators(self):
        return [s for s in self.spectators if s not in self.player_sids]
    
    def get_mayor_nominees(self):
        return self.mayor_nominees

    def get_player_token_count(self, player_sid):
        if player_sid in self.player_token_count:
            return self.player_token_count[player_sid]
        return {token: 0 for token in AnswerToken}

    def _start_day_phase(self):
        """Start the question-asking phase of game.

        Returns:
            A tuple of bool status on successful start of game and a message of
            any applicable errors.
        """
        self.game_state = GameState.DAY_PHASE_QUESTIONS
        self.start_time = datetime.now()

    def reset(self):
        self.admin = self._get_next_admin()
        self.game_state = GameState.SETUP
        self.killed_players = []
        self.last_answered = None
        self.mayor = None
        self.mayor_nominees = []
        self.night_actions_required = []
        self.player_token_count = {}
        self.reveal_ack_required = []
        self.questions = []
        self.required_voters = []
        self.selected_roles = []
        self.start_time = None
        self._tokens = {}
        for token in AnswerToken:
            self._tokens[token] = token.default_count
        self.vote_count = []
        self.votes = {}
        self.winner = None
        self.word = None
        self.word_choices = []
        self.word_guessed = False
        for player_sid in self.player_sids:
            self.player_sids[player_sid] = None

    def start_vote(self) -> bool:
        """Start the voting process.

        Returns:
            True if voting state successfully; False otherwise.
        """
        self.word_guessed = self._tokens[AnswerToken.CORRECT] < 1
        self.out_of_tokens = (self._tokens[AnswerToken.YES] <= 0 or
                              self._tokens[AnswerToken.NO] <= 0)
        if self.is_started():
            if self.start_time:
                # TODO: Remove the extra 2 second buffer after time skew is done.
                if self.timer <= (datetime.now() - self.start_time).seconds + 2:
                    self.game_state = GameState.VOTING
            if (self.out_of_tokens or self.word_guessed):
                self.game_state = GameState.VOTING
                

        if self.game_state != GameState.VOTING:
            logging_func(
                'End of game conditions not met.\n'
                f'Word guessed: {self.word_guessed}\n'
                f'Elapsed sec: {(datetime.now() - self.start_time).seconds}'
                f'Reqd sec: {self.timer}')
            return False

        if self.word_guessed:
            for player_sid in self.player_sids:
                if self.player_sids[player_sid].votes_on_guessed_word:
                    if player_sid not in self.required_voters:
                        self.required_voters.append(player_sid)
        else:
            # Drop all player_sids into required voters since everyone can vote
            # including Werewolfs and Minions during this state.
            self.required_voters = list(self.player_sids)
        
        # Set the voting end time stamp.
        self.end_vote_timestamp_ms = int(time.time() + self.vote_timer) * 1e3

        return True

    def finish_game(self) -> bool:
        if self.game_state == GameState.VOTING:
            self._tally_results()
            self.game_state = GameState.FINISHED
            return True
        return False

    def is_started(self) -> bool:
        return self.game_state == GameState.DAY_PHASE_QUESTIONS

    def is_voting(self) -> bool:
        return self.game_state == GameState.VOTING
    
    def is_finished(self) -> bool:
        return self.game_state == GameState.FINISHED

    def is_night_action_phase(self) -> bool:
        return self.game_state in [
            GameState.NIGHT_PHASE_DOPPELGANGER,
            GameState.NIGHT_PHASE_TARGETTING,
        ]

    def get_words(self):
        """Returns list of word choices if in word choice phase."""
        if self.game_state == GameState.NIGHT_PHASE_WORD_CHOICE:
            if not self.word_choices:
                all_words = []
                for word_list in WORDLISTS:
                    # TODO: Add ability to select word difficulties
                    # words = WORDLISTS[word_list].get_all_words(level=self.word_difficulty)
                    words = WORDLISTS[word_list].get_all_words()
                    all_words += words
                self.word_choices = choices(
                    all_words, k=self.word_choice_count)
            return self.word_choices
        return None

    def set_word_choice_count(self, count: int) -> bool:
        """Set the number of word choices a mayor will receive.

        Args:
            count: An integer between 0 and 42 for number of word choices.

        Returns:
            True if successfully set; False otherwise.
        """
        if self.game_state == GameState.SETUP:
            if count > 0 and count < 42:
                self.word_choice_count = count
                return True
        return False

    def set_word(self, word: str) -> bool:
        """Sets the word to the selected choice and starts the targetting phase.

        Args:
            word: String word to set as the selected word.

        Returns:
            True if set successfully; False otherwise.
        """
        if self.game_state == GameState.NIGHT_PHASE_WORD_CHOICE:
            if word not in self.word_choices:
                logging_func(
                    f'Unable to set {word}. Word not in: {self.word_choices}')
                return False
            self.word = word
            self._start_night_phase_doppelganger()
            return True
        return False

    def get_word(self) -> str:
        if self.game_state in [GameState.SETUP,
                               GameState.NIGHT_PHASE_WORD_CHOICE]:
            raise GameError('No word chosen yet.')
        return self.word

    def _start_night_phase_doppelganger(self):
        doppelganger_players = [
            p for p in self.player_sids if isinstance(self.player_sids[p],
                                                      Doppelganger)
        ]
        if doppelganger_players:
            self.night_actions_required += doppelganger_players
            self.game_state = GameState.NIGHT_PHASE_DOPPELGANGER
        else:
            self._start_night_phase_targetting()

    def set_doppelganger_target(self, player_sid: str, target_sid: str):
        """Attempts to set Doppelganger role target.

        Args:
            player_sid: String player SID for the Doppelganger.
            target_sid: String player SID of target whose role to copy.

        Returns:
            True if successfully set; False otherwise.
        """
        if (target_sid in self.player_sids and
                isinstance(self.player_sids[player_sid], Doppelganger)):

            s = self.player_sids[player_sid]
            t = self.player_sids[target_sid]
            self.player_sids[player_sid] = deepcopy(
                self.player_sids[target_sid])
            self.player_sids[player_sid].doppelganger = True
            self.player_sids[player_sid].add_known_role(
                target_sid, str(self.player_sids[target_sid]))
            if player_sid in self.night_actions_required:
                self.night_actions_required.remove(player_sid)
            if not self.night_actions_required:
                # No more doppelganger or copy roles.
                self._start_night_phase_targetting()
            return True
        return False

    def _tally_results(self):
        self.game_state = GameState.FINISHED
        vote_count = {}
        for voter in self.votes:
            target = self.votes[voter]
            if target not in vote_count:
                vote_count[target] = 0
            vote_count[target] += 1

        if self.word_guessed:
            self.winner = Affiliation.VILLAGE
            # All werewolf votes count to kill someone.
            for player_sid in vote_count:
                if player_sid not in self.killed_players:
                    self.killed_players.append(player_sid)
                role = self.player_sids[player_sid]
                if (vote_count[player_sid] > 0 and
                    role.team_loses_if_killed and
                        role.affiliation == Affiliation.VILLAGE):
                    self.winner = Affiliation.WEREWOLF
            return True
        else:
            # Outputs sorted list of highest voted player
            voted_player_sids_sorted = sorted(
                vote_count,
                reverse=True,
                key=lambda x: vote_count[x])
            self.killed_players = [voted_player_sids_sorted[0]]
            for player_sid in vote_count:
                if vote_count[player_sid] >= vote_count[self.killed_players[0]]:
                    if player_sid not in self.killed_players:
                        self.killed_players.append(player_sid)

            self.winner = Affiliation.WEREWOLF
            # Explicitly check if the most voted player has one vote. If so,
            # then all players have one vote and werewolfs win.
            if vote_count[voted_player_sids_sorted[0]] == 1:
                return True
            for player_sid in self.killed_players:
                role = self.player_sids[player_sid]
                if (role.team_loses_if_killed and
                        role.affiliation == Affiliation.WEREWOLF):
                    self.winner = Affiliation.VILLAGE
            return True

    def get_results(self) -> (Affiliation, list[str], dict[str, str]):
        """Get results of a game after all voting has completed.

        Returns:
            A tuple Affilition enum for winner, list of str killed player sids,
            and a dict of votes for each player.
        """
        if self.game_state != GameState.FINISHED:
            logging_func(f'Game not finished, no results to give.')
            return None
        return (self.winner, self.killed_players, self.votes)

    def set_timer(self, time_in_seconds) -> None:
        """Set the timer amount in seconds.

        Args:
            time_in_seconds: Integer time. in. seconds.
        """
        if time_in_seconds > 0:
            logging_func(f'Setting time to {time_in_seconds}')
            self.timer = time_in_seconds

    def set_vote_timer(self, time_in_seconds) -> None:
        """Set the vote timer amount in seconds.

        Args:
            time_in_seconds: Integer time. in. seconds.
        """
        if time_in_seconds > 0:
            logging_func(f'Setting time to {time_in_seconds}')
            self.vote_timer = time_in_seconds


    def vote(self, voter_sid: str, target_sid: str) -> bool:
        """Votes for player identified by session ID.

        Args:
            voter_sid: SID for the player voting.
            target_sid: SID of the targer player for which the player is voting.

        Returns:
            True if vote was successfully cast; False otherwise.
        """
        if not self.is_voting():
            raise GameError(f'Game not in voting state.')
        if voter_sid not in self.required_voters:
            raise GameError(f'Player {PLAYERS[voter_sid].name} is '
                            'ineligible to vote.')
        if target_sid not in self.player_sids:
            raise GameError('Unable to vote for player '
                            f'{PLAYERS[target_sid].name}; Not found in game.')
        if target_sid == voter_sid:
            raise GameError('You can\'t vote for yourself. :P')

        self.votes[voter_sid] = target_sid
        if set(self.votes) == set(self.required_voters):
            self.finish_game()
        return True

    def get_state(self, game_id: str) -> dict[str, Any]:
        """Returns a dict of the current game state.

        Args:
            game_id: A string representing the associated game to include.

        Returns:
            A dict representing the current GameState enum name value, the
            current timer as seen from the Game, an int forexpected end of game
            epoch timestamp in ms, str game id.
        """

        end_timestamp_ms = 0
        remaining_time_ms = 0
        remaining_vote_time_ms = 0
        if self.start_time:
            end_time = self.start_time + timedelta(seconds=self.timer)
            end_timestamp_ms = int(time.mktime(end_time.timetuple()) * 1e3)
            if not self.is_voting():
                remaining_time_ms = end_timestamp_ms - int(time.time() * 1e3)
            else:
                remaining_vote_time_ms = (self.end_vote_timestamp_ms -
                                          int(time.time() * 1e3))

        game_status = {
            'game_state': self.game_state.name,
            'timer': self.timer,
            'end_timestamp_ms': end_timestamp_ms,
            'remaining_time_ms': remaining_time_ms,
            'remaining_vote_time_ms': remaining_vote_time_ms,
            'end_vote_timestamp_ms': self.end_vote_timestamp_ms,
            'game_id': game_id,
            'mayor': self.mayor,
            'admin': self.admin,
        }
        return game_status

    # Player and Role functions
    def get_player_role(self, sid: str) -> Role:
        """Returns a Role object for the player."""
        if sid in self.player_sids and self.player_sids[sid]:
            return self.player_sids[sid]
        return None

    def _get_next_admin(self):
        try:
            return next(iter(self.player_sids))
        except StopIteration:
            pass
        return None

    def nominate_for_mayor(self, sid: str):
        if sid in self.player_sids and sid not in self.mayor_nominees:
            self.mayor_nominees.append(sid)
            logging_func(f'Adding {sid} to mayor nominees')

    def add_player(self, sid: str):
        """Add player to game.

        Returns:
            True if successful; False otherwise.
        """
        if self.game_state != GameState.SETUP:
            logging_func(
                f'Player unable to join. Game in progress. Spectating.')
            self.add_spectator(sid)
            return False
        if sid not in self.player_sids:
            self.player_sids[sid] = None
            if sid in self.spectators:
                self.spectators.remove(sid)
            if not self.admin:
                self.admin = self._get_next_admin()
            return True
        else:
            logging_func(f'ADD: User {sid} already in game')
            return False

    def add_spectator(self, sid: str) -> bool:
        """Add spectator to game.

        Returns:
            True if successful; False otherwise.
        """
        if sid not in self.spectators:
            self.spectators.append(sid)
            return True
        else:
            logging_func(f'User {sid} already spectating game.')
            return False

    def remove_player(self, sid: str) -> None:
        if sid in self.player_sids:
            del self.player_sids[sid]
            if self.admin not in self.player_sids:
                self.admin = self._get_next_admin()
        else:
            logging_func(f'DELETE: User {sid} not in game')

    def remove_spectator(self, sid: str) -> None:
        if sid in self.spectators:
            self.spectators.remove(sid)
        else:
            logging_func(f'DELETE: User {sid} not spectating game')

    def is_player_in_game(self, sid: str) -> bool:
        logging_func(f'Attempting to verify player {sid}')
        return sid in self.player_sids

    def _current_role_instances(self, role: str) -> int:
        """Returns the number of instances of provided role in selected roles.

        Args:
            A string role to lookup that matches an existing role value.

        Returns:
            An integer value of number instances.
        """
        return len([
            r for r in self.selected_roles if str(r) == role.capitalize()])

    def add_role(self, role: Role):
        """Add the selected role to game.

        Args:
            role: An object inheriting the westwords.Role object.

        Returns:
            True if role is known and able to be added; False otherwise.
        """
        if self.game_state.name != GameState.SETUP:
            return False

        if self._current_role_instances(role) >= role.get_max_instances():
            logging_func(f'Unable to add {role}: too many of that role.')
            return False
        if len(self.player_sids) < role.get_required_players():
            logging_func(f'Unable to add {role}: too few players.')
            return False

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

        if role.is_required() and self._current_role_instances(role) == 1:
            logging_func(f'Unable to remove {role} as it is required.')
            return False
        if self._current_role_instances(role) < 1:
            logging_func(
                f'Unable to remove role {role} as it is not selected.')
            return False

        for i in range(len(self.selected_roles)):
            if self.selected_roles[i] == role:
                removed_role = self.selected_roles[i].pop()
                logging_func(f'Removed role: {removed_role}')
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
            if ROLES[role].get_required_players() <= len(self.player_sids):
                for _ in range(ROLES[role].get_max_instances()):
                    roles.append(deepcopy(ROLES[role]))
        return roles

    # Question functions
    def add_question(self, sid, question_text):
        """Add a question to the game.

        Args:
            sid: A string player session id of the question asker.
            question_text: String question text.

        Returns:
            A tuple of success boolean and the int id of the added question, if
            the question was added successfuly; (False, None) otherwise.

        Raises:
            GameError if question is not able to be asked due to game
            conditions.
        """
        if not self.is_player_in_game(sid):
            raise GameError('Player is not listed in the game.')
        if sid == self.mayor:
            raise GameError('Player is the Mayor and unable to ask questions.')
        if not self.is_started():
            raise GameError('Game is not yet started.')

        question = Question(sid, question_text)
        question_id = self._get_next_question_id()
        self.questions.append(question)
        return (True, question_id)

    def delete_question(self, question_id):
        q = self.get_question(question_id)
        if q.get_answer():
            raise GameError('Unable to delete question; already answered.')
        q.mark_deleted()

    def get_question(self, id) -> Question:
        """Returns the Question object for the specified ID.

        Args:
            id: Integer ID for the question to retrieve.

        Returns:
            A Question object for the specified ID, if found; None otherwise.
        """
        try:
            return self.questions[id]
        except KeyError:
            return None

    def get_questions(self) -> list[Question]:
        return self.questions

    def _get_next_question_id(self):
        return len(self.questions)

    def answer_question(self, question_id: int, answer: AnswerToken):
        """Answer a question for the given id.

        Args:
            question_id: An integer id for the question to answer.
            answer: An AnswerToken answer for the given question.

        Returns:
            Str error, if present, or None otherwise.
        """
        if question_id < len(self.questions):
            if self.questions[question_id].get_answer():
                return 'Question is already answered.'

            success = self._remove_token(answer)
            if not success:
                return f"Out of {answer.name} tokens"

            asking_player_sid = self.questions[question_id].player_sid
            self.questions[question_id].answer_question(answer)
            self.last_answered = question_id
            if asking_player_sid not in self.player_token_count:
                self.player_token_count[asking_player_sid] = {
                    AnswerToken.YES: 0,
                    AnswerToken.NO: 0,
                    AnswerToken.MAYBE: 0,
                    AnswerToken.SO_CLOSE: 0,
                    AnswerToken.SO_FAR: 0,
                    AnswerToken.LARAMIE: 0,
                    AnswerToken.BRONEY: 0,
                    AnswerToken.CORRECT: 0,
                }
            self.player_token_count[asking_player_sid][answer] += 1
            if (self._tokens[AnswerToken.CORRECT] <= 0 or
                    self._tokens[AnswerToken.YES] <= 0):
                self.start_vote()
            return None
        return 'Unknown question or other error encountered.'

    def undo_answer(self):
        try:
            if self.last_answered is not None and self.last_answered < len(self.questions):
                logging_func(
                    f'Undoing answer for question id {self.last_answered}')
                question = self.questions[self.last_answered]
                token = question.clear_answer()
                self._add_token(token)
                self.player_token_count[question.player_sid][token] -= 1
                self.last_answered = None
                self.game_state = GameState.DAY_PHASE_QUESTIONS
                return True
        except (TypeError, KeyError) as e:
            logging_func(f'Encountered error: {e}')
        logging_func(
            f'No answer to undo for question id: {self.last_answered}')
        return False

    def _add_token(self, token: AnswerToken):
        if token in [AnswerToken.NO, AnswerToken.YES]:
            # Because both count for the mayor tokens... doh.
            self._tokens[AnswerToken.NO] += 1
            self._tokens[AnswerToken.YES] += 1
        else:
            self._tokens[token] += 1

    def _remove_token(self, token: AnswerToken):
        """Decrement the token counter and evaluate/set end of game status.

        Args:
            token: An AnswerToken object for the token to decrement.

        Returns:
            A tuple of bools indicating successfully removing a token.
        """
        if self._tokens[token] > 0:
            if token in [AnswerToken.NO, AnswerToken.YES]:
                self._tokens[AnswerToken.NO] -= 1
                self._tokens[AnswerToken.YES] -= 1
                if self._tokens[token] < 1:
                    self.game_state = GameState.VOTING
                    return True

            else:
                self._tokens[token] -= 1
                if token == AnswerToken.CORRECT:
                    self.game_state = GameState.VOTING
                    return True
            return True

        return False

    def set_update_timestamp(self, timestamp: int) -> None:
        self.update_timestamp = timestamp

    def get_update_timestamp(self) -> int:
        return self.update_timestamp
