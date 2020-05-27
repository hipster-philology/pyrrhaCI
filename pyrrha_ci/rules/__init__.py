from typing import Dict, List, Optional, Union

Line = Dict[str, str]


def check_str(in_value: str, check_value: str):
    """ Check that `in_value` is indeed in `check_value`

    >>> check_str("Data", "Dat*")
    True
    >>> check_str("Data", "Data")
    True
    >>> check_str("Data", "Dat")
    False
    """
    if check_value.endswith("*"):
        if not in_value.startswith(check_value[:-1]):
            return False
    else:
        if in_value != check_value:
            return False
    return True


def check_list(in_value: str, check_value: List[str]):
    """ Check that `in_value` is indeed in `check_value`

    >>> check_list("Data", ["Dat*", "Couic"])
    True
    >>> check_list("Data", ["Dat", "Couic"])
    False
    """
    for sub_chek_value in check_value:
        if check_str(in_value, sub_chek_value):
            return True
    return False


class Rule(object):
    """

    """
    def __init__(self, match: Dict[str, Optional[Union[str, List]]], message: str, warning=True, **kwargs):
        self.warning: bool = warning
        self.message: str = message
        self.match = match

    def applies_to(self, line: Dict[str, str]) -> bool:
        """ Check that the current rule applies to the given line

        >>> (Rule({"lemma": "de+le"}, message="")).applies_to({"token": "du", "lemma": "de+le"})
        True
        >>> (Rule({"lemma": "dele"}, message="")).applies_to({"token": "du", "lemma": "de+le"})
        False
        """
        for cat, check in self.match.items():
            if isinstance(check, str) and not check_str(line[cat], check):
                return False
            elif isinstance(check, list) and not check_list(line[cat], check):
                return False
        return True

    def check(self, line: Line, previous: Optional[List[Line]] = None, following: Optional[List[Line]] = None):
        raise NotImplementedError()
