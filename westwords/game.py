# Game and player-related classes
import logging
from copy import deepcopy
from datetime import datetime, timedelta
from random import choice, choices, shuffle

from westwords.enums import AnswerToken
from westwords.question import Question, QuestionError

from .enums import Affiliation, AnswerToken, GameState
from .role import (Beholder, Doppelganger, Esper, FortuneTeller, Intern, Mason,
                   Minion, Seer, Villager, Werewolf,
                   DEFAULT_ROLES_BY_PLAYER_COUNT)
from .wordlists import WORDLISTS

logging.basicConfig(level=logging.DEBUG)
# logging.basicConfig(level=logging.INFO)


ROLES = {
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
}


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

    def __init__(self, timer=300, player_sids=[]):
        # TODO: Add concept of a game admin and management of users in that space
        self.timer = timer
        self.player_sids = {}
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
            # Purpose is generally unknown even by lar.
            AnswerToken.LARAMIE: 1,
            AnswerToken.CORRECT: 1,
        }
        self.reset()

    def __repr__(self):
        return f'Game(timer={self.timer},player_sids={list(self.player_sids.keys())})'

    # Game state functions
    def start_night_phase_word_choice(self):
        """Start the night phase of game.

        Returns:
            True if successful; False otherwise.
        """
        if self.game_state != GameState.SETUP:
            logging.debug(f'Game not in SETUP state: {self.game_state}')
            return False
        # TODO: Remove this in favor of choosing roles
        try:
            if not self.selected_roles:
                self.selected_roles = deepcopy(DEFAULT_ROLES_BY_PLAYER_COUNT[
                    str(len(self.player_sids))])
        except KeyError:
            logging.debug(
                f'Config not defined for {len(self.player_sids)} players')
            return False,
        if len(self.selected_roles) != len(self.player_sids):
            logging.debug('Unable to start game. Role/Player count mismatch: '
                          f'{sum(self.selected_roles)} vs {len(self.player_sids)}')
            return False

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
            ] and
                self.word is not None):
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
        if self.game_state != GameState.NIGHT_PHASE_REVEAL:
            return False
        if player_sid in self.player_sids:
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

    def get_players_needing_to_ack(self):
        """Returns a list of player SIDs needing to ack the reveal info."""
        if self.game_state != GameState.NIGHT_PHASE_REVEAL:
            return []
        return self.reveal_ack_required

    def voting_info(self):
        """Returns voting options.

        Returns:
            A list of str player SIDs that are required to vote, a bool whether
            word was guessed, and a list of possible targets."""
        if self.game_state != GameState.VOTING:
            if self.word_guessed:
                candidates = [p for p in self.player_sids
                              if str(self.player_sids[p]) != str(Werewolf)]
            else:
                candidates = self.player_sids
            return self.required_voters, self.word_guessed, candidates
        return None, None

    def set_player_target(self, player_sid, target_sid):
        """Set the target of player's night action.

        Args:
            player_sid: String player SID that is doing the targetting.
            target_sid: String player SID of the targetted player.

        Returns:
            True if successful set; False otherwise."""
        if (self.game_state == GameState.NIGHT_PHASE_TARGETTING and
            player_sid in self.night_actions_required and
                target_sid in self.player_sids):
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

    def get_players(self):
        return self.player_sids

    def get_player_token_count(self, player_sid):
        if player_sid in self.player_token_count:
            return self.player_token_count[player_sid]
        return {
            AnswerToken.YES: 0,
            AnswerToken.NO: 0,
            AnswerToken.MAYBE: 0,
            AnswerToken.SO_CLOSE: 0,
            AnswerToken.SO_FAR: 0,
            AnswerToken.LARAMIE: 0,
            AnswerToken.CORRECT: 0,
        }

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
        self.tokens = self.token_defaults.copy()
        self.vote_count = []
        self.votes = {}
        self.winner = None
        self.word = None
        self.word_choices = []
        self.word_guessed = False
        for player_sid in self.player_sids:
            self.player_sids[player_sid] = None

    def start_vote(self):
        """Start the voting process.

        Returns:
            True if voting state successfully; False otherwise.
        """
        self.word_guessed = self.tokens[AnswerToken.CORRECT] < 1
        elapsed_time = (datetime.now() - self.start_time).seconds
        if elapsed_time < self.timer and not self.word_guessed:
            logging.debug('End of game conditions not met.'
                          f'Word guessed: {self.word_guessed}'
                          f'Elapsed time: {elapsed_time} vs Timer: {self.timer}')
            return False

        if self.game_state != GameState.AWAITING_VOTE:
            logging.debug(
                f'Current game state {self.game_state} is not AWAITING_VOTE.')
            return False

        if self.word_guessed:
            for player_sid in self.player_sids:
                if self.player_sids[player_sid].votes_on_guessed_word:
                    self.required_voters.append(player_sid)
        else:
            # Drop all player_sids into required voters since everyone can vote
            # including Werewolfs and Minions during this state.
            self.required_voters = list(self.player_sids)

        self.game_state = GameState.VOTING
        return True

    def _finish_game(self):
        if self.game_state == GameState.VOTING:
            self._tally_results()
            self.game_state = GameState.FINISHED
            return True
        return False

    def is_started(self):
        return self.game_state in [
            GameState.DAY_PHASE_QUESTIONS,
            GameState.AWAITING_VOTE,
        ]

    def is_voting(self):
        return self.game_state == GameState.VOTING

    def get_words(self):
        """Returns list of word choices if in word choice phase."""
        if self.game_state == GameState.NIGHT_PHASE_WORD_CHOICE:
            if not self.word_choices:
                all_words = []
                for word_list in WORDLISTS:
                    words = WORDLISTS[word_list].get_words(
                        level=self.word_difficulty)
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
                logging.debug(
                    f'Unable to set {word}. Word not in: {self.word_choices}')
                return False
            self.word = word
            self._start_night_phase_doppelganger()
            return True
        return False

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

    def get_results(self):
        """Get results of a game after all voting has completed.

        Returns:
            A tuple Affilition enum for winner, list of str killed player sids,
            and a dict of votes for each player.
        """
        if self.game_state != GameState.FINISHED:
            logging.debug(f'Game not finished, no results to give.')
            return None
        return (self.winner, self.killed_players, self.votes)

    def set_timer(self, time_in_seconds):
        """Set the timer amount in seconds.

        Args:
            time_in_seconds: Integer time. in. seconds.
        """
        if time_in_seconds > 0:
            logging.debug(f'Setting time to {time_in_seconds}')
            self.timer = time_in_seconds

    def get_required_voters(self):
        if self.game_state != GameState.VOTING:
            return []
        return self.required_voters

    def vote(self, voter_sid, target_sid):
        """Votes for player identified by session ID.

        Args:
            voter_sid: SID for the player voting.
            target_sid: SID of the targer player for which the player is voting.

        Returns:
            True if vote was successfully cast; False otherwise.
        """
        if not self.is_voting():
            logging.error(f'Game not in voting state.')
            return False
        if voter_sid not in self.required_voters:
            logging.error(f'Player {voter_sid} is ineligible to vote.')
            return False
        if target_sid not in self.player_sids:
            logging.error(
                f'Unable to vote for player {target_sid}; Not found in game.')
            return False

        self.votes[voter_sid] = target_sid
        if set(self.votes) == set(self.required_voters):
            self._finish_game()
        return True

    def get_tokens(self):
        result = {i.value: self.tokens[i] for i in self.tokens if i not in [
            AnswerToken.NO, AnswerToken.YES]}
        result['yesno'] = self.tokens[AnswerToken.YES]
        return result

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
        if sid in self.player_sids and self.player_sids[sid]:
            return self.player_sids[sid]
        return None

    def _get_next_admin(self):
        try:
            return next(iter(self.player_sids))
        except StopIteration:
            pass
        return None

    def nominate_for_mayor(self, sid):
        if sid in self.player_sids and sid not in self.mayor_nominees:
            self.mayor_nominees.append(sid)
            logging.debug(f'Adding {sid} to mayor nominees')

    def add_player(self, sid):
        """Add player to game.

        Returns:
            True if successful; False otherwise.
        """
        if sid not in self.player_sids:
            self.player_sids[sid] = None
            if not self.admin:
                self.admin = self._get_next_admin()
            return True
        else:
            logging.debug(f'ADD: User {sid} already in game')
            return False

    def remove_player(self, sid):
        if sid in self.player_sids:
            del self.player_sids[sid]
            if self.admin not in self.player_sids:
                self.admin = self._get_next_admin()
        else:
            logging.debug(f'DELETE: User {sid} not in game')

    def is_player_in_game(self, sid):
        logging.debug(f'Attempting to verify player {sid}')
        return sid in self.player_sids

    def _current_role_instances(self, role):
        """Returns the number of instances of provided role in selected roles.

        Args:
            A string role to lookup that matches an existing role value.

        Returns:
            An integer value of number instances.
        """
        return len([
            r for r in self.selected_roles if str(r) == role.capitalize()])

    def add_role(self, role):
        """Add the selected role to game.

        Args:
            role: An object inheriting the westwords.Role object.

        Returns:
            True if role is known and able to be added; False otherwise.
        """
        if self.game_state.name != GameState.SETUP:
            return False

        if self._current_role_instances(role) >= role.get_max_instances():
            logging.info(f'Unable to add {role}: too many of that role.')
            return False
        if len(self.player_sids) < role.get_required_players():
            logging.info(f'Unable to add {role}: too few players.')
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
            logging.info(f'Unable to remove {role} as it is required.')
            return False
        if self._current_role_instances(role) < 1:
            logging.info(
                f'Unable to remove role {role} as it is not selected.')
            return False

        for i in range(len(self.selected_roles)):
            if self.selected_roles[i] == role:
                removed_role = self.selected_roles[i].pop()
                logging.debug(f'Removed role: {removed_role}')
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

    def get_question(self, id):
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
        if (self.tokens[AnswerToken.CORRECT] <= 0 or
                self.tokens[AnswerToken.YES] <= 0):
            return 'Last token played, Undo or Move to vote'

        if question_id < len(self.questions):
            if self.questions[question_id].get_answer():
                return 'Question is already answered.'

            if answer is not AnswerToken.NONE:

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
                        AnswerToken.CORRECT: 0,
                    }
                self.player_token_count[asking_player_sid][answer] += 1
                return None
        return 'Unknown question or other error encountered.'

    def undo_answer(self):
        try:
            if self.last_answered is not None and self.last_answered < len(self.questions):
                logging.debug(
                    f'Undoing answer for question id {self.last_answered}')
                question = self.questions[self.last_answered]
                token = question.clear_answer()
                self._add_token(token)
                self.player_token_count[question.player_sid][token] -= 1
                self.last_answered = None
                self.game_state = GameState.DAY_PHASE_QUESTIONS
                return True
        except (TypeError, KeyError) as e:
            logging.error(f'Encountered error: {e}')
        logging.debug(
            f'No answer to undo for question id: {self.last_answered}')
        return False

    def _add_token(self, token: AnswerToken):
        self.tokens[token] += 1

    def _remove_token(self, token: AnswerToken):
        """Decrement the token counter and evaluate/set end of game status.

        Args:
            token: An AnswerToken object for the token to decrement.

        Returns:
            A tuple of bools indicating successfully removing a token.
        """
        if self.tokens[token] > 0:
            if token in [AnswerToken.NO, AnswerToken.YES]:
                self.tokens[AnswerToken.NO] -= 1
                self.tokens[AnswerToken.YES] -= 1
                if self.tokens[token] < 1:
                    self.game_state = GameState.AWAITING_VOTE
                    return True

            else:
                self.tokens[token] -= 1
                if token == AnswerToken.CORRECT:
                    self.game_state = GameState.AWAITING_VOTE
                    return True
            return True

        return False
