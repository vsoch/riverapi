__author__ = "Vanessa Sochat"
__copyright__ = "Copyright 2022, Vanessa Sochat"
__license__ = "MPL 2.0"

import os
import stat
import json


def write_file(filename, content, mode="w", exec=False):
    """
    Write content to a filename
    """
    with open(filename, mode) as filey:
        filey.writelines(content)
    if exec:
        st = os.stat(filename)
        os.chmod(filename, st.st_mode | stat.S_IEXEC)
    return filename


def write_json(json_obj, filename, mode="w"):
    """
    Write json to a filename
    """
    with open(filename, mode) as filey:
        filey.writelines(print_json(json_obj))
    return filename


def print_json(json_obj):
    """
    Print json pretty
    """
    return json.dumps(json_obj, indent=4, separators=(",", ": "))


def read_file(filename, mode="r"):
    """
    Read a file.
    """
    with open(filename, mode) as filey:
        content = filey.read()
    return content


def read_json(filename, mode="r"):
    """
    Read a json file to a dictionary.
    """
    return json.loads(read_file(filename))
