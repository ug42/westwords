from enum import Enum


class Affiliation(Enum):
    WEREWOLF = 'werewolf'
    VILLAGE = 'village'
    # To be determined in course of game
    UNKNOWN = 'unknown'


class Role(object):
    def __init__(self):
        see_word = False
        wins_with = Affiliation.VILLAGE

    def guess_seer(self, player_sid):
        pass

    def guess_werewolf(self, player_sid):
        pass


class Mayor(Role):
    def __init__(self):
        sees_word = True
        wins_with = Affiliation.UNKNOWN


class Spectator(Role):
    def __init__(self):
        sees_word = True
        wins_with = Affiliation.UNKNOWN

class Werewolf(Role):
    def __init__(self):
        super().__init__()
        see_word = True
        wins_with = Affiliation.WEREWOLF


class Villager(Role):
    def __init__(self):
        super().__init__()


class Seer(Villager):
    def __init__(self):
        super().__init__()


class Apprentice(Villager):
    def __init__(self):
        super().__init__()
        # Will only see word if Mayor is Seer
        sees_word = False