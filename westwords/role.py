from westwords.enums import Affiliation
import logging

# logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)


ROLE_SET = {}


class RoleSet(object):

    def __init__(self, player_count: int = 3):
        self.player_count = player_count

    def get_role_set(self):
        pass

    def set_role_set(self):
        pass


class Role(object):
    def __init__(self, doppelganger=False):
        self.affiliation = Affiliation.VILLAGE
        self.description = "Generic night action, no vote ability."
        self.doppelganger = doppelganger
        self.image_name = None
        self.known_players = {}
        self.known_word = None
        self.max_instances = 1
        self.required = False
        self.required_players = 0
        self.night_action_description = None
        self.targetted_player = None
        # Whether this role's night action are done
        self.night_phase_complete = False
        # Whether this role targets another player with an action
        self.targetting_role = False
        self.team_loses_if_killed = False
        self.votes_on_guessed_word = False

    def __str__(self):
        return type(self).__name__

    def get_affiliation(self) -> Affiliation:
        return self.affiliation

    def get_max_instances(self):
        return self.max_instances

    def get_string_id(self):
        return type(self).__name__.casefold().replace(' ', '')

    def is_required(self):
        return self.required

    def is_targetting_role(self):
        return self.targetting_role

    def get_required_players(self):
        return self.required_players

    def _role_night_action(self, player_sid, target_sid, player_roles):
        """Night phase targeting-specific role actions."""
        return False

    def add_known_role(self, player_sid, role):
        if player_sid not in self.known_players:
            self.known_players[player_sid] = role
            return True
        else:
            logging.debug(f'Player {player_sid} already in known roles.')
        return False

    def target_player(self, player_sid, target_sid, player_roles):
        if self.targetting_role:
            self.targetted_player = target_sid
            self._role_night_action(player_sid, target_sid, player_roles)
            return True
        return False

    def get_night_action_description(self):
        if self.targetting_role:
            return self.night_action_description
        return None

    def get_role_description(self) -> str:
        return self.description

    def get_image_name(self) -> str:
        if self.image_name:
            return self.image_name
        return None

    def get_night_action_info(self, player_sid, player_roles, mayor, word):
        """Calculate any night info and return it for the player role.

        Args:
            player_roles: A dict of string player SIDs to Role objects.
            mayor: A string player SID of the current mayor.

        Returns:
            Returns a dict of player SID strings to string roles.
        """
        # If the player is the mayor, we override all the other stuff. /shrug
        if player_sid == mayor:
            logging.debug(f'Setting word as known for mayor: {mayor}.')
            self.known_word = word
        return (self.known_word, self.known_players)


class Doppelganger(Role):
    def __init__(self, doppelganger=False):
        super().__init__(doppelganger=doppelganger)
        # This role has no intrinsic night-time ability, so it is called out
        # separately to determine its eventual role associated night action, if
        # any.
        self.description = """
        Doppelganger chooses a player to see their role, and copies that
        player's ability and alignment.
        """
        self.night_action_description = """
        Choose a player to mimic. You will become a copy of their role.
        """
        self.image_name = 'doppelganger.png'
        self.affiliation = Affiliation.VILLAGE
        self.required_players = 6
        self.max_instances = 6
        # Doppelganger is special cased to not target during normal phase.
        self.targetting_role = True

    def __str__(self):
        role_str = "Doppelganger"
        if self.doppelganger:
            role_str += " (Doppelganger)"
        return role_str


class Werewolf(Role):
    def __init__(self, doppelganger=False):
        super().__init__(doppelganger=doppelganger)
        self.description = """
        A werewolf. Not really evil, just misunderstood. You'll try to lead
        guesses away from the word, as you will have seen the word and other
        werewolves, but not minion. If Village team guesses the word, Werewolves
        have a chance to win by finding and executing the Seer/Apprentice Seer
        or Fortune Teller.
        """
        self.image_name = 'werewolf.png'
        self.max_instances = 4
        self.required = True
        self.required_players = 0
        self.sees_word = True
        self.team_loses_if_killed = True
        self.votes_on_guessed_word = True
        self.affiliation = Affiliation.WEREWOLF

    def __str__(self):
        role_str = "Werewolf"
        if self.doppelganger:
            role_str += " (Doppelganger)"
        return role_str

    def get_night_action_info(self, player_sid, player_roles, mayor, word):
        self.known_word = word
        for p in player_roles:
            if (self != player_roles[p] and
                    isinstance(player_roles[p], Werewolf)):
                self.known_players[p] = str(player_roles[p])
        return super().get_night_action_info(player_sid, player_roles, mayor, word)


