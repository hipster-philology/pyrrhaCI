import os
from enum import Enum
from typing import Union, TextIO, Generator, Tuple, Dict


class MESSAGE_TYPE(Enum):
    INFO = '\033[94m'
    OK = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    IGNORE = '\033[94m'


def parse_tsv(content: Union[str, TextIO]) -> Generator[Tuple[int, Dict[str, str]], None, None]:
    """ Parses a Pyrrha TSV

    :param content: Path to the file
    :yield: Yields the line number and the content
    """
    if isinstance(content, str):
        content = open(content)
    header = []
    for line_no, line in enumerate(content):
        if line_no == 0:
            header = line.strip().split("\t")
        else:
            yield line_no, dict(zip(header, line.strip().split("\t")))
    content.close()
    return None


def merge(source, destination):
    """Merges b into a

    Source: https://stackoverflow.com/questions/20656135/python-deep-merge-dictionary-data

    >>> a = { 'first' : { 'all_rows' : { 'pass' : 'dog', 'number' : '1' } } }
    >>> b = { 'first' : { 'all_rows' : { 'fail' : 'cat', 'number' : '5' } } }
    >>> merge(b, a) == { 'first' : { 'all_rows' : { 'pass' : 'dog', 'fail' : 'cat', 'number' : '5' } } }
    True
    """
    for key, value in source.items():
        if isinstance(value, dict):
            # get node or create one
            node = destination.setdefault(key, {})
            merge(value, node)
        else:
            destination[key] = value
    return destination


def _relative_path(first_file: str, second_file: str):
    """ Compute a relative path based on the path of the first
    file """
    return os.path.join(
        os.path.dirname(first_file),
        second_file
    )