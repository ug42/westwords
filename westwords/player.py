from .enums import AnswerToken

class Player(object):
    """Simple class for player.
    
    Args:
        name: A string for the username of the player.
        game: An optional string for the current game name.
    """

    def __init__(self, name, game=None):
        self.name = name
        self.rooms = []
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

    def join_room(self, room: str):
        if room not in self.rooms:
            self.rooms.append(room)
        return True

    def leave_room(self, room: str):
        if room in self.rooms:
            self.rooms.remove(room)
            return True
        return False

    def get_rooms(self):
        return self.rooms