# Licensed under a 3-clause BSD style license - see LICENSE.rst
import ska_helpers
from .cmd_states import *
from .get_cmd_states import fetch_states

__version__ = ska_helpers.get_version('chandra_cmd_states')


def test(*args, **kwargs):
    '''
    Run py.test unit tests.
    '''
    import testr
    return testr.test(*args, **kwargs)