class Villager(Role):
    def __init__(self, doppelganger=False):
        super().__init__(doppelganger=doppelganger)
        self.description = """
        Ordinary villager. Asks questions, tries to guess word. Wins with
        Village team.
        """
        self.image_name = 'villager.png'
        self.required_players = 3
        self.max_instances = 8

    def __str__(self):
        role_str = "Villager"
        if self.doppelganger:
            role_str += " (Doppelganger)"
        return role_str


class Seer(Role):
    def __init__(self, doppelganger=False):
        super().__init__(doppelganger=doppelganger)
        self.description = """
        The Seer. As in they've seen things, and that is generally a bad idea.
        They're aligned with Village and see the word. If the Village team
        guesses the word, the Werewolves team will have a chance to find and
        execute the Seer or other word-seeing roles to steal the win.
        """
        self.image_name = 'seer.png'
        self.required = False
        self.required_players = 0
        self.team_loses_if_killed = True

    def __str__(self):
        role_str = "Seer"
        if self.doppelganger:
            role_str += " (Doppelganger)"
        return role_str

    def get_night_action_info(self, player_sid, player_roles, mayor, word):
        self.known_word = word
        for p in player_roles:
            if (self != player_roles[p] and
                    isinstance(player_roles[p], Seer)):
                self.known_players[p] = str(player_roles[p])
        return super().get_night_action_info(player_sid, player_roles, mayor, word)


class Apprentice(Role):
    def __init__(self, doppelganger=False):
        super().__init__(doppelganger=doppelganger)
        # Will only see word if Mayor is Seer
        self.description = """
        An ordinary villager unless the Mayor is a Seer, in which case, they
        become the Seer, with all that entails. The mayor is no longer the
        Werewolves' target; the Apprentice is. (and maybe a Fortune Teller)
        """
        self.image_name = 'apprentice.png'
        self.sees_word = False
        self.required_players = 5
        # This will be set to true if Mayor is the Seer.
        self.team_loses_if_killed = False

    def __str__(self):
        role_str = "Apprentice"
        if self.doppelganger:
            role_str += " (Doppelganger)"
        return role_str

    def get_night_action_info(self, player_sid, player_roles, mayor, word):
        if isinstance(player_roles[mayor], Seer):
            self.sees_word = True
            self.known_word = word
            self.add_known_role(mayor, str(player_roles[mayor]))
        return super().get_night_action_info(player_sid, player_roles, mayor, word)


class FortuneTeller(Role):
    def __init__(self, doppelganger=False):
        super().__init__(doppelganger=doppelganger)
        self.description = """
        The Fortune Teller. Probably not a great one seeing as they only get to
        see the first letter of each word. They align with the Village team.
        Werewolf team wins if they find them, the Seer, or an Apprentice Seer.
        """
        self.image_name = 'fortune_teller.png'
        self.sees_word = False
        self.required_players = 5
        self.max_instances = 4
        self.team_loses_if_killed = True

    def __str__(self):
        role_str = "Fortune Teller"
        if self.doppelganger:
            role_str += " (Doppelganger)"
        return role_str

    def get_night_action_info(self, player_sid, player_roles, mayor, word):
        sub_words = []
        # The footer requests this information before it's set by mayor
        if word:
            for sub_word in word.split():
                sub_words.append(f'{sub_word[0]}{"*" * (len(sub_word) - 1)}')
            self.known_word = ' '.join(sub_words)
        return super().get_night_action_info(player_sid, player_roles, mayor, word)


