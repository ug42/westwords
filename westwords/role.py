from westwords.enums import Affiliation

class Role(object):
    def __init__(self):
        self.description = "Generic night action, no vote ability."
        self.affiliation = Affiliation.VILLAGE
        self.known_players = {}
        self.max_instances = 1
        self.required = False
        self.required_players = 0
        self.sees_word = False
        self.targetted_player = None
        self.night_phase_complete = False
        self.targetting_role = False
        self.team_loses_if_killed = False
        self.votes_on_guessed_word = False

    def __str__(self):
        return type(self).__name__

    def get_max_instances(self):
        return self.max_instances
    
    def is_required(self):
        return self.required
    
    def get_required_players(self):
        return self.required_players

    def target_player(self, player_sid):
        if self.targetting_role:
            self.targetted_player = player_sid
            return True
        return False

    def get_known_players(self):
        return self.known_players


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
        play if an Intern is in play.
        """
        self.sees_word = True
        self.affiliation = Affiliation.UNKNOWN
        self.required = True

    def __str__(self):
        return "Mayor"


class Doppelganger(Role):
    def __init__(self):
        super().__init__()
        self.description = """
        Doppelganger chooses a player to see their role, and inherits that
        player's ability and alignment.
        """
        self.affiliation = Affiliation.UNKNOWN
        self.required_players = 4
        self.targetting_role = True

    def __str__(self):
        return "Doppelganger"



class Werewolf(Role):
    def __init__(self):
        super().__init__()
        self.description = """
        Tries to lead guesses away from the word. Sees word and other
        werewolves, but not minion.
        """
        self.max_instances = 4
        self.required = True
        self.required_players = 0
        self.sees_word = True
        self.team_loses_if_killed = True
        self.votes_on_guessed_word = True
        self.affiliation = Affiliation.WEREWOLF
    
    def __str__(self):
        return "Werewolf"


class Villager(Role):
    def __init__(self):
        super().__init__()
        self.description = """
        Ordinary villager. Asks questions, tries to guess word. Wins with
        Village team.
        """
        self.required_players = 3
        self.max_instances = 8
        
    
    def __str__(self):
        return "Villager"


class Seer(Villager):
    def __init__(self):
        super().__init__()
        self.description = """
        Village-aligned but sees the word. If the Werewolves find and choose to
        execute this player after the Village teams guesses the word, the
        Werewolf team wins.
        """
        self.required = True
        self.required_players = 0
        self.team_loses_if_killed = True

    def __str__(self):
        return "Seer"


class Intern(Villager):
    def __init__(self):
        super().__init__()
        # Will only see word if Mayor is Seer
        self.description = """
        Ordinary villager unless the Mayor is a Seer, in which case, they become
        the Seer. Werewolves executing the Intern is only a win condition if
        the Mayor is a Seer.
        """
        self.sees_word = False
        self.required_players = 5
        # This will be set to true if Mayor is the Seer.
        self.team_loses_if_killed = False

    def __str__(self):
        return "Intern"


class FortuneTeller(Villager):
    def __init__(self):
        super().__init__()
        self.description = """
        Village team player. Sees the first letter of each word. Werewolf team
        wins if they find the Fortune Teller or the Seer.
        """
        self.sees_word = False
        self.required_players = 5
        self.team_loses_if_killed = True

    def __str__(self):
        return "Fortune Teller"


class Minion(Werewolf):
    def __init__(self):
        super().__init__()
        self.description = """
        Werewolf-aligned character that doesn't get seen by Werewolves. Village
        team still wins if executing the Minion.

        Does not vote with Werewolves to find the Seer/Fortune Teller.
        """
        self.sees_word = False
        self.required_players = 7
        self.team_loses_if_killed = True
        self.votes_on_guessed_word = False

    def __str__(self):
        return "Minion"


class Beholder(Villager):
    def __init__(self):
        super().__init__()
        self.description = """
        Villager who knows the players with the Intern, Seer and Fortune
        Teller roles. Does not lose on being targetted by Werewolves. Otherwise
        known as the villager who know too much.
        """
        self.required_players = 5
    
    def __str__(self):
        return "Beholder"


class Mason(Villager):
    def __init__(self):
        super().__init__()
        self.description = """
        Villager who happens to know which players are the other Masons.
        """
        self.required_players = 8
        self.max_instances = 2


    def __str__(self):
        return "Mason"


class Esper(Villager):
    def __init__(self):
        super().__init__()
        self.description = """
        Villager who lets their neighbor know they're not a Werewolf by 
        sending good vibes to another person.
        """
        self.required_players = 5
        self.targetting_role = True

    def __str__(self):
        return "Esper"
