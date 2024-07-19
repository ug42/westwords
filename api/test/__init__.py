# test module for westwords

import westwords

from .functional_test import testWestwordsFunctional
from .game_test import (testGameControlFunctions, testGameFunctions,
                        testPlayerControlFunctions, testQuestionFunctions,
                        testWestwordsInteraction, testEndOfGameFunctions)
from .role_test import testWestwordsRoles
