import re
import typing

from westwords.enums import AnswerToken

ADVERBS = [
    'accordingly',
    'additionally',
    'also',
    'anyway',
    'besides',
    'certainly',
    'conversely',
    'finally',
    'hence',
    'however',
    'instead',
    'lately',
    'likewise',
    'moreover',
    'namely',
    'nevertheless',
    'so',
    'then',
    'yet',
    'always',
    'usually',
    'often',
    'sometimes',
    'rarely',
    'never',
    'ever',
    'hardly ever',
    'occasionally',
    'seldom',
    'generally',
    'frequently',
    'normally',
    'once',
    'twice',
    'behind',
    'above',
    'nearby',
    'backward',
    'toward',
    'outside',
    'inside',
    'around',
    'over',
    'overseas',
    'close',
    'away',
    'upstairs',
    'downstairs',
    'here',
    'there',
    'everywhere',
]

PREPOSITIONS = [
    'about',
    'above',
    'across',
    'after',
    'against',
    'along',
    'among',
    'around',
    'as',
    'at',
    'before',
    'behind',
    'below',
    'beneath',
    'beside',
    'between',
    'beyond',
    'by',
    'despite',
    'down',
    'during',
    'except',
    'for',
    'from',
    'in',
    'inside',
    'into',
    'like',
    'near',
    'of',
    'off',
    'on',
    'onto',
    'opposite',
    'out',
    'outside',
    'over',
    'past',
    'round',
    'since',
    'than',
    'through',
    'to',
    'towards',
    'under',
    'underneath',
    'unlike',
    'until',
    'up',
    'upon',
    'via',
    'with',
    'within',
    'without',
]

AUX_VERBS = [
    'is',
    'am',
    'are',
    'was',
    'were',
    'been',
    'being',
    'have',
    'has',
    'had',
    'having',
    'do',
    'does',
    'did',
    'can',
    'could',
    'shall',
    'should',
    'will',
    'would',
    'may',
    'might',
    'must',
    'dare',
    'need',
    'used to',
    'ought to',
]

ARTICLES = [
    'a',
    'an',
    'the',
]

PRONOUNS = [
    'he',
    'her',
    "her's",
    'herself',
    'him',
    'himself',
    'his',
    'i',
    'it',
    'its',
    'itself',
    'mine',
    'my',
    'myself',
    'our',
    'ours',
    'ourselves',
    'she',
    'their',
    'theirs',
    'them',
    'themself',
    'themselves',
    'they',
    'they',
    'us',
    'we',
    'you',
    'your',
    'yours',
    'yourself',
    'yourselves',
]

REMOVAL =  ADVERBS + PREPOSITIONS + AUX_VERBS + ARTICLES + PRONOUNS


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
        component_count = len(components)
        
        # Return a _very_ loose regex on sentence structure.
        # In general this any term that is not surrounded by an alphanumeric
        # character up to the number of times seen in the original question.
        # This is likely very computationally expensive, so something like RE2
        # would be nice to cut down computation costs, but that is costly to the
        # image size, as well. This might be a tradeoff that needs to happen
        # later.
        # question_regex = re.compile(rf'(.*([^\w]{"|".join(components)}[^\w]).*){{{component_count}}}', re.IGNORECASE)
        regex_string = '.*'.join(components)
        question_regex = None
        if component_count > 1 and len(regex_string) > 5:
            question_regex = re.compile(regex_string, re.IGNORECASE)

        return question_regex

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
