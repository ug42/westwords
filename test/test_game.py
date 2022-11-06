import unittest
from westwords import Game as GameClass
from westwords import Question as QuestionClass
from westwords import AnswerToken

class testGame(unittest.TestCase):

    def setUp(self):
        self.game = GameClass(timer=300, player_sids=[])
        self.player_sids = ['foo', 'bar', 'baz', 'xxx']
        pass

    def tearDown(self):
        pass

    def testAddPlayerSuccess(self):
        self.assertFalse(self.game.is_player_in_game('foo'))
        self.assertNotIn('foo', self.game.player_sids)
        self.game.add_player('foo')
        self.assertTrue(self.game.is_player_in_game('foo'))
        self.assertEqual(self.game.admin, 'foo')
        self.assertIn('foo', self.game.player_sids)

    def testAddMultiplePlayersSuccess(self):
        self.assertEqual(self.game.is_player_in_game('foo'), False)
        self.assertNotIn('foo', self.game.player_sids)
        for player_sid in self.player_sids:
            self.game.add_player(player_sid)
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
        self.game.add_player('foo')
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

    def testGameWorkflow(self):
        self.game = GameClass(player_sids=['foo', 'bar', 'baz', 'xxx'])
        self.game.nominate_for_mayor('baz')
        self.game.start()
        self.assertEqual(self.game.mayor, 'baz')
        self.game.reset()
        self.assertIsNone(self.game.mayor)
        self.game.nominate_for_mayor('foo')
        self.game.start()
        for player_sid in self.player_sids:
            self.assertIsNotNone(self.game.player_sids[player_sid])
            print(f'{player_sid}: {self.game.player_sids[player_sid]}')
        self.game.player_sids['foo'] = "villager"
        self.game.player_sids['bar'] = "villager"
        self.game.player_sids['baz'] = "seer"
        self.game.player_sids['xxx'] = "werewolf"
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
        self.game.start_vote(word_guessed=True)
        self.assertEqual(self.game.required_voters, ['xxx'])
        self.assertFalse(self.game.vote('baz', 'xxx'))
        self.assertTrue(self.game.vote('xxx', 'bar'))
        self.assertTrue(self.game.get_results(), ('village', {'xxx': 'bar'}))
        
        

if __name__ == '__main__':
    unittest.main()