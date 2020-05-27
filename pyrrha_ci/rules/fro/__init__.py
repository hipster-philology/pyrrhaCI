from ..proto import RuleStatic, Line, Types
from typing import Optional, List


class LeLaLesPro(RuleStatic):
    """ Documentation HERE

    """
    MESSAGE = "Le devant un verbe est généralement PROper"
    TYPE = Types.Warn

    @staticmethod
    def applies_to(line):
        """ Check that the line is to be considered for tests.

        >>> LeLaLesPro.applies_to({"token": "la", "lemma": "le", "POS": "PROper"})
        True
        >>> LeLaLesPro.applies_to({"token": "la", "lemma": "il", "POS": "PROper"})
        False

        """
        if line["token"] in ["le", "la", "les", "l'"] and (line["lemma"] != "il" or line["POS"] != "PROper"):
            return True

    @staticmethod
    def check(line: Line, previous: Optional[List[Line]] = None, following: Optional[List[Line]] = None):
        """ False means it fails.

        >>> LeLaLesPro.check({"token": "la", "lemma": "le", "POS": "PROper"}, following=[{"POS": "PROper"}])
        False
        >>> LeLaLesPro.check({"token": "la", "lemma": "le", "POS": "PROper"}, following=[{"POS": "NOMcom"}])
        True

        """
        for line in following[:1]:
            if line["POS"] not in ("VERcjg", "VERinf", "PROper"):
                return False
        return True

