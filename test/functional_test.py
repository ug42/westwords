from datetime import datetime, timedelta
import random
import unittest
from westwords import Game as GameClass
from westwords import GameError as GameError
from westwords import Question as QuestionClass
from westwords import AnswerToken, GameState, Affiliation
from westwords import (Doppelganger, Mason, Werewolf, Villager, Seer,
                       FortuneTeller, Apprentice, Esper, Beholder, Minion)


def add_roles(game: GameClass):
    game.add_role('Seer')
    game.add_role('Doppelganger')
    game.add_role('Mason')
    game.add_role('Mason')
    game.add_role('Werewolf')
    game.add_role('FortuneTeller')
    game.add_role('Apprentice')
    game.add_role('Esper')
    game.add_role('Beholder')
    game.add_role('Minion')

class testWestwordsFunctional(unittest.TestCase):
    def setUp(self):
        self.player_sid_list = ['villager', 'werewolf1', 'seer', 'doppelganger',
                                'mason1', 'mason2', 'werewolf2', 'fortuneteller', 'apprentice', 'esper',
                                'beholder', 'minion', ]
        self.game = GameClass(timer=300, player_sids=self.player_sid_list)
        self.game.set_timer(1)
        self.game.start_time = datetime.now() - timedelta(seconds=2)

        self.player_sids = {}
        self.player_sids['villager'] = Villager()
        self.player_sids['werewolf1'] = Werewolf()
        self.player_sids['seer'] = Seer()
        self.player_sids['doppelganger'] = Doppelganger()
        self.player_sids['mason1'] = Mason()
        self.player_sids['mason2'] = Mason()
        self.player_sids['werewolf2'] = Werewolf()
        self.player_sids['fortuneteller'] = FortuneTeller()
        self.player_sids['apprentice'] = Apprentice()
        self.player_sids['esper'] = Esper()
        self.player_sids['beholder'] = Beholder()
        self.player_sids['minion'] = Minion()

        add_roles(self.game)

    def testFullGameWorkflow(self):
        word_list_length = 10
        self.game.nominate_for_mayor('villager')
        self.game.start_night_phase_word_choice()
        self.assertEqual(self.game.mayor, 'villager')
        self.game.reset()
        add_roles(self.game)
        self.assertIsNone(self.game.mayor)
        self.game.nominate_for_mayor('mason1')
        self.assertTrue(self.game.set_word_choice_count(word_list_length))
        self.game.start_night_phase_word_choice()
        # Add role-related stuff

        for player_sid in self.player_sids:
            # Check that all roles are assigned.
            self.assertIsNotNone(self.game.player_sids[player_sid])

        # Set the roles to known values
        self.game.player_sids = self.player_sids

        # Choose the word
        self.assertEqual(self.game.game_state,
                         GameState.NIGHT_PHASE_WORD_CHOICE)
        words = self.game.get_words()
        self.assertEqual(len(words), word_list_length)
        selected_word = random.choice(words)
        self.game.set_word(selected_word)

        # Do the doppelganger role
        self.assertEqual(self.game.game_state,
                         GameState.NIGHT_PHASE_DOPPELGANGER)
        self.assertTrue(
            self.game.set_doppelganger_target('doppelganger', 'esper'))

        # Do the targetting roles
        self.assertEqual(self.game.game_state,
                         GameState.NIGHT_PHASE_TARGETTING)
        self.assertCountEqual(self.game.night_actions_required,
                              ['esper', 'doppelganger'])
        self.assertFalse(self.game.set_player_target('seer', 'werewolf1'))
        self.assertTrue(self.game.set_player_target(
            'doppelganger', 'werewolf2'))
        self.assertTrue(self.game.set_player_target('esper', 'seer'))

        # Do the reveal and ack knowledge of stuff
        self.assertEqual(self.game.game_state,
                         GameState.NIGHT_PHASE_REVEAL)
        self.assertCountEqual(self.game.get_players_needing_to_ack(),
                              self.player_sid_list)

        word, roles = self.game.get_player_revealed_information('villager')
        self.assertIsNone(word)
        self.assertEqual(roles, {})
        self.game.acknowledge_revealed_info('villager')
        word, roles = self.game.get_player_revealed_information(
            'werewolf1', acknowledge=True)
        self.assertEqual(word, selected_word)
        self.assertEqual(roles, {'werewolf2': 'Werewolf'})
        word, roles = self.game.get_player_revealed_information(
            'seer', acknowledge=True)
        self.assertEqual(word, selected_word)
        self.assertEqual(roles, {'esper': 'Esper'})
        word, roles = self.game.get_player_revealed_information(
            'doppelganger', acknowledge=True)
        self.assertEqual(word, None)
        self.assertEqual(roles, {'esper': 'Esper'})
        word, roles = self.game.get_player_revealed_information(
            'mason1', acknowledge=True)
        self.assertEqual(word, selected_word)
        self.assertEqual(roles, {'mason2': 'Mason'})
        word, roles = self.game.get_player_revealed_information(
            'mason2', acknowledge=True)
        self.assertEqual(word, None)
        self.assertEqual(roles, {'mason1': 'Mason'})
        word, roles = self.game.get_player_revealed_information(
            'werewolf2', acknowledge=True)
        self.assertEqual(word, selected_word)
        self.assertEqual(
            roles, {'doppelganger': 'Esper (Doppelganger)', 'werewolf1': 'Werewolf'})
        word, roles = self.game.get_player_revealed_information(
            'fortuneteller', acknowledge=True)
        self.assertRegexpMatches(word, r'(.\*+){1,}$')
        self.assertEqual(roles, {})
        word, roles = self.game.get_player_revealed_information(
            'apprentice', acknowledge=True)
        self.assertEqual(word, None)
        self.assertEqual(roles, {})
        word, roles = self.game.get_player_revealed_information(
            'esper', acknowledge=True)
        self.assertEqual(word, None)
        self.assertEqual(roles, {})
        word, roles = self.game.get_player_revealed_information(
            'beholder', acknowledge=True)
        self.assertEqual(word, None)
        self.assertEqual(
            roles, {'seer': '???', 'fortuneteller': '???', 'apprentice': '???'})
        self.assertFalse(self.game.acknowledge_revealed_info('werewolf2'))
        word, roles = self.game.get_player_revealed_information('minion')
        self.assertEqual(word, None)
        self.assertEqual(
            roles, {'werewolf1': 'Werewolf', 'werewolf2': 'Werewolf'})
        self.game.acknowledge_revealed_info('minion')

        # After ack of all roles, it should automatically start day phase.
        self.assertEqual(self.game.game_state, GameState.DAY_PHASE_QUESTIONS)
        # Ensure Mayor is unable to ask questions.
        with self.assertRaises(GameError):
            self.game.add_question('mason1', 'How can this be?')
        # Assure we can't answer a question that doesn't yet exist
        error = self.game.answer_question(0, AnswerToken.YES)
        self.assertEqual(error, 'Unknown question or other error encountered.')

        success, id = self.game.add_question(
            'mason2', 'Am I the first question?')
        self.assertTrue(success)
        self.assertEqual(id, 0)
        error = self.game.answer_question(id, AnswerToken.YES)
        self.assertIsNone(error)

        success, id = self.game.add_question('werewolf2', 'Is it a squirrel?')
        self.assertTrue(success)
        self.assertEqual(id, 1)
        error = self.game.answer_question(id, AnswerToken.NO)
        self.assertIsNone(error)

        success, id = self.game.add_question('villager', 'Chimpanzee?')
        self.assertTrue(success)
        self.assertEqual(id, 2)
        error = self.game.answer_question(id, AnswerToken.CORRECT)
        self.assertIsNone(error)

        self.assertEqual(self.game.game_state, GameState.VOTING)
        self.assertEqual(self.game.get_required_voters(),
                         ['werewolf1', 'werewolf2'])

        self.assertTrue(self.game.vote('werewolf1', 'villager'))
        self.assertTrue(self.game.vote('werewolf2', 'mason2'))
        self.assertEqual(self.game.game_state, GameState.FINISHED)
        winner, killed_players, votes, players = self.game.get_results()
        self.assertEqual(winner, Affiliation.VILLAGE)
        self.assertEqual(killed_players, ['villager', 'mason2'])
        self.assertEqual(
            votes, {'werewolf1': 'villager', 'werewolf2': 'mason2'})
        self.assertCountEqual(players, self.player_sid_list)


if __name__ == '__main__':
    unittest.main()
