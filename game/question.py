class Question(object):
    """Simple question construct for named variables"""

    def __init__(self, player_sid, question_text):
        self.player_sid = player_sid
        self.question_text = question_text
        # TODO: change this to use the AnswerToken enum
        self.answer = ''

    def __repr__(self):
        return f'Question({self.player_sid}, {self.question_text})'

    def html_format(self):
        # id and player name are held outside this scope.
        return ('<div class="question"'
                'id="q{id}">'
                '{player_name}'
                f': {self.question_text}'
                '<div id="q{id}a" style="display: inline">'
                f'  ({self.answer})</div></div>')