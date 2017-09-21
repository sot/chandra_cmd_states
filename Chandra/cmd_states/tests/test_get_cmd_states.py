# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os
import sys
import six
from six.moves import cStringIO as StringIO
import pytest

import numpy as np
from astropy.io import ascii

from Chandra.cmd_states.get_cmd_states import main, fetch_states

# This is taken from the output of
#  get_cmd_states --start=2010:100 --stop=2010:101 --vals=obsid,simpos,pcad_mode,clocking,power_cmd
# for Chandra.cmd_states version 0.07 in skare 0.13 on July 18, 2012.
LINES = [
    "datestart             datestop              tstart        tstop         obsid power_cmd  pcad_mode clocking simpos",
    "2010:100:11:39:57.675 2010:100:14:04:43.358 387286863.859 387295549.542 56340 XTZ0000005 NPNT      1        -99616",
    "2010:100:14:04:43.358 2010:100:14:24:58.675 387295549.542 387296764.859 56340 XTZ0000005 NMAN      1        -99616",
    "2010:100:14:24:58.675 2010:100:14:27:58.675 387296764.859 387296944.859 56340 AA00000000 NMAN      0        92904 ",
    "2010:100:14:27:58.675 2010:100:14:28:06.675 387296944.859 387296952.859 11979 AA00000000 NMAN      0        92904 ",
    "2010:100:14:28:06.675 2010:100:14:28:30.675 387296952.859 387296976.859 11979 WSPOW00000 NMAN      0        92904 ",
    "2010:100:14:28:30.675 2010:100:14:29:37.675 387296976.859 387297043.859 11979 WSPOW0CF3F NMAN      0        92904 ",
    "2010:100:14:29:37.675 2010:100:14:32:26.896 387297043.859 387297213.08  11979 XTZ0000005 NMAN      1        92904 ",
    "2010:100:14:32:26.896 2010:101:00:54:29.675 387297213.08  387334535.859 11979 XTZ0000005 NPNT      1        92904 ",
    "2010:101:00:54:29.675 2010:101:00:57:29.675 387334535.859 387334715.859 11979 AA00000000 NMAN      0        75624 ",
    "2010:101:00:57:29.675 2010:101:00:57:37.675 387334715.859 387334723.859 11390 AA00000000 NMAN      0        75624 ",
    "2010:101:00:57:37.675 2010:101:00:58:01.675 387334723.859 387334747.859 11390 WSPOW00000 NMAN      0        75624 ",
    "2010:101:00:58:01.675 2010:101:00:59:08.675 387334747.859 387334814.859 11390 WSPOW1EC3F NMAN      0        75624 ",
    "2010:101:00:59:08.675 2010:101:01:19:50.514 387334814.859 387336056.698 11390 XTZ0000005 NMAN      1        75624 ",
    "2010:101:01:19:50.514 2010:101:20:50:50.263 387336056.698 387406316.447 11390 XTZ0000005 NPNT      1        75624 "]

OUT = "\n".join(LINES) + "\n"
VALS = ascii.read(LINES, guess=False)


def test_get_states_main():
    """Test command line interface to getting commanded states.
    """
    cli_string = "--start=2010:100 --stop=2010:101 --vals=obsid,simpos,pcad_mode,clocking,power_cmd"
    sys.stdout = StringIO()
    main(cli_string.split())
    out = sys.stdout.getvalue()
    sys.stdout = sys.__stdout__
    assert out == OUT


# Set up possible backends
dbis = ['hdf5', 'sqlite']
if six.PY2 and 'SYBASE' in os.environ and os.path.exists(os.environ['SYBASE']):
    dbis.append('sybase')


@pytest.mark.parametrize('dbi', dbis)
def test_get_states(dbi):
    """Test Python function interface to getting commanded states.
    """
    val_names = "obsid,simpos,pcad_mode,clocking,power_cmd".split(',')

    states = fetch_states(start='2010:100', stop='2010:101', dbi=dbi,
                          vals=val_names)
    for name in states.dtype.names:
        if states[name].dtype.kind == 'f':
            assert np.allclose(states[name], VALS[name])
        else:
            assert np.all(states[name] == VALS[name])

    names = ["datestart", "datestop", "tstart", "tstop"]
    assert names + val_names == list(states.dtype.names)
