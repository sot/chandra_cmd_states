# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os
import sys
from io import StringIO

import pytest
import numpy as np
from astropy.io import ascii

from chandra_cmd_states.get_cmd_states import main, fetch_states
from chandra_cmd_states.cmd_states import decode_power, get_state0, get_cmds, get_states

HAS_SOTMP_FILES = os.path.exists(f'{os.environ["SKA"]}/data/mpcrit1/mplogs/2017')


# This is taken from the output of
#  get_cmd_states --start=2010:100 --stop=2010:101 --vals=obsid,simpos,pcad_mode,clocking,power_cmd
# for chandra_cmd_states version 0.07 in skare 0.13 on July 18, 2012.
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
    cli_string = "--start=2010:100:12:00:00 --stop=2010:101:12:00:00 --vals=obsid,simpos,pcad_mode,clocking,power_cmd"
    sys.stdout = StringIO()
    main(cli_string.split())
    out = sys.stdout.getvalue()
    sys.stdout = sys.__stdout__
    assert out == OUT


# Set up possible backends
dbis = ['hdf5', 'sqlite']


@pytest.mark.parametrize('dbi', dbis)
def test_get_states(dbi):
    """Test Python function interface to getting commanded states.
    """
    val_names = "obsid,simpos,pcad_mode,clocking,power_cmd".split(',')

    states = fetch_states(start='2010:100:12:00:00', stop='2010:101:12:00:00', dbi=dbi,
                          vals=val_names)
    for name in states.dtype.names:
        if states[name].dtype.kind == 'f':
            assert np.allclose(states[name], VALS[name])
        else:
            assert np.all(states[name] == VALS[name])

    names = ["datestart", "datestop", "tstart", "tstop"]
    assert names + val_names == list(states.dtype.names)


@pytest.mark.skipif('not HAS_SOTMP_FILES', reason='Needs 2017 products')
def test_acis_power_cmds():
    import Ska.DBI
    all_off = decode_power("WSPOW00000")
    assert all_off["ccd_count"] == 0
    assert all_off["fep_count"] == 0
    assert all_off["vid_board"] == 0
    server = os.path.join(os.environ['SKA'], 'data', 'cmd_states', 'cmd_states.db3')
    db = Ska.DBI.DBI(dbi="sqlite", server=server)
    state0 = get_state0("2017:359:13:37:50", db=db)
    cmds = get_cmds("2017:359:13:37:50", "2017:360:00:46:00", db=db)
    states = get_states(state0, cmds)
    vid_dn = np.where(states["power_cmd"] == "WSVIDALLDN")[0]
    assert (states["ccd_count"][vid_dn] == 0).all()
    assert (states["fep_count"][vid_dn] == states["fep_count"][vid_dn[0]-1]).all()
    pow_zero = np.where(states["power_cmd"] == "WSPOW00000")[0]
    assert (states["ccd_count"][pow_zero] == 0).all()
    assert (states["fep_count"][pow_zero] == 0).all()
