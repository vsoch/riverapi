__author__ = "Vanessa Sochat"
__copyright__ = "Copyright 2022, Vanessa Sochat"
__license__ = "MPL 2.0"

import re


class authHeader:
    def __init__(self, lookup):
        """
        Given a dictionary of values, match them to class attributes
        """
        for key in lookup:
            if key in ["realm", "service", "scope"]:
                setattr(self, key.capitalize(), lookup[key])


def parse_auth_header(authHeaderRaw):
    """
    Parse an authentication header into relevant pieces
    """
    regex = re.compile('([a-zA-z]+)="(.+?)"')
    matches = regex.findall(authHeaderRaw)
    lookup = dict()
    for match in matches:
        lookup[match[0]] = match[1]
    return authHeader(lookup)
