import re
import typing

from westwords.enums import AnswerToken


ARTICLES = [
    'a',
    'an',
    'the',
]

PRONOUNS = [
  'i',
  'you',
  'my',
  'mine',
  'myself'
  'we',
  'us',
  'our',
  'ours',
  'ourselves'
  'you',
  'you',
  'your',
  'yours',
  'yourself'
  'you',
  'you',
  'your',
  'your',
  'yourselves'
  'he',
  'him',
  'his',
  'his',
  'himself'
  'she',
  'her',
  'her',
  'her',
  'herself'
  'it',
  'it',
  'its',
  'itself'
  'they',
  'them',
  'their',
  'theirs',
  'themself'
  'they',
  'them',
  'their',
  'theirs',
  'themselves'
]

REMOVAL = ARTICLES + PRONOUNS

class QuestionError(BaseException):
    """Simple exception class for Question objects."""
    pass


class Question(object):
    """Simple question construct for named variables"""

    def __init__(self, player_sid: str, question_text: str):
        self.player_sid = player_sid
        self.question_text = question_text
        self.deleted = False
        self.answer = None
        self.skipped = False

    def __str__(self) -> str:
        return f'{self.question_text}'

    def __repr__(self) -> str:
        return f'Question({self.player_sid}, {self.question_text})'

    @property
    def text_match_regex(self) -> re.Pattern:
        # Strip newlines, casefold to lower case, and remove special characters
        question_string = self.question_text.strip().casefold()
        question_string = re.sub(r'[^\w]', ' ', question_string)

        # generate ordered list of only core sentence elements
        components = [i for i in question_string.split() if i not in REMOVAL]
        
        # Return a _very_ loose regex on sentence structure.
        return re.compile('.*'.join(components), re.IGNORECASE)

    def get_answer(self) -> typing.Optional[AnswerToken]:
        if self.answer:
            return self.answer
        return None

    def mark_deleted(self) -> None:
        if not self.answer:
            self.deleted = True

    def is_deleted(self) -> bool:
        return self.deleted

    def is_skipped(self) -> bool:
        return self.skipped

    def answer_question(self, answer: AnswerToken) -> bool:
        """Sets the answer for this question."""
        if not self.deleted:
            self.answer = answer
            return True
        return False

    def skip_question(self) -> None:
        if not self.deleted:
            self.skipped = True

    def clear_answer(self) -> AnswerToken:
        """Simple method to clear the currently assigned AnswerToken.

        Returns:
            Previously-set AnswerToken for this question.
        """
        if self.answer:
            previous_answer = self.answer
            self.answer = None
            return previous_answer
        elif self.skipped:
            # undo the skipping, but don't credit anyone with a token
            self.skipped = False
            return None
        else:
            # Assume another state not accounted for here.
            return None
