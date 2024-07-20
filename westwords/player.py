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
        self.tokens = {token: 0 for token in AnswerToken}

    def __repr__(self):
        return f'Player({self.name})'

    def __str__(self):
        return f'Player name: {self.name}'

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