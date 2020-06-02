from typing import Optional, List

from pyrrha_ci.rules.proto import RuleStatic, Line
from pyrrha_ci.utils import MESSAGE_TYPE

_ADJ = {"ADJqua", "ADJind", "ADJcar", "ADJord", "ADJpos"}
_DET = {"DETdef", "DETndf", "DETdem", "DETpos", "DETind", "DETcar", "DETrel", "DETint", "DETcom"}


class LeLaLesPro(RuleStatic):
    """ Documentation HERE

    """
    MESSAGE = "Le devant un verbe est généralement PROper"
    TYPE = MESSAGE_TYPE.WARNING

    @staticmethod
    def applies_to(line):
        """ Check that the line is to be considered for tests.

        >>> LeLaLesPro.applies_to({"token": "la", "lemma": "le", "POS": "PROper"})
        True
        >>> LeLaLesPro.applies_to({"token": "la", "lemma": "il", "POS": "PROper"})
        False

        """
        return line["token"] in ["le", "la", "les", "l'", "l"] and (line["lemma"] != "il" or line["POS"] != "PROper")

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


class LeLaLesDet(RuleStatic):
    """ Documentation HERE

    """
    MESSAGE = "Le devant une forme nominale est généralement DETdef"
    TYPE = MESSAGE_TYPE.WARNING

    _WrongPos = _ADJ | {"NOMcom", "NOMpro", "PROind", "PROcar", "PROpos", "PROord"
                                   "VERppe", "VERppa"}

    @staticmethod
    def applies_to(line):
        """ Check that the line is to be considered for tests.

        >>> LeLaLesDet.applies_to({"token": "la", "lemma": "le", "POS": "PROper"})
        True
        >>> LeLaLesDet.applies_to({"token": "la", "lemma": "il", "POS": "PROper"})
        True
        >>> LeLaLesDet.applies_to({"token": "la", "lemma": "le", "POS": "DETdef"})
        False

        """
        return line["token"] in ["le", "la", "les", "l'", "l"] and (line["lemma"] != "le" or line["POS"] != "DETdef")

    @staticmethod
    def check(line: Line, previous: Optional[List[Line]] = None, following: Optional[List[Line]] = None):
        """ False means it fails.

        >>> LeLaLesDet.check({"token": "la", "lemma": "le", "POS": "PROper"}, following=[{"POS": "PROper", "lemma": "a"}])
        False
        >>> LeLaLesDet.check({"token": "la", "lemma": "le", "POS": "PROper"}, following=[{"POS": "NOMcom", "lemma": "b"}])
        True

        """
        for line in following[:1]:
            if line["POS"] not in LeLaLesDet._WrongPos and line["lemma"] not in {"plus"}:
                return False
        return True


class TotPredet(RuleStatic):
    """ Checks that «tot» or «trestot» before determiner is tagged as «prédeterminant»

    """
    MESSAGE = "tot ou trestot devant un déterminant est généralement un prédéterminant (DETind)"
    TYPE = MESSAGE_TYPE.WARNING

    @staticmethod
    def applies_to(line):
        """ Check that the line is to be considered for tests.

        >>> TotPredet.applies_to({"token": "tuit", "lemma": "tot", "POS": "DETind"})
        False
        >>> TotPredet.applies_to({"token": "trestot", "lemma": "trestot", "POS": "ADVgen"})
        True
        >>> TotPredet.applies_to({"token": "chanter", "lemma": "chanter", "POS": "VERinf"})
        False

        """
        if line["lemma"] in ["tot", "trestot"] and (line["POS"] != "DETind"):
            return True

    @staticmethod
    def check(line: Line, previous: Optional[List[Line]] = None, following: Optional[List[Line]] = None):
        """ False means it fails.

        >>> TotPredet.check({"token": "tuit", "lemma": "tot", "POS": "DETind"})
        True
        >>> TotPredet.check({"token": "trestot", "lemma": "trestot", "POS": "ADVgen"})
        False

        """
        for line in following[:1]:
            if line["POS"] not in _DET:
                return False
        return True