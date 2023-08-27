import unittest
from datetime import datetime, timedelta

from westwords import (Affiliation, AnswerToken, Beholder, Doppelganger, Esper,
                       FortuneTeller)
from westwords import Game as GameClass
from westwords import GameError as GameError
from westwords import GameState, Intern, Mason, Minion
from westwords import Question as QuestionClass
from westwords import Seer, Villager, Werewolf


class testGameControlFunctions(unittest.TestCase):

    def setUp(self):
        self.player_sids = ['foo', 'bar', 'baz', 'xxx']
        self.game = GameClass(timer=300, player_sids=self.player_sids)

    def testReset(self):
        self.game = GameClass(player_sids=['foo', 'bar', 'baz', 'xxx'])
        self.game.nominate_for_mayor('baz')
        self.game.start_night_phase_word_choice()
        self.assertEqual(self.game.mayor, 'baz')
        self.game.reset()
        self.assertIsNone(self.game.mayor)

    def testStartVoteFail(self):
        self.game.game_state = GameState.FINISHED
        self.assertFalse(self.game.start_night_phase_word_choice())

    def testStartVoteSuccess(self):
        self.assertTrue(self.game.start_night_phase_word_choice())

    def testReprObject(self):
        self.assertEqual(
            repr(self.game),
            "Game(timer=300,player_sids=['foo', 'bar', 'baz', 'xxx'])")

    def testFinishGameFail(self):
        self.assertFalse(self.game._finish_game())

    def testIsStarted(self):
        self.assertFalse(self.game.is_started())
        self.game.game_state = GameState.DAY_PHASE_QUESTIONS
        self.assertTrue(self.game.is_started())

    def testIsVoting(self):
        self.assertFalse(self.game.is_voting())
        self.game.game_state = GameState.VOTING
        self.assertTrue(self.game.is_voting())


class testGameFunctions(unittest.TestCase):

    def setUp(self):
        self.game = GameClass(timer=300)
        self.player_sids = ['foo', 'bar', 'baz', 'xxx']

    def testGetWords(self):
        self.assertIsNone(self.game.get_words())
        self.game.game_state = GameState.NIGHT_PHASE_WORD_CHOICE
        self.assertIsNotNone(self.game.get_words())

    def testSetWord(self):
        self.assertFalse(self.game.set_word('foo'))
        self.game.game_state = GameState.NIGHT_PHASE_WORD_CHOICE
        list_of_words = self.game.get_words()
        self.assertIsNotNone(list_of_words)
        self.assertTrue(self.game.set_word(list_of_words[0]))
        self.assertFalse(self.game.set_word(list_of_words[0]))
        self.assertEqual(self.game.word, list_of_words[0])

    def testSetWordChoiceCount(self):
        self.game.game_state = GameState.SETUP
        self.assertFalse(self.game.set_word_choice_count(42))
        self.assertFalse(self.game.set_word_choice_count(0))
        self.assertFalse(self.game.set_word_choice_count(-1))
        self.assertTrue(self.game.set_word_choice_count(22))
        self.game.game_state = GameState.NIGHT_PHASE_WORD_CHOICE
        self.assertEqual(len(self.game.get_words()), 22)
        self.assertFalse(self.game.set_word_choice_count(20))

    def testSetTimer(self):
        self.game = GameClass(timer=300, player_sids=self.player_sids)
        self.game.set_timer(1)
        self.game.start_time = datetime.now() - timedelta(seconds=2)
        self.game.game_state = GameState.DAY_PHASE_QUESTIONS
        self.assertTrue(self.game.start_vote())
        self.assertCountEqual(self.game.get_required_voters(),
                              ['foo', 'bar', 'baz', 'xxx'])
        self.game = GameClass(timer=300, player_sids=self.player_sids)
        self.game.set_timer(100)
        self.game.start_time = datetime.now() - timedelta(seconds=97)
        self.assertEqual(self.game.start_vote(), False)

    def testGetResults(self):
        self.assertIsNone(self.game.get_results())
        self.game.winner = 'Werewolf'
        self.game.killed_players = 'villager'
        self.game.votes = {'werewolf': 'villager'}
        self.game.game_state = GameState.FINISHED
        self.assertEqual(self.game.get_results(),
                         ('Werewolf', 'villager', {'werewolf': 'villager'}))

    def testVote(self):
        with self.assertRaises(GameError):
            self.game.vote('foo', 'bar')
        self.game.game_state = GameState.VOTING
        self.game.required_voters = ['foo', 'bar']
        self.game.player_sids = {'foo': None, 'bar': None}
        self.assertTrue(self.game.vote('bar', 'foo'))
        self.assertTrue(self.game.vote('foo', 'bar'))

    def testGetState(self):
        game_status = self.game.get_state('somename')
        self.assertEqual(game_status['game_state'], 'SETUP')
        self.assertEqual(game_status['timer'], 300)
        self.assertEqual(game_status['game_id'], 'somename')
        self.assertEqual(game_status['admin'], None)
        self.assertEqual(game_status['mayor'], None)
        self.assertCountEqual(
            game_status['tokens'],
            {
                AnswerToken.SO_CLOSE.value: 1,
                AnswerToken.MAYBE.value: 10,
                AnswerToken.SO_FAR.value: 1,
                AnswerToken.LARAMIE.value: 1,
                AnswerToken.BRONEY.value: 1,
                AnswerToken.CORRECT.value: 1,
                'yesno': 36,
            },
        )


