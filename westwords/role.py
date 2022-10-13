from enum import Enum


class Affiliation(Enum):
    WEREWOLF = 'werewolf'
    VILLAGE = 'village'
    # To be determined in course of game
    UNKNOWN = 'unknown'


class Role(object):
    def __init__(self):
        self.description = 'Generic night action, no vote ability.'
        self.see_word = False
        self.wins_with = Affiliation.VILLAGE

    def guess_seer(self, player_sid):
        pass

    def guess_werewolf(self, player_sid):
        pass


class Mayor(Role):
    def __init__(self):
        self.description = """
        Mayor picks the word from a list, and tries to answer questions in a way
        that suits their role, choosing from the "tokens" available. Mayor also
        gets a role for the night phase, but can only be one of a few selected
        roles:

        A Werewolf Mayor: Wins with the Werewolf team.
        A Villager Mayor: Wins with the Village.
        A Seer Mayor: Wins with the village, but may choose from a larger set of
        words since no Seer will be able to help. Extra words do not come into
        play if an Apprentice is in play.
        """
        self.sees_word = True
        self.wins_with = Affiliation.UNKNOWN


class Doppelganger(Role):
    def __init__(self):
        super().__init__()
        self.description = """
        Doppelganger chooses a player to see their role, and inherits that
        player's ability and alignment.
        """


class Spectator(Role):
    def __init__(self):
        self.description = """
        Not a player, no votes, but can see the word and player roles. (Maybe)
        """
        self.sees_word = True
        self.wins_with = Affiliation.UNKNOWN


class Werewolf(Role):
    def __init__(self):
        super().__init__()
        self.description = """
        Tries to lead guesses away from the word. Sees word and other
        werewolves, but not minion.
        """
        self.sees_word = True
        self.wins_with = Affiliation.WEREWOLF


class Villager(Role):
    def __init__(self):
        super().__init__()
        self.description = """
        Ordinary villager. Asks questions, tries to guess word. Wins with
        Village team.
        """


class Seer(Villager):
    def __init__(self):
        super().__init__()
        self.description = """
        Village-aligned but sees the word. If the Werewolves find and choose to
        execute this player after the Village teams guesses the word, the
        Werewolf team wins.
        """


class Apprentice(Villager):
    def __init__(self):
        super().__init__()
        # Will only see word if Mayor is Seer
        self.description = """
        Ordinary villager unless the Mayor is a Seer, in which case, they become
        the Seer. Werewolves executing the Apprentice is only a win condition if
        the Mayor is a Seer.
        """
        self.sees_word = False


class FortuneTeller(Villager):
    def __init__(self):
        super().__init__()
        self.description = """
        Village team player. Sees the first letter of each word. Werewolf team
        wins if they find the Fortune Teller or the Seer.
        """
        self.sees_word = False


class Minion(Werewolf):
    def __init__(self):
        super().__init__()
        self.description = """
        Werewolf-aligned character that doesn't get seen by Werewolves. Village
        team still wins if executing the Minion.

        Does not vote with Werewolves to find the Seer.
        """


class Beholder(Villager):
    def __init__(self):
        super().__init__()
        self.description = """
        Villager who knows the players with the Apprentice, Seer and Fortune
        Teller roles.
        """


class Mason(Villager):
    def __init__(self):
        super().__init__()
        self.description = """
        Villager who happens to know which players are the other Masons.
        """


class Thing(Villager):
    def __init__(self):
        super().__init__()
        self.description = """
        Villager who lets their neighbor know they're not a Werewolf by 
        "tapping their shoulder."
        """