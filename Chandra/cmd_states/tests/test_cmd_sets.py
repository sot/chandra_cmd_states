# Licensed under a 3-clause BSD style license - see LICENSE.rst

from Chandra.cmd_states import cmd_set

# COMMAND_HW       | TLMSID= AFIDP, HEX= 6480005, MSID= AFLCRSET

def test_cmd_sets1():
    cmds = cmd_set('scs107')
    exp = ({'dur': 1.025},
           {'cmd': 'COMMAND_SW', 'dur': 1.025, 'tlmsid': 'OORMPDS'},
           {'cmd': 'COMMAND_HW', 'dur': 1.025, 'tlmsid': 'AFIDP', 'msid': 'AFLCRSET'},
           {'cmd': 'SIMTRANS', 'dur': 65.66, 'params': {'POS': -99616}},
           {'cmd': 'ACISPKT', 'dur': 1.025, 'tlmsid': 'AA00000000'},
           {'cmd': 'ACISPKT', 'dur': 10.25, 'tlmsid': 'AA00000000'},
           {'cmd': 'ACISPKT', 'tlmsid': 'WSPOW0002A'})
    assert cmds == exp


def test_cmd_sets2():
    cmds = cmd_set('nsm')
    exp = ({'cmd': 'COMMAND_SW', 'tlmsid': 'AONSMSAF'},
           {'dur': 1.025},
           {'cmd': 'COMMAND_SW', 'dur': 1.025, 'tlmsid': 'OORMPDS'},
           {'cmd': 'COMMAND_HW', 'dur': 1.025, 'tlmsid': 'AFIDP', 'msid': 'AFLCRSET'},
           {'cmd': 'SIMTRANS', 'dur': 65.66, 'params': {'POS': -99616}},
           {'cmd': 'ACISPKT', 'dur': 1.025, 'tlmsid': 'AA00000000'},
           {'cmd': 'ACISPKT', 'dur': 10.25, 'tlmsid': 'AA00000000'},
           {'cmd': 'ACISPKT', 'tlmsid': 'WSPOW0002A'},
           {'dur': 1.025},
           {'cmd': 'COMMAND_SW', 'tlmsid': 'AODSDITH'})
    assert cmds == exp


def test_cmd_sets3():
    cmds = cmd_set('manvr', 0, 0, 0, 1)
    exp = ({'cmd': 'COMMAND_SW',
            'dur': 0.25625,
            'msid': 'AONMMODE',
            'tlmsid': 'AONMMODE'},
           {'cmd': 'COMMAND_SW', 'dur': 4.1, 'msid': 'AONM2NPE', 'tlmsid': 'AONM2NPE'},
           {'cmd': 'MP_TARGQUAT',
            'dur': 5.894,
            'params': {'Q1': 0.0, 'Q2': 0.0, 'Q3': 0.0, 'Q4': 1.0},
            'tlmsid': 'AOUPTARQ'},
           {'cmd': 'COMMAND_SW', 'msid': 'AOMANUVR', 'tlmsid': 'AOMANUVR'})
    assert cmds == exp


def test_cmd_sets4():
    cmds = cmd_set('obsid', 30000)
    exp = ({'cmd': 'MP_OBSID', 'params': {'ID': 30000}},)
    assert cmds == exp


def test_cmd_sets5():
    cmds = cmd_set('acis', 'XTZ0000005', 'WSPOW0CF3F')
    exp = ({'cmd': 'ACISPKT', 'tlmsid': 'XTZ0000005'},
           {'cmd': 'ACISPKT', 'tlmsid': 'WSPOW0CF3F'})
    assert cmds == exp


def test_cmd_sets6():
    cmds = cmd_set('dith_on')
    exp = ({'dur': 1.025}, {'cmd': 'COMMAND_SW', 'tlmsid': 'AOENDITH'})
    assert cmds == exp


def test_cmd_sets7():
    cmds = cmd_set('dith_off')
    exp = ({'dur': 1.025}, {'cmd': 'COMMAND_SW', 'tlmsid': 'AODSDITH'})
    assert cmds == exp
