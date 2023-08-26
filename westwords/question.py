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
        self.deleted = False
        self.answer = None

    def __str__(self):
        return f'Question: {self.question_text} -- player: {self.player_sid}'

    def __repr__(self):
        return f'Question({self.player_sid}, {self.question_text})'

    def get_answer(self):
        if self.answer:
            return self.answer.name
        return None
    
    def mark_deleted(self):
        if not self.answer:
            self.deleted = True

    def is_deleted(self):
        return self.deleted

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
