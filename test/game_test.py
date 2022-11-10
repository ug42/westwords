from datetime import datetime, timedelta
import unittest
from westwords import Game as GameClass
from westwords import Question as QuestionClass
from westwords import AnswerToken, GameState, Affiliation
from westwords import (Doppelganger, Mason, Werewolf, Villager, Seer,
                       FortuneTeller, Intern, Esper, Beholder, Minion)


class testGameUnits(unittest.TestCase):

    def setUp(self):
        self.game = GameClass(timer=300)
        self.player_sids = ['foo', 'bar', 'baz', 'xxx']

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
            "Game(timer=300,player_sids=[])")

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

    def testTallyResults(self):

        pass

    def testSetTimer(self):
        self.game = GameClass(timer=300, player_sids=self.player_sids)
        self.game.set_timer(1)
        self.game.start_time = datetime.now() - timedelta(seconds=2)
        self.game.game_state = GameState.DAY_PHASE_QUESTIONS
        self.assertEqual(self.game.start_vote(word_guessed=False),
                         (True, ['foo', 'bar', 'baz', 'xxx']))
        self.game = GameClass(timer=300, player_sids=self.player_sids)
        self.game.set_timer(100)
        self.game.start_time = datetime.now() - timedelta(seconds=2)
        self.game.game_state = GameState.DAY_PHASE_QUESTIONS
        self.assertEqual(self.game.start_vote(word_guessed=False), (False, []))

    def testGetResults(self):
        self.assertIsNone(self.game.get_results())
        self.game.winner = 'Werewolf'
        self.game.killed_players = 'villager'
        self.game.votes = {'werewolf': 'villager'}
        self.game.game_state = GameState.FINISHED
        self.assertEqual(self.game.get_results(),
                         ('Werewolf', 'villager', {'werewolf': 'villager'}))
        
    def testVote(self):
        self.assertFalse(self.game.vote('foo', 'bar'))
        self.game.game_state = GameState.VOTING
        self.game.required_voters = ['foo', 'bar']
        self.game.player_sids = {'foo': None, 'bar': None}
        self.assertTrue(self.game.vote('bar', 'foo'))
        self.assertTrue(self.game.vote('foo', 'bar'))
    
    def testGetState(self):
        self.game.get_state()

        # self.game._get_next_admin()

        # self.game.get_player_role(sid)
        # self.game.nominate_for_mayor(sid)
        # self.game.add_player(sid)
        # self.game.remove_player(sid)
        # self.game.is_player_in_game(sid)

        # self.game._current_role_instances(role)
        # self.game.add_role(role)
        # self.game.remove_role(role)
        # self.game.get_selected_roles()
        # self.game.get_possible_roles()

        # self.game.add_question(sid, question_text)
        # self.game.get_question(id)
        # self.game._get_next_question_id()
        # self.game.answer_question(question_id, answer)
        # self.game.undo_answer()

        # self.game._add_token(token)
        # self.game.get_tokens()
        # self.game.remove_token(token)

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


class testWestwordsInteraction(unittest.TestCase):
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
        self.assertCountEqual(players, ['xxx'])
        self.assertTrue(self.game.vote('xxx', 'bar'))
        winner, killed, votes = self.game.get_results()
        self.assertEqual(winner, Affiliation.VILLAGE)
        self.assertEqual(killed, ['bar'])
        self.assertEqual(votes, {'xxx': 'bar'})


if __name__ == '__main__':
    unittest.main()
