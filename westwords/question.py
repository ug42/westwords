from html import escape

from westwords.enums import AnswerToken


class Question(object):
    """Simple question construct for named variables"""

    def __init__(self, player_sid, question_text):
        self.player_sid = player_sid
        self.question_text = question_text
        # TODO: change this to use the AnswerToken enum
        self.answer = None

    def __repr__(self):
        return f'Question({self.player_sid}, {self.question_text})'

    def html_format(self):
        if self.answer:
            answer_html = self.answer
        else:
            answer_html = """
<div id="answers" style="display: inline">
<button class="answer" onclick="answer({id}, 'yes')" {hidden}>Yes</button>
<button class="answer" onclick="answer({id}, 'no')" {hidden}>No</button>
<button class="answer" onclick="answer({id}, 'maybe')" {hidden}>Maybe</button>
<button class="answer" onclick="answer({id}, 'so_close')" {hidden}>So Close</button>
<button class="answer" onclick="answer({id}, 'so_far')" {hidden}>Very far off</button>
<button class="answer" onclick="answer({id}, 'correct')"  {hidden}>Correct!</button>
</div>
</div>
"""
        # id and player name are held outside this scope.
        return ('<div class="question"'
                'id="q{id}">'
                '{player_name}'
                f': {escape(self.question_text)}'
                '<div id="q{id}a" style="display: inline">'
                f'  ({answer_html})</div>')


    def clear_answer(self):
        """Simple method to clear the currently assigned AnswerToken."""
        self.answer = None
