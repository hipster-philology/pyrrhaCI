from ..proto import RuleStatic, Line, Types
from typing import Optional, List
import regex as re

_VERBALLEMMA = re.compile(r".*(er|ir|oir|re)\d?$")

_ADJ = {"ADJqua", "ADJind", "ADJcar", "ADJord", "ADJpos"}
_VER = {"VERcjg", "VERinf", "VERppe", "VERppa"}
_DET = {"DETdef", "DETndf", "DETdem", "DETpos", "DETind", "DETcar", "DETrel", "DETint", "DETcom"}

### DETERMINANTS ET PRONOMS

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
        if line["token"] in ["le", "la", "les", "l'", "l"] and (line["lemma"] != "il" or line["POS"] != "PROper"):
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


class LeLaLesDet(RuleStatic):
    """ Documentation HERE

    """
    MESSAGE = "Le devant une forme nominale est généralement DETdef"
    TYPE = Types.Warn

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
        if line["token"] in ["le", "la", "les", "l'", "l"] and (line["lemma"] != "le" or line["POS"] != "DETdef"):
            return True

    @staticmethod
    def check(line: Line, previous: Optional[List[Line]] = None, following: Optional[List[Line]] = None):
        """ False means it fails.

        >>> LeLaLesDet.check({"token": "la", "lemma": "le", "POS": "PROper"}, following=[{"POS": "PROper"}])
        False
        >>> LeLaLesDet.check({"token": "la", "lemma": "le", "POS": "PROper"}, following=[{"POS": "NOMcom"}])
        True

        """
        for line in following[:1]:
            if line["POS"] not in _ADJ|{"NOMcom", "NOMpro", "PROind", "PROcar", "PROpos", "PROord"
                                   "VERppe", "VERppa"} and line["lemma"] not in ("plus"):
                return False
        return True


class TotPredet(RuleStatic):
    """ Checks that «tot» or «trestot» before determiner is tagged as «prédeterminant»

    """
    MESSAGE = "tot ou trestot devant un déterminant est généralement un prédéterminant (DETind)"
    TYPE = Types.Warn

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


#### VERBES

class VerbalLemma(RuleStatic):
    """ Checks the lemma of verbal POS (must end in -er, -ir, -oir, -re).
    """
    MESSAGE = "Lemme verbal bizarre: le lemme d'un VER* est un infinitif"
    TYPE = Types.Warn

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
    TYPE = Types.Warn

    @staticmethod
    def applies_to(line):
        """ Check that the line is to be considered for tests.

        >>> VerbalInf.applies_to({"token": "chanter", "lemma": "chanter", "POS": "VERinf"})
        True
        >>> VerbalInf.applies_to({"token": "chantoit", "lemma": "chanter", "POS": "VERcjg"})
        False

        """
        if line["POS"] == ["VERinf"]:
            return True

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

### Not converted from utils_etiquetage_verification.xsl
### - syntactic checks: mais1 et autres CONsub en tête de proposition, etc.
