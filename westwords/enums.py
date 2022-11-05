from enum import Enum

class GameState(Enum):
    SETUP = 1
    STARTED = 2
    PAUSED = 3
    VOTING = 4
    FINISHED = 5


class AnswerToken(Enum):
    # Provides canonical tokens and mapping to buckets
    YES = "yes"
    NO = "no"
    MAYBE = "maybe"
    SO_CLOSE = "so_close"
    SO_FAR = "so_far"
    CORRECT = "correct"
    LARAMIE = "laramie"
    NONE = ""


class Affiliation(Enum):
    WEREWOLF = 'Werewolf'
    VILLAGE = 'Village'
    # To be determined in course of game
    UNKNOWN = 'Unknown'