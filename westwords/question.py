from html import escape

from westwords.enums import AnswerToken


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

    def get_answer(self):
        if self.answer:
            return self.answer.name
        return None

    def _html_format(self):
        """Provides a baseline HTML format for the question."""
        # id and player name are held outside this scope.
        return ('<div class="question"'
                'id="q{id}">'
                '{player_name}'
                f': {escape(self.question_text)}'
                '<div id="q{id}a" style="display: inline">')

    def html_format(self):
        # This should be the actual name of answer.
        # TODO: move this to be an image with alt text.
        if self.answer:
            answer = self.answer.name
        else:
            answer = ''
        return self._html_format() + f'({answer})</div>'

    def mayor_html_format(self):
        # TODO: Move these all to be images greyed out with alt-text and
        # mouseover highlight to non-greyed out image
        if not self.answer:
            return self._html_format() + HTML_ANSWER_TEMPLATE
        else:
            return self.html_format()

    def answer_question(self, answer: AnswerToken):
        """Sets the answer for this question."""
        self.answer = answer

    def clear_answer(self):
        """Simple method to clear the currently assigned AnswerToken.

        Returns:
            Previously-set AnswerToken for this question.
        """
        previous_answer = self.answer
        self.answer = None
        return previous_answer