class Minion(Role):
    def __init__(self, doppelganger=False):
        super().__init__(doppelganger=doppelganger)
        self.description = """
        A minion. You align with the Werewolf team, but they don't see the
        minion. (typical...) Village team still wins if executing the Minion,
        but you don't get to vote. It's like High School again. All risk, very
        little reward.
        """
        self.image_name = 'minion.png'
        self.required_players = 7
        self.team_loses_if_killed = True
        self.votes_on_guessed_word = False
        self.affiliation = Affiliation.WEREWOLF

    def __str__(self):
        role_str = "Minion"
        if self.doppelganger:
            role_str += " (Doppelganger)"
        return role_str

    def get_night_action_info(self, player_sid, player_roles, mayor, word):
        for p in player_roles:
            if (self != player_roles[p] and
                    isinstance(player_roles[p], (Werewolf, Minion))):
                self.known_players[p] = str(player_roles[p])
        return super().get_night_action_info(player_sid, player_roles, mayor, word)


class Beholder(Role):
    def __init__(self, doppelganger=False):
        super().__init__(doppelganger=doppelganger)
        self.description = """
        The beholder is a villager who knows the players with the Apprentice,
        Seer and Fortune Teller roles, but not who has which role. Village team
        does not lose if Werewolves kill a Beholder.
        """
        self.image_name = 'beholder.png'
        self.required_players = 5

    def __str__(self):
        role_str = "Beholder"
        if self.doppelganger:
            role_str += " (Doppelganger)"
        return role_str

    def get_night_action_info(self, player_sid, player_roles, mayor, word):
        for p in player_roles:
            if isinstance(player_roles[p],
                          (Apprentice, Seer, FortuneTeller)):
                self.known_players[p] = "???"
        return super().get_night_action_info(player_sid, player_roles, mayor, word)


class Mason(Role):
    def __init__(self, doppelganger=False):
        super().__init__(doppelganger=doppelganger)
        self.description = """
        A Mason. A villager who knows the other Masons.
        """
        self.image_name = 'mason.png'
        self.required_players = 8
        self.max_instances = 2

    def __str__(self):
        role_str = "Mason"
        if self.doppelganger:
            role_str += " (Doppelganger)"
        return role_str

    def get_night_action_info(self, player_sid, player_roles, mayor, word):
        logging.debug(f'Processing for {player_sid} in night action')
        for p in player_roles:
            if (self != player_roles[p] and
                    isinstance(player_roles[p], Mason)):
                self.known_players[p] = str(player_roles[p])
        logging.debug(f'Attempting to set night action for {player_sid}')
        return super().get_night_action_info(player_sid, player_roles, mayor, word)


class Esper(Role):
    def __init__(self, doppelganger=False):
        super().__init__(doppelganger=doppelganger)
        self.description = """
        The Esper. You can let someone know you're the esper without knowing
        their role. They'll see you and your role during the night phase.
        """
        self.image_name = 'esper.png'
        self.required_players = 5
        self.targetting_role = True
        self.night_action_description = """
        Target a player with whom to send your telepathic communication. They
        will see you in their mind's eye as a Village-aligned Esper.
        """

    def __str__(self):
        role_str = "Esper"
        if self.doppelganger:
            role_str += " (Doppelganger)"
        return role_str

    def _role_night_action(self, player_sid, target_sid, player_roles):
        if target_sid in player_roles:
            player_roles[target_sid].add_known_role(player_sid, str(self))


