import unittest
from datetime import datetime, timedelta

from westwords import (Beholder, Esper, FortuneTeller, Apprentice, Mason, Minion,
                       Seer, Villager, Werewolf)
from westwords import Game as GameClass
from westwords import Question as QuestionClass


class testWestwordsRoles(unittest.TestCase):
    def setUp(self):
        self.player_sids = {}
        self.word = "Bardily's Best +fraging"
        self.mayor = 'foo'
        self.player_sids['villager'] = Villager()
        self.player_sids['werewolf1'] = Werewolf()
        self.player_sids['seer'] = Seer()
        self.player_sids['doppelbeholder'] = Beholder(doppelganger=True)
        self.player_sids['doppelesper'] = Esper(doppelganger=True)
        self.player_sids['doppelteller'] = FortuneTeller(doppelganger=True)
        self.player_sids['doppelapprentice'] = Apprentice(doppelganger=True)
        self.player_sids['doppelmason'] = Mason(doppelganger=True)
        self.player_sids['doppelminion'] = Minion(doppelganger=True)
        self.player_sids['doppelseer'] = Seer(doppelganger=True)
        self.player_sids['doppelvillager'] = Villager(doppelganger=True)
        self.player_sids['doppelwolf'] = Werewolf(doppelganger=True)
        self.player_sids['mason1'] = Mason()
        self.player_sids['mason2'] = Mason()
        self.player_sids['werewolf2'] = Werewolf()
        self.player_sids['fortuneteller'] = FortuneTeller()
        self.player_sids['apprentice'] = Apprentice()
        self.player_sids['esper'] = Esper()
        self.player_sids['beholder'] = Beholder()
        self.player_sids['minion'] = Minion()

    def testVillagerRoleMayor(self):
        self.assertFalse(self.player_sids['villager'].target_player(
            'villager', 'esper', self.player_sids))
        self.assertEqual(
            self.player_sids['villager'].get_required_players(), 3)
        self.assertEqual(self.player_sids['villager'].get_max_instances(), 8)
        self.assertFalse(self.player_sids['villager'].is_required())
        # Is the mayor
        self.assertEqual(
            self.player_sids['villager'].get_night_action_info(
                player_sid='villager',
                player_roles=self.player_sids,
                mayor='villager',
                word="Bardily's Best +fraging"),
            ("Bardily's Best +fraging", {}))
        self.assertTrue(
            self.player_sids['villager'].add_known_role('esper', 'Esper'))
        # Is the mayor
        self.assertEqual(
            self.player_sids['villager'].get_night_action_info(
                'villager',
                self.player_sids,
                'villager',
                "Bardily's Best +fraging"),
            ("Bardily's Best +fraging", {'esper': 'Esper'}))
        self.assertFalse(self.player_sids['villager'].add_known_role(
            'esper', 'Esper'))
        self.assertFalse(self.player_sids['villager']._role_night_action(
            'villager', 'esper', self.player_sids))

    def testVillagerRoleNotMayor(self):
        # Not the mayor
        self.assertEqual(
            self.player_sids['villager'].get_night_action_info(
                'villager',
                self.player_sids,
                'esper',
                "Bardily's Best +fraging"),
            (None, {}))

    def testMasonRoleMayor(self):
        self.assertFalse(self.player_sids['mason1'].target_player(
            'mason1', 'esper', self.player_sids))
        self.assertEqual(
            self.player_sids['mason1'].get_required_players(), 8)
        self.assertEqual(self.player_sids['mason1'].get_max_instances(), 2)
        self.assertFalse(self.player_sids['mason1'].is_required())
        self.assertIsNone(
            self.player_sids['mason1'].get_night_action_description())
        
        # Is the mayor
        self.assertEqual(
            self.player_sids['mason1'].get_night_action_info(
                'mason1',
                self.player_sids,
                'mason1',
                "Bardily's Best +fraging"),
            ("Bardily's Best +fraging", {'doppelmason': 'Mason (Doppelganger)',
                                         'mason2': 'Mason'}))
        self.assertTrue(
            self.player_sids['mason1'].add_known_role('esper', 'Esper'))
        # Is the mayor
        self.assertEqual(
            self.player_sids['mason1'].get_night_action_info(
                'mason1',
                self.player_sids,
                'mason1',
                "Bardily's Best +fraging"),
            ("Bardily's Best +fraging", {'esper': 'Esper',
                                         'doppelmason': 'Mason (Doppelganger)',
                                         'mason2': 'Mason'}))
        self.assertFalse(self.player_sids['mason1'].add_known_role(
            'esper', 'Esper'))
        self.assertFalse(self.player_sids['mason1']._role_night_action(
            'mason1', 'esper', self.player_sids))

    def testMasonRoleNotMayor(self):
        # Not the mayor
        self.assertEqual(
            self.player_sids['mason1'].get_night_action_info(
                player_sid='mason1',
                player_roles=self.player_sids,
                mayor='esper',
                word="Bardily's Best +fraging"),
            (None, {'doppelmason': 'Mason (Doppelganger)', 'mason2': 'Mason'}))

    def testWerewolfRoleMayor(self):
        self.assertFalse(self.player_sids['werewolf1'].target_player(
            'werewolf1', 'esper', self.player_sids))
        self.assertEqual(
            self.player_sids['werewolf1'].get_required_players(), 0)
        self.assertEqual(self.player_sids['werewolf1'].get_max_instances(), 4)
        self.assertTrue(self.player_sids['werewolf1'].is_required())
        # Is the mayor
        self.assertEqual(
            self.player_sids['werewolf1'].get_night_action_info(
                'werewolf1',
                self.player_sids,
                'werewolf1',
                "Bardily's Best +fraging"),
            ("Bardily's Best +fraging", {'doppelwolf': 'Werewolf (Doppelganger)',
                                         'werewolf2': 'Werewolf'}))
        self.assertTrue(
            self.player_sids['werewolf1'].add_known_role('esper', 'Esper'))
        # Is the mayor
        self.assertEqual(
            self.player_sids['werewolf1'].get_night_action_info(
                'werewolf1',
                self.player_sids,
                'werewolf1',
                "Bardily's Best +fraging"),
            ("Bardily's Best +fraging", {'doppelwolf': 'Werewolf (Doppelganger)',
                                         'esper': 'Esper',
                                         'werewolf2': 'Werewolf'}))
        self.assertFalse(self.player_sids['werewolf1'].add_known_role(
            'esper', 'Esper'))
        self.assertFalse(self.player_sids['werewolf1']._role_night_action(
            'werewolf1', 'werewolf1', self.player_sids))

    def testWerewolfRoleNotMayor(self):
        # Not the mayor
        self.assertEqual(
            self.player_sids['werewolf1'].get_night_action_info(
                player_sid='werewolf1',
                player_roles=self.player_sids,
                mayor='esper',
                word="Bardily's Best +fraging"),
            ("Bardily's Best +fraging", {'doppelwolf': 'Werewolf (Doppelganger)',
                                         'werewolf2': 'Werewolf'}))

    def testSeerRoleMayor(self):
        self.assertFalse(self.player_sids['seer'].target_player(
            'seer', 'esper', self.player_sids))
        self.assertEqual(
            self.player_sids['seer'].get_required_players(), 0)
        self.assertEqual(self.player_sids['seer'].get_max_instances(), 1)
        self.assertFalse(self.player_sids['seer'].is_required())
        # Is the mayor
        self.assertEqual(
            self.player_sids['seer'].get_night_action_info(
                'seer',
                self.player_sids,
                'seer',
                "Bardily's Best +fraging"),
            ("Bardily's Best +fraging", {'doppelseer': 'Seer (Doppelganger)'}))
        self.assertTrue(
            self.player_sids['seer'].add_known_role('esper', 'Esper'))
        # Is the mayor
        self.assertEqual(
            self.player_sids['seer'].get_night_action_info(
                'seer',
                self.player_sids,
                'seer',
                "Bardily's Best +fraging"),
            ("Bardily's Best +fraging", {'doppelseer': 'Seer (Doppelganger)',
                                         'esper': 'Esper'}))
        self.assertFalse(self.player_sids['seer'].add_known_role(
            'esper', 'Esper'))
        self.assertFalse(self.player_sids['seer']._role_night_action(
            'seer', 'esper', self.player_sids))

    def testSeerRoleNotMayor(self):
        # Not the mayor
        self.assertEqual(
            self.player_sids['seer'].get_night_action_info(
                player_sid='seer',
                player_roles=self.player_sids,
                mayor='esper',
                word="Bardily's Best +fraging"),
            ("Bardily's Best +fraging", {'doppelseer': 'Seer (Doppelganger)'}))

    def testFortuneTellerRoleMayor(self):
        self.assertFalse(self.player_sids['fortuneteller'].target_player(
            'fortuneteller', 'esper', self.player_sids))
        self.assertEqual(
            self.player_sids['fortuneteller'].get_required_players(), 5)
        self.assertEqual(self.player_sids['fortuneteller'].get_max_instances(),
                         1)
        self.assertFalse(self.player_sids['fortuneteller'].is_required())
        # Is the mayor
        self.assertEqual(
            self.player_sids['fortuneteller'].get_night_action_info(
                'fortuneteller',
                self.player_sids,
                'fortuneteller',
                "Bardily's Best +fraging"),
            ("Bardily's Best +fraging", {}))
        self.assertTrue(
            self.player_sids['fortuneteller'].add_known_role('esper', 'Esper'))
        # Is the mayor
        self.assertEqual(
            self.player_sids['fortuneteller'].get_night_action_info(
                'fortuneteller',
                self.player_sids,
                'fortuneteller',
                "Bardily's Best +fraging"),
            ("Bardily's Best +fraging", {'esper': 'Esper'}))
        self.assertFalse(self.player_sids['fortuneteller'].add_known_role(
            'esper', 'Esper'))
        self.assertFalse(self.player_sids['fortuneteller']._role_night_action(
            'fortuneteller', 'esper', self.player_sids))

    def testFortuneTellerRoleNotMayor(self):
        # Not the mayor
        self.assertEqual(
            self.player_sids['fortuneteller'].get_night_action_info(
                player_sid='fortuneteller',
                player_roles=self.player_sids,
                mayor='esper',
                word="Bardily's Best +fraging"),
            ("B******** B*** +*******", {}))

    def testApprenticeRoleMayor(self):
        self.assertFalse(self.player_sids['apprentice'].target_player(
            'apprentice', 'esper', self.player_sids))
        self.assertEqual(
            self.player_sids['apprentice'].get_required_players(), 5)
        self.assertEqual(self.player_sids['apprentice'].get_max_instances(), 1)
        self.assertFalse(self.player_sids['apprentice'].is_required())
        # Is the mayor
        self.assertEqual(
            self.player_sids['apprentice'].get_night_action_info(
                'apprentice',
                self.player_sids,
                'apprentice',
                "Bardily's Best +fraging"),
            ("Bardily's Best +fraging", {}))
        self.assertTrue(
            self.player_sids['apprentice'].add_known_role('esper', 'Esper'))
        # Is the mayor
        self.assertEqual(
            self.player_sids['apprentice'].get_night_action_info(
                'apprentice',
                self.player_sids,
                'apprentice',
                "Bardily's Best +fraging"),
            ("Bardily's Best +fraging", {'esper': 'Esper'}))
        self.assertFalse(self.player_sids['apprentice'].add_known_role(
            'esper', 'Esper'))
        self.assertFalse(self.player_sids['apprentice']._role_night_action(
            'apprentice', 'esper', self.player_sids))

    def testApprenticeRoleNotMayorIsNotSeer(self):
        # Not the mayor
        self.assertEqual(
            self.player_sids['apprentice'].get_night_action_info(
                player_sid='apprentice',
                player_roles=self.player_sids,
                mayor='esper',
                word="Bardily's Best +fraging"),
            (None, {}))

    def testApprenticeRoleNotMayorIsSeer(self):
        # Not the mayor
        self.assertEqual(
            self.player_sids['apprentice'].get_night_action_info(
                player_sid='apprentice',
                player_roles=self.player_sids,
                mayor='seer',
                word="Bardily's Best +fraging"),
            ("Bardily's Best +fraging", {'seer': 'Seer'}))

    def testEsperRoleMayor(self):
        self.assertTrue(self.player_sids['esper'].target_player(
            player_sid='esper',
            target_sid='apprentice',
            player_roles=self.player_sids))
        self.assertEqual(
            self.player_sids['apprentice'].get_night_action_info(
                'apprentice',
                self.player_sids,
                'esper',
                "Bardily's Best +fraging"),
            (None, {'esper': 'Esper'}))
        self.assertEqual(
            self.player_sids['esper'].get_required_players(), 5)
        self.assertEqual(self.player_sids['esper'].get_max_instances(), 1)
        self.assertFalse(self.player_sids['esper'].is_required())
        self.assertIsNotNone(
            self.player_sids['esper'].get_night_action_description())
        # Is the mayor
        self.assertEqual(
            self.player_sids['esper'].get_night_action_info(
                'esper',
                self.player_sids,
                'esper',
                "Bardily's Best +fraging"),
            ("Bardily's Best +fraging", {}))
        self.assertTrue(
            self.player_sids['esper'].add_known_role('doppelesper', 'Esper'))
        # Is the mayor
        self.assertEqual(
            self.player_sids['esper'].get_night_action_info(
                'esper',
                self.player_sids,
                'esper',
                "Bardily's Best +fraging"),
            ("Bardily's Best +fraging", {'doppelesper': 'Esper'}))
        self.assertFalse(self.player_sids['esper'].add_known_role(
            'doppelesper', 'Esper'))
        self.assertFalse(self.player_sids['esper']._role_night_action(
            'esper', 'esper', self.player_sids))

    def testEsperRoleNotMayor(self):
        # Not the mayor
        self.assertEqual(
            self.player_sids['esper'].get_night_action_info(
                player_sid='esper',
                player_roles=self.player_sids,
                mayor='apprentice',
                word="Bardily's Best +fraging"),
            (None, {}))

    def testBeholderRoleMayor(self):
        self.assertFalse(self.player_sids['beholder'].target_player(
            'beholder', 'esper', self.player_sids))
        self.assertEqual(
            self.player_sids['beholder'].get_required_players(), 5)
        self.assertEqual(self.player_sids['beholder'].get_max_instances(), 1)
        self.assertFalse(self.player_sids['beholder'].is_required())
        # Is the mayor
        self.assertEqual(
            self.player_sids['beholder'].get_night_action_info(
                'beholder',
                self.player_sids,
                'beholder',
                "Bardily's Best +fraging"),
            ("Bardily's Best +fraging", {
                'doppelapprentice': '???',
                'doppelseer': '???',
                'doppelteller': '???',
                'fortuneteller': '???',
                'apprentice': '???',
                'seer': '???'}))
        self.assertTrue(
            self.player_sids['beholder'].add_known_role('esper', 'Esper'))
        # Is the mayor
        self.assertEqual(
            self.player_sids['beholder'].get_night_action_info(
                'beholder',
                self.player_sids,
                'beholder',
                "Bardily's Best +fraging"),
            ("Bardily's Best +fraging", {
                'esper': 'Esper',
                'doppelapprentice': '???',
                'doppelseer': '???',
                'doppelteller': '???',
                'fortuneteller': '???',
                'apprentice': '???',
                'seer': '???'}))
        self.assertFalse(self.player_sids['beholder'].add_known_role(
            'esper', 'Esper'))
        self.assertFalse(self.player_sids['beholder']._role_night_action(
            'beholder', 'esper', self.player_sids))

    def testBeholderRoleNotMayor(self):
        # Not the mayor
        self.assertEqual(
            self.player_sids['beholder'].get_night_action_info(
                player_sid='beholder',
                player_roles=self.player_sids,
                mayor='esper',
                word="Bardily's Best +fraging"),
            (None, {
                'doppelapprentice': '???',
                'doppelseer': '???',
                'doppelteller': '???',
                'fortuneteller': '???',
                'apprentice': '???',
                'seer': '???'
            }
            ))

    def testMinionRoleMayor(self):
        self.assertFalse(self.player_sids['minion'].target_player(
            'minion', 'esper', self.player_sids))
        self.assertEqual(
            self.player_sids['minion'].get_required_players(), 7)
        self.assertEqual(self.player_sids['minion'].get_max_instances(), 1)
        self.assertFalse(self.player_sids['minion'].is_required())
        # Is the mayor
        self.assertEqual(
            self.player_sids['minion'].get_night_action_info(
                'minion',
                self.player_sids,
                'minion',
                "Bardily's Best +fraging"),
            ("Bardily's Best +fraging", {
                'werewolf1': 'Werewolf',
                    'werewolf2': 'Werewolf',
                    'doppelminion': 'Minion (Doppelganger)',
                    'doppelwolf': 'Werewolf (Doppelganger)', 
            }))
        self.assertTrue(
            self.player_sids['minion'].add_known_role('esper', 'Esper'))
        # Is the mayor
        self.assertEqual(
            self.player_sids['minion'].get_night_action_info(
                'minion',
                self.player_sids,
                'minion',
                "Bardily's Best +fraging"),
            ("Bardily's Best +fraging", {
                'esper': 'Esper',
             'werewolf1': 'Werewolf',
                    'werewolf2': 'Werewolf',
                    'doppelminion': 'Minion (Doppelganger)',
                    'doppelwolf': 'Werewolf (Doppelganger)', }))
        self.assertFalse(self.player_sids['minion'].add_known_role(
            'esper', 'Esper'))
        self.assertFalse(self.player_sids['minion']._role_night_action(
            'minion', 'esper', self.player_sids))

    def testMinionRoleNotMayor(self):
        # Not the mayor
        self.assertEqual(
            self.player_sids['minion'].get_night_action_info(
                player_sid='minion',
                player_roles=self.player_sids,
                mayor='esper',
                word="Bardily's Best +fraging"),
            (None, {'werewolf1': 'Werewolf',
                    'werewolf2': 'Werewolf',
                    'doppelminion': 'Minion (Doppelganger)',
                    'doppelwolf': 'Werewolf (Doppelganger)', }))


if __name__ == '__main__':
    unittest.main()
