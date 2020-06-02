from typing import Optional, List
import regex as re
from pyrrha_ci.rules.proto import RuleStatic, Line
from pyrrha_ci.utils import MESSAGE_TYPE

_VERBALLEMMA = re.compile(r".*(er|ir|oir|re)\d?$")
_VER = {"VERcjg", "VERinf", "VERppe", "VERppa"}


class VerbalLemma(RuleStatic):
    """ Checks the lemma of verbal POS (must end in -er, -ir, -oir, -re).
    """
    MESSAGE = "Lemme verbal bizarre: le lemme d'un VER* est un infinitif"
    TYPE = MESSAGE_TYPE.WARNING

    @staticmethod
    def applies_to(line):
        """ Check that the line is to be considered for tests.

        >>> VerbalLemma.applies_to({"token": "chantant", "lemma": "chantant", "POS": "VERppa"})
        True
        >>> VerbalLemma.applies_to({"token": "chantoit", "lemma": "chanter", "POS": "VERcjg"})
        True

        """
        if line["POS"] in _VER:
            return True

    @staticmethod
    def check(line: Line, previous: Optional[List[Line]] = None, following: Optional[List[Line]] = None):
        """ False means it fails.

        >>> VerbalLemma.check({"token": "chantant", "lemma": "chantant", "POS": "VERppa"})
        False
        >>> VerbalLemma.check({"token": "chantoit", "lemma": "chanter", "POS": "VERcjg"})
        True

        """
        if not _VERBALLEMMA.match(line["lemma"]):
            return False
        return True


class VerbalInf(RuleStatic):
    """ Checks that VERinf actually are

    """
    MESSAGE = "Forme du VERinf bizarre"
    TYPE = MESSAGE_TYPE.WARNING

    @staticmethod
    def applies_to(line):
        """ Check that the line is to be considered for tests.

        >>> VerbalInf.applies_to({"token": "chanter", "lemma": "chanter", "POS": "VERinf"})
        True
        >>> VerbalInf.applies_to({"token": "chantoit", "lemma": "chanter", "POS": "VERcjg"})
        False

        """
        return line["POS"] == "VERinf"

    @staticmethod
    def check(line: Line, previous: Optional[List[Line]] = None, following: Optional[List[Line]] = None):
        """ False means it fails.

        >>> VerbalInf.check({"token": "chantant", "lemma": "chanter", "POS": "VERinf"})
        False
        >>> VerbalInf.check({"token": "chanter", "lemma": "chanter", "POS": "VERinf"})
        True

        """
        if not _VERBALLEMMA.match(line["token"]):
            return False
        return True
