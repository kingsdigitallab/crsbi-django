import os.path
import re


FILENAME_PATTERN = re.compile(r'^(?P<prefix>[a-z]?)[0-9]+$')


def get_normalised_name (file_path):
    """Returns a normalised form of `file_path`.

    This is the basename without extension and with any prefix or
    surrounding parentheses.

    """
    name = os.path.splitext(os.path.basename(file_path))[0]
    if name[0] == '(':
        name = name[1:]
    if name[-1] == ')':
        name = name[:-1]
    match = FILENAME_PATTERN.search(name)
    if match and match.group('prefix'):
        name = name[1:]
    name = name.replace(',', '_')
    return name
