class Player(object):
    def __init__(self) -> None:
        self.role = None


class Role(object):
    def __init__(self) -> None:
        pass


class Werewolf(Role):
    def __init__(self) -> None:
        super().__init__()

    def guessSeer(self, user):
        pass


class Villager(Role):
    def __init__(self) -> None:
        super().__init__() 

    def guessWerewolf(self, user):
        pass

    