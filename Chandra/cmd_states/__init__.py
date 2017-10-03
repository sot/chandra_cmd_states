# Licensed under a 3-clause BSD style license - see LICENSE.rst
from .cmd_states import *
from .get_cmd_states import fetch_states

__version__ = '3.12'


def test(*args, **kwargs):
    '''
    Run py.test unit tests.
    '''
    import testr
    return testr.test(*args, **kwargs)