DEFAULT_ROLES_BY_PLAYER_COUNT = {
    '3':
    [
        Villager(),
        FortuneTeller(),
        Werewolf()
    ],
    '4':
    [
        Villager(),
        Apprentice(),
        FortuneTeller(),
        Werewolf()
    ],
    '5':
    [
        Villager(),
        Villager(),
        Apprentice(),
        Seer(),
        Werewolf()
    ],
    '6':
    [
        Villager(),
        Villager(),
        Villager(),
        Apprentice(),
        Seer(),
        Werewolf()
    ],
    '7':
    [
        Villager(),
        Villager(),
        Villager(),
        Villager(),
        Apprentice(),
        Seer(),
        Werewolf()
    ],
    '8':
    [
        Villager(),
        Villager(),
        Villager(),
        Villager(),
        Apprentice(),
        Seer(),
        Werewolf(),
        Werewolf()
    ],
    '9':
    [
        Villager(),
        Villager(),
        Villager(),
        Villager(),
        Esper(),
        Apprentice(),
        Seer(),
        Werewolf(),
        Werewolf()
    ],
    '10':
    [
        Villager(),
        Villager(),
        Villager(),
        Villager(),
        Villager(),
        Esper(),
        Apprentice(),
        Seer(),
        Werewolf(),
        Werewolf()
    ],
    '11':
    [
        Villager(),
        Villager(),
        Villager(),
        Villager(),
        Villager(),
        Beholder(),
        Apprentice(),
        Seer(),
        Werewolf(),
        Werewolf(),
        Werewolf()
    ],
    '12':
    [
        Villager(),
        Villager(),
        Villager(),
        Villager(),
        Villager(),
        Villager(),
        Beholder(),
        Apprentice(),
        Seer(),
        Werewolf(),
        Werewolf(),
        Werewolf()
    ],
    '13':
    [
        Villager(),
        Villager(),
        Villager(),
        Villager(),
        Villager(),
        Villager(),
        Mason(),
        Mason(),
        Apprentice(),
        Seer(),
        Werewolf(),
        Werewolf(),
        Werewolf()
    ],
    '14':
    [
        Villager(),
        Villager(),
        Villager(),
        Villager(),
        Villager(),
        Villager(),
        Villager(),
        Mason(),
        Mason(),
        Apprentice(),
        Seer(),
        Werewolf(),
        Werewolf(),
        Werewolf()
    ],
    '15':
    [
        Villager(),
        Villager(),
        Villager(),
        Villager(),
        Villager(),
        Villager(),
        Villager(),
        Mason(),
        Mason(),
        Apprentice(),
        Seer(),
        Werewolf(),
        Werewolf(),
        Werewolf(),
        FortuneTeller()
    ],
    '16':
    [
        Villager(),
        Villager(),
        Villager(),
        Villager(),
        Villager(),
        Villager(),
        Villager(),
        Mason(),
        Mason(),
        Apprentice(),
        Seer(),
        Werewolf(),
        Werewolf(),
        Werewolf(),
        FortuneTeller(),
        Beholder()
    ],
    '17':
    [
        Villager(),
        Villager(),
        Villager(),
        Villager(),
        Villager(),
        Villager(),
        Villager(),
        Mason(),
        Mason(),
        Apprentice(),
        Seer(),
        Werewolf(),
        Werewolf(),
        Werewolf(),
        FortuneTeller(),
        Beholder(),
        Esper()
    ],
    '18':
    [
        Villager(),
        Villager(),
        Villager(),
        Villager(),
        Villager(),
        Villager(),
        Villager(),
        Villager(),
        Mason(),
        Mason(),
        Apprentice(),
        Seer(),
        Werewolf(),
        Werewolf(),
        Werewolf(),
        FortuneTeller(),
        Beholder(),
        Esper()
    ],
    '19':
    [
        Villager(),
        Villager(),
        Villager(),
        Villager(),
        Villager(),
        Villager(),
        Villager(),
        Villager(),
        Mason(),
        Mason(),
        Apprentice(),
        Seer(),
        Minion(),
        Werewolf(),
        Werewolf(),
        Werewolf(),
        FortuneTeller(),
        Beholder(),
        Esper()
    ],
    '20':
    [
        Villager(),
        Villager(),
        Villager(),
        Villager(),
        Villager(),
        Villager(),
        Villager(),
        Villager(),
        Mason(),
        Mason(),
        Apprentice(),
        Seer(),
        Minion(),
        Werewolf(),
        Werewolf(),
        Werewolf(),
        FortuneTeller(),
        Beholder(),
        Esper(),
        Doppelganger()
    ],
}