class testEndOfGameFunctions(unittest.TestCase):

    def setUp(self):
        self.game = GameClass(
            timer=300,
            player_sids=['villager', 'werewolf1', 'seer', 'doppelganger',
                         'mason1', 'mason2', 'werewolf2', 'fortuneteller',
                         'intern', 'esper', 'beholder', 'minion', ])
        self.game.set_timer(1)
        self.game.start_time = datetime.now() - timedelta(seconds=2)
        self.game.player_sids['villager'] = Villager()
        self.game.player_sids['werewolf1'] = Werewolf()
        self.game.player_sids['seer'] = Seer()
        self.game.player_sids['doppelganger'] = Werewolf()
        self.game.player_sids['mason1'] = Mason()
        self.game.player_sids['mason2'] = Mason()
        self.game.player_sids['werewolf2'] = Werewolf()
        self.game.player_sids['fortuneteller'] = FortuneTeller()
        self.game.player_sids['intern'] = Intern()
        self.game.player_sids['esper'] = Esper()
        self.game.player_sids['beholder'] = Beholder()
        self.game.player_sids['minion'] = Minion()
        self.game.game_state = GameState.FINISHED

    def testTallyResultsWerewolfFortuneTellerKillWin(self):
        self.game.word_guessed = True
        self.game.votes = {
            'werewolf1': 'esper',
            'werewolf2': 'fortuneteller',
            'doppelganger': 'fortuneteller',
        }
        self.assertTrue(self.game._tally_results())
        self.assertEqual(self.game.winner, Affiliation.WEREWOLF)

    def testTallyResultsWerewolfSeerKillWin(self):
        self.game.word_guessed = True
        self.game.votes = {
            'werewolf1': 'seer',
            'werewolf2': 'seer',
            'doppelganger': 'fortuneteller',
        }
        self.assertTrue(self.game._tally_results())
        self.assertEqual(self.game.winner, Affiliation.WEREWOLF)

    def testTallyResultsWordGuessedVillageWin(self):
        self.game.word_guessed = True
        self.game.votes = {
            'werewolf1': 'beholder',
            'werewolf2': 'beholder',
            'doppelganger': 'esper',
        }
        self.assertTrue(self.game._tally_results())
        self.assertEqual(self.game.winner, Affiliation.VILLAGE)

    def testTallyResultsWerewolfWin(self):
        self.game.word_guessed = False
        self.game.votes = {
            'villager': 'werewolf2',
            'werewolf1': 'seer',
            'seer': 'werewolf1',
            'doppelganger': 'seer',
            'mason1': 'seer',
            'mason2': 'seer',
            'werewolf2': 'werewolf1',
            'fortuneteller': 'esper',
            'intern': 'seer',
            'esper': 'werewolf2',
            'beholder': 'esper',
            'minion': 'esper',
        }
        self.assertTrue(self.game._tally_results())
        self.assertEqual(self.game.winner, Affiliation.WEREWOLF)

    def testTallyResultsVillageWin(self):
        self.game.word_guessed = False
        self.game.votes = {
            'villager': 'werewolf1',
            'werewolf1': 'seer',
            'seer': 'werewolf1',
            'doppelganger': 'werewolf2',
            'mason1': 'werewolf1',
            'mason2': 'seer',
            'werewolf2': 'werewolf1',
            'fortuneteller': 'werewolf1',
            'intern': 'seer',
            'esper': 'werewolf2',
            'beholder': 'esper',
            'minion': 'esper',
        }
        self.assertTrue(self.game._tally_results())
        self.assertEqual(self.game.winner, Affiliation.VILLAGE)


