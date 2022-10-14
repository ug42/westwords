from html import escape

from westwords.enums import AnswerToken


HTML_ANSWER_TEMPLATE = """
<div id="answers_{id}" style="display: inline">
<button class="answer" onclick="answer({id}, 'yes')" hidden>Yes</button>
<button class="answer" onclick="answer({id}, 'no')" hidden>No</button>
<button class="answer" onclick="answer({id}, 'maybe')" hidden>Maybe</button>
<button class="answer" onclick="answer({id}, 'so_close')" hidden>So Close</button>
<button class="answer" onclick="answer({id}, 'so_far')" hidden>Very far off</button>
<button class="answer" onclick="answer({id}, 'correct')" hidden>Correct!</button>
</div>
</div>
"""

class QuestionError(BaseException):
    """Simple exception class for Question objects."""
    pass


class Question(object):
    """Simple question construct for named variables"""

    def __init__(self, player_sid, question_text):
        self.player_sid = player_sid
        self.question_text = question_text
        self.answer = None

    def __str__(self):
        return f'Question: {self.question_text} -- player: {self.player_sid}'

    def __repr__(self):
        return f'Question({self.player_sid}, {self.question_text})'

    def html_format(self):
        if self.answer:
            # This should be the actual name of answer.
            # TODO: move this to be an image with alt text.
            answer_html = self.answer.name + '</div>'
        else:
            # TODO: Move these all to be images greyed out with alt-text and
            # mouseover highlight to non-greyed out image
            answer_html = HTML_ANSWER_TEMPLATE
        # id and player name are held outside this scope.
        return ('<div class="question"'
                'id="q{id}">'
                '{player_name}'
                f': {escape(self.question_text)}'
                '<div id="q{id}a" style="display: inline">'
                f'  ({answer_html})</div>')

    def answer_question(self, answer: AnswerToken):
        """Sets the answer for this question."""
        self.answer = answer

    def clear_answer(self):
        """Simple method to clear the currently assigned AnswerToken."""
        self.answer = None
