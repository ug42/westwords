from enum import Enum, auto

class GameState(Enum):
    SETUP = auto()
    # Doppelganger/Esper action and Mayor Word Choice
    NIGHT_PHASE_WORD_CHOICE = auto()
    NIGHT_PHASE_DOPPELGANGER = auto()
    NIGHT_PHASE_TARGETTING = auto()
    # Reveal all known roles and words or word portions
    NIGHT_PHASE_REVEAL = auto()
    DAY_PHASE_QUESTIONS = auto()
    VOTING = auto()
    FINISHED = auto()


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
    WEREWOLF = "Werewolf"
    VILLAGE = "Village"
    # To be determined in course of game
    UNKNOWN = "Unknown"