class testPlayerControlFunctions(unittest.TestCase):

    def setUp(self):
        self.game = GameClass(timer=300)
        self.player_sids = ['foo', 'bar', 'baz', 'xxx']

    def testAddPlayerSuccess(self):
        self.assertFalse(self.game.is_player_in_game('foo'))
        self.assertNotIn('foo', self.game.player_sids)
        self.assertTrue(self.game.add_player('foo'))
        self.assertTrue(self.game.is_player_in_game('foo'))
        self.assertEqual(self.game.admin, 'foo')
        self.assertIn('foo', self.game.player_sids)

    def testAddMultiplePlayersSuccess(self):
        self.assertEqual(self.game.is_player_in_game('foo'), False)
        self.assertNotIn('foo', self.game.player_sids)
        for player_sid in self.player_sids:
            self.assertTrue(self.game.add_player(player_sid))
        for player_sid in self.player_sids:
            self.assertEqual(self.game.is_player_in_game(player_sid), True)
            self.assertIn(player_sid, self.game.player_sids)

    def testInitializeGameWithPlayersSuccess(self):
        self.game = GameClass(player_sids=['foo', 'bar', 'baz', 'xxx'])
        self.assertTrue(self.game.is_player_in_game('foo'))
        self.assertEqual(self.game.admin, 'foo')
        self.assertTrue(self.game.is_player_in_game('bar'))
        self.assertTrue(self.game.is_player_in_game('baz'))
        self.assertTrue(self.game.is_player_in_game('xxx'))

    def testAddPlayerRepeatedlyFailure(self):
        self.assertEqual(self.game.is_player_in_game('foo'), False)
        self.assertNotIn('foo', self.game.player_sids)
        self.assertTrue(self.game.add_player('foo'))
        self.assertFalse(self.game.add_player('foo'))

    def testRemovePlayer(self):
        self.game = GameClass(player_sids=['foo', 'bar', 'baz', 'xxx'])
        self.assertTrue(self.game.is_player_in_game('foo'))
        self.assertEqual(self.game.admin, 'foo')
        self.assertTrue(self.game.is_player_in_game('bar'))
        self.assertTrue(self.game.is_player_in_game('baz'))
        self.assertTrue(self.game.is_player_in_game('xxx'))
        self.game.remove_player('bar')
        self.assertFalse(self.game.is_player_in_game('bar'))
        self.game.remove_player('foo')
        self.assertFalse(self.game.is_player_in_game('foo'))
        self.assertEqual(self.game.admin, 'baz')

    def testGetPlayerRoleFailure(self):
        self.game = GameClass(timer=300, player_sids=['foo', 'bar', 'baz'])
        self.assertIsNone(self.game.get_player_role('foo'))

    def testGetPlayerRoleSuccess(self):
        self.game = GameClass(timer=300, player_sids=['foo', 'bar', 'baz'])
        self.game.start_night_phase_word_choice()
        self.assertTrue(self.game.get_player_role('bar'))


class testRoleSelectionFunctions(unittest.TestCase):

    def setUp(self):
        self.game = GameClass(timer=300,
                              player_sids=['foo', 'bar', 'baz', 'xxx'])

    def testAddRole(self):
        self.assertListEqual(self.game.get_selected_roles(), [])
        roles = self.game.get_possible_roles()
        self.assertEqual(len(roles), 13)
        # TODO: Add more in-depth tests to ensures Roles are being returned with
        # the right numbers.
        for role in roles:
            self.assertGreaterEqual(len(self.game.get_players()),
                                    role.get_required_players())

        for role in roles:
            self.game.add_role(role)
            self.game.remove_role(role)

class testQuestionFunctions(unittest.TestCase):

    def setUp(self):
        self.player_sids = ['foo', 'bar', 'baz', 'xxx']
        self.game = GameClass(timer=300, player_sids=self.player_sids)
        self.game.player_sids['foo'] = Werewolf()
        self.game.player_sids['bar'] = Seer()
        self.game.player_sids['baz'] = Villager()
        self.game.player_sids['xxx'] = Villager()
        self.game.game_state = GameState.DAY_PHASE_QUESTIONS

    def testAddQuestion(self):
        success, id = self.game.add_question('foo', 'Am I wrong?')
        self.assertTrue(success)
        self.assertIsNotNone(id)
        with self.assertRaises(GameError):
            self.game.add_question('not_a_player', 'No matter')

    def testGetQuestion(self):
        self.game.add_question('foo', 'Am I wrong?')
        self.game.add_question('foo', 'Am I wrong?')
        self.game.add_question('foo', 'Am I wrong?')
        success, id = self.game.add_question('foo', 'Am I right for 3?')
        self.assertTrue(success)
        question = self.game.get_question(id)
        self.assertEqual(question.player_sid, 'foo')
        self.assertEqual(question.question_text, 'Am I right for 3?')


    def testAnswerQuestion(self):
        self.game.add_question('foo', 'Am I wrong?')
        error = self.game.answer_question(0, AnswerToken.NO)
        self.assertIsNone(error)
        self.game.add_question('foo', 'Am I wrong?')
        error = self.game.answer_question(2, AnswerToken.MAYBE)
        self.assertEqual(error, 'Unknown question or other error encountered.')
        error = self.game.answer_question(1, AnswerToken.CORRECT)
        self.assertIsNone(error)
        self.assertEqual(self.game.game_state, GameState.VOTING)
        with self.assertRaises(GameError):
            self.game.add_question('foo', 'Am I wrong?')
        error = self.game.answer_question(2, AnswerToken.YES)
        self.assertEqual(error, 'Unknown question or other error encountered.')
        self.assertEqual(self.game.game_state, GameState.VOTING)

    def testUndoAnswer(self):
        self.game.add_question('foo', 'Am I wrong?')
        error = self.game.answer_question(0, AnswerToken.CORRECT)
        self.assertIsNone(error)
        self.assertEqual(self.game.game_state, GameState.VOTING)
        self.game.undo_answer()
        error = self.game.answer_question(0, AnswerToken.YES)
        self.assertIsNone(error)
        self.assertEqual(self.game.game_state, GameState.DAY_PHASE_QUESTIONS)


class testWestwordsInteraction(unittest.TestCase):
    def setUp(self):
        self.player_sids = ['foo', 'bar', 'baz', 'xxx']
        self.game = GameClass(timer=300, player_sids=self.player_sids)
        self.game.set_timer(1)
        self.game.start_time = datetime.now() - timedelta(seconds=2)
        self.game.game_state = GameState.VOTING
        self.game.player_sids['foo'] = Villager()
        self.game.player_sids['bar'] = Villager()
        self.game.player_sids['baz'] = Seer()
        self.game.player_sids['xxx'] = Werewolf()

    def testWerewolfWinWordNotGuessed(self):
        self.assertTrue(self.game.start_vote())
        self.assertCountEqual(self.game.get_required_voters(), self.player_sids)
        self.assertTrue(self.game.vote('xxx', 'bar'))
        self.assertTrue(self.game.vote('foo', 'bar'))
        self.assertTrue(self.game.vote('baz', 'bar'))
        self.assertTrue(self.game.vote('bar', 'xxx'))
        winner, killed_players, votes = self.game.get_results()
        self.assertEqual(winner, Affiliation.WEREWOLF)
        self.assertCountEqual(killed_players, ['bar'])
        expected_votes = {
            'xxx': 'bar',
            'foo': 'bar',
            'baz': 'bar',
            'bar': 'xxx',
        }
        self.assertEqual(expected_votes, votes)

    def testVillageWinWordNotGuessed(self):
        self.assertTrue(self.game.start_vote())
        self.assertCountEqual(self.game.get_required_voters(), self.player_sids)
        self.assertTrue(self.game.vote('xxx', 'bar'))
        self.assertTrue(self.game.vote('foo', 'xxx'))
        self.assertTrue(self.game.vote('baz', 'bar'))
        self.assertTrue(self.game.vote('bar', 'xxx'))
        winner, killed_players, votes = self.game.get_results()
        self.assertEqual(winner, Affiliation.VILLAGE)
        self.assertCountEqual(killed_players, ['bar', 'xxx'])
        expected_votes = {
            'xxx': 'bar',
            'foo': 'xxx',
            'baz': 'bar',
            'bar': 'xxx',
        }
        self.assertEqual(expected_votes, votes)

    def testWerewolfWinWordGuessed(self):
        self.game._remove_token(AnswerToken.CORRECT)
        self.assertTrue(self.game.start_vote())
        self.assertCountEqual(self.game.get_required_voters(), ['xxx'])
        self.assertTrue(self.game.vote('xxx', 'baz'))
        winner, killed, votes = self.game.get_results()
        self.assertEqual(winner, Affiliation.WEREWOLF)
        self.assertEqual(killed, ['baz'])
        self.assertEqual(votes, {'xxx': 'baz'})

    def testVillageWinWordGuessed(self):
        self.game._remove_token(AnswerToken.CORRECT)
        self.assertTrue(self.game.start_vote())
        self.assertCountEqual(self.game.get_required_voters(), ['xxx'])
        self.assertTrue(self.game.vote('xxx', 'bar'))
        winner, killed, votes = self.game.get_results()
        self.assertEqual(winner, Affiliation.VILLAGE)
        self.assertEqual(killed, ['bar'])
        self.assertEqual(votes, {'xxx': 'bar'})


if __name__ == '__main__':
    unittest.main()
