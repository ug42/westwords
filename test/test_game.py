from datetime import datetime, timedelta
import unittest
from westwords import Game as GameClass
from westwords import Question as QuestionClass
from westwords import AnswerToken, GameState, Affiliation
from westwords import (Doppelganger, Mason, Werewolf, Villager, Seer,
                       FortuneTeller, Intern, Esper, Beholder, Minion)


class testGameUnits(unittest.TestCase):

    def setUp(self):
        self.game = GameClass(timer=300, player_sids=[])
        self.player_sids = ['foo', 'bar', 'baz', 'xxx']

    def tearDown(self):
        pass

    def testReset(self):
        self.game = GameClass(player_sids=['foo', 'bar', 'baz', 'xxx'])
        self.game.nominate_for_mayor('baz')
        self.game.start_night_phase()
        self.assertEqual(self.game.mayor, 'baz')
        self.game.reset()
        self.assertIsNone(self.game.mayor)

    def testStart(self):
        pass

    def testStartVoteFail(self):
        pass

    def testStartVoteSuccess(self):
        pass

    def testReprObject(self):
        pass

    def testFinishGameSuccess(self):
        pass

    def testFinishGameFail(self):
        pass

    def testIsStarted(self):
        pass

    def testIsVoting(self):
        pass

    def testGetWords(self):
        pass

    def testSetWord(self):
        pass

    def testSetWordChoiceCount(self):
        pass

    def testTallyResults(self):
        pass

    # def get_results(self):
    # def set_timer(self, time_in_seconds):
    # def vote(self, voter_sid, target_sid):
    # def get_tokens(self):
    # def get_state(self, game_id):
    # def get_player_role(self, sid):
    # def _get_next_admin(self):
    # def nominate_for_mayor(self, sid):
    # def add_player(self, sid):
    # def remove_player(self, sid):
    # def is_player_in_game(self, sid):
    # def _current_role_instances(self, role):
    # def add_role(self, role):
    # def remove_role(self, role):
    # def get_selected_roles(self):
    # def get_possible_roles(self):
    # def add_question(self, sid, question_text):
    # def get_question(self, id):
    # def _get_next_question_id(self):
    # def answer_question(self, question_id: int, answer: AnswerToken):
    # def undo_answer(self):
    # def _add_token(self, token: AnswerToken):
    # def remove_token(self, token: AnswerToken):

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

    def testInitializeGameSuccess(self):
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


class testWestwordsFunctional(unittest.TestCase):
    def setUp(self):
        self.player_sids = ['foo', 'bar', 'baz', 'xxx']
        self.game = GameClass(timer=300, player_sids=self.player_sids)
        self.game.set_timer(1)
        self.game.start_time = datetime.now() - timedelta(seconds=2)
        self.game.game_state = GameState.DAY_PHASE_QUESTIONS
        self.game.player_sids['foo'] = Villager()
        self.game.player_sids['bar'] = Villager()
        self.game.player_sids['baz'] = Seer()
        self.game.player_sids['xxx'] = Werewolf()

    def testWerewolfWinWordNotGuessed(self):
        success, players = self.game.start_vote(word_guessed=False)
        self.assertTrue(success)
        self.assertCountEqual(self.player_sids, players)
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
        success, players = self.game.start_vote(word_guessed=False)
        self.assertTrue(success)
        self.assertCountEqual(self.player_sids, players)
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
        success, players = self.game.start_vote(word_guessed=True)
        self.assertTrue(success)
        self.assertCountEqual(players, ['xxx'])
        self.assertTrue(self.game.vote('xxx', 'baz'))
        winner, killed, votes = self.game.get_results()
        self.assertEqual(winner, Affiliation.WEREWOLF)
        self.assertEqual(killed, ['baz'])
        self.assertEqual(votes, {'xxx': 'baz'})

    def testVillageWinWordGuessed(self):
        success, players = self.game.start_vote(word_guessed=True)
        self.assertTrue(success)
        print(players)
        self.assertCountEqual(players, ['xxx'])
        self.assertTrue(self.game.vote('xxx', 'bar'))
        winner, killed, votes = self.game.get_results()
        self.assertEqual(winner, Affiliation.VILLAGE)
        self.assertEqual(killed, ['bar'])
        self.assertEqual(votes, {'xxx': 'bar'})

    def testFullGameWorkflow(self):
        self.game = GameClass(player_sids=['foo', 'bar', 'baz', 'xxx'])
        self.game.nominate_for_mayor('baz')
        self.game.start_night_phase()
        self.assertEqual(self.game.mayor, 'baz')
        self.game.reset()
        self.assertIsNone(self.game.mayor)
        self.game.nominate_for_mayor('foo')
        self.game.start_night_phase()
        # Add role-related stuff
        self.game.start_day_phase()

        for player_sid in self.player_sids:
            self.assertIsNotNone(self.game.player_sids[player_sid])
        self.game.player_sids['foo'] = Villager()
        self.game.player_sids['bar'] = Villager()
        self.game.player_sids['baz'] = Seer()
        self.game.player_sids['xxx'] = Werewolf()

        success, id = self.game.add_question('foo', 'How can this be?')
        self.assertFalse(success)
        self.assertIsNone(id)
        # Assure we can't answer a question that doesn't yet exist
        self.assertFalse(self.game.answer_question(0, AnswerToken.NONE))

        success, id = self.game.add_question('bar', 'Am I the first question?')
        self.assertTrue(success)
        self.assertEqual(id, 0)
        self.assertTrue(self.game.answer_question(id, AnswerToken.YES))

        success, id = self.game.add_question('baz', 'Is it a squirrel?')
        self.assertTrue(success)
        self.assertEqual(id, 1)
        self.assertTrue(self.game.answer_question(id, AnswerToken.NO))

        success, id = self.game.add_question('xxx', 'Chimpanzee?')
        self.assertTrue(success)
        self.assertEqual(id, 2)
        self.assertTrue(self.game.answer_question(id, AnswerToken.CORRECT))

        success, players = self.game.start_vote(word_guessed=True)
        self.assertEqual(self.game.required_voters, ['xxx'])
        self.assertEqual(players, ['xxx'])

        self.assertFalse(self.game.vote('baz', 'xxx'))
        self.assertTrue(self.game.vote('xxx', 'bar'))
        self.assertEqual(self.game.get_results(),
                         (Affiliation.VILLAGE, ['bar'], {'xxx': 'bar'}))

    def testAllRolesFullGameWorkflow(self):
        """
        Doppelganger
        Mason
        Werewolf
        Villager
        Seer
        FortuneTeller
        Intern
        Esper
        Beholder
        Minion
        """
        pass


if __name__ == '__main__':
    unittest.main()
