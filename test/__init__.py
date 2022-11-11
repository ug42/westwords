# test module for westwords

import westwords

from .functional_test import testWestwordsFunctional
from .game_test import (testGameControlFunctions, testGameFunctions,
                        testPlayerControlFunctions, testQuestionFunctions,
                        testRoleSelectionFunctions, testTokenFunctions,
                        testWestwordsInteraction)
from .role_test import testWestwordsRoles
