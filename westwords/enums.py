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
    # Form of value name, token text, and token material icon
    YES = ("yes", "Yes", "check_circle", 36)
    NO = ("no", "No", "cancel", 36)
    MAYBE = ("maybe", "Maybe", "help", 10)
    SO_CLOSE = ("so_close", "So close!", "radar")
    SO_FAR = ("so_far", "Very far off!", "delete_forever")
    LARAMIE = ("laramie", "Very troll-y.", "trolley")
    BRONEY = ("broney", "Maybe, but let's not go there.", "sentiment_neutral")
    CORRECT = ("correct", "Correct!", "star")
    # MICHAEL = ("michael", "" "")
    # JOHANNA = ("johanna", "" "")
    # MATT = ("matt", "" "")
    # NONE = ("")

    def __new__(cls, *args, **_):
        obj = object.__new__(cls)
        obj._value_ = args[0]
        return obj

    def __init__(self,
                 _: str,
                 token_text: str = None,
                 token_icon: str = None,
                 default_count: int = 1,
                 ):
        self._token_text_ = token_text
        self._token_icon_ = token_icon
        self._default_count = default_count

    @property
    def token_text(self):
        return self._token_text_

    @property
    def token_icon(self):
        return self._token_icon_
    
    @property
    def default_count(self):
        return self._default_count


class Affiliation(Enum):
    WEREWOLF = "Werewolf"
    VILLAGE = "Village"
    # To be determined in course of game
    UNKNOWN = "Unknown"
