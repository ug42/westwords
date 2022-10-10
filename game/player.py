from .enums import AnswerToken

class Player(object):
    """Simple class for player.
    
    Args:
        name: A string for the username of the player.
        game: An optional string for the current game name.
    """

    def __init__(self, name, game=None):
        self.name = name
        self.game = game
        self.tokens = {
            AnswerToken.CORRECT: 0,
            AnswerToken.YES: 0,
            AnswerToken.NO: 0,
            AnswerToken.MAYBE: 0,
            AnswerToken.SO_CLOSE: 0,
            AnswerToken.SO_FAR: 0,
            AnswerToken.CORRECT: 0,
            AnswerToken.LARAMIE: 0,
        }

    def __repr__(self):
        return f'Player({self.name}, {self.game})'

    def __str__(self):
        return f'Player name: {self.name}, in game id: {self.game}'

    def add_token(self, token):
        # Add a token of a given enum value to this player's total
        self.tokens[token] += 1