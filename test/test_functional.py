from datetime import datetime, timedelta
import unittest
from westwords import Game as GameClass
from westwords import Question as QuestionClass
from westwords import AnswerToken, GameState, Affiliation
from westwords import (Doppelganger, Mason, Werewolf, Villager, Seer,
                       FortuneTeller, Intern, Esper, Beholder, Minion)


class testWestwordsFunctional(unittest.TestCase):
    def setUp(self):
        self.player_sids = ['foo', 'bar', 'baz', 'xxx']
        self.game = GameClass(timer=300, player_sids=self.player_sids)
        self.game.set_timer(1)
        self.game.start_time = datetime.now() - timedelta(seconds=2)
        self.game.game_state = GameState.DAY_PHASE_QUESTIONS
        self.player_sids['villager'] = Villager()
        self.player_sids['werewolf1'] = Werewolf()
        self.player_sids['seer'] = Seer()
        self.player_sids['doppelganger'] = Doppelganger()
        self.player_sids['mason1'] = Mason()
        self.player_sids['mason2'] = Mason()
        self.player_sids['werewolf2'] = Werewolf()
        self.player_sids['fortuneteller'] = FortuneTeller()
        self.player_sids['intern'] = Intern()
        self.player_sids['esper'] = Esper()
        self.player_sids['beholder'] = Beholder()
        self.player_sids['minion'] = Minion()


    def testFullGameWorkflow(self):
        self.game = GameClass(player_sids=['foo', 'bar', 'baz', 'xxx'])
        self.game.nominate_for_mayor('baz')
        self.game.start_night_phase_word_choice()
        self.assertEqual(self.game.mayor, 'baz')
        self.game.reset()
        self.assertIsNone(self.game.mayor)
        self.game.nominate_for_mayor('foo')
        self.game.start_night_phase_word_choice()
        # Add role-related stuff

        for player_sid in self.player_sids:
            self.assertIsNotNone(self.game.player_sids[player_sid])

        self.game.start_day_phase()
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

if __name__ == '__main__':
    unittest.main()
