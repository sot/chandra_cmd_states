# Licensed under a 3-clause BSD style license - see LICENSE.rst
from setuptools import setup

from Chandra.cmd_states import __version__
try:
    from testr.setup_helper import cmdclass
except ImportError:
    cmdclass = {}

setup(name='Chandra.cmd_states',
      author='Tom Aldcroft',
      description=('Functions for creating, manipulating and updating '
                   'the Chandra commanded states database'),
      author_email='taldcroft@cfa.harvard.edu',
      py_modules=['Chandra.cmd_states.cmd_states',
                  'Chandra.cmd_states.get_cmd_states',
                  'Chandra.cmd_states.update_cmd_states',
                  'Chandra.cmd_states.interrupt_loads',
                  'Chandra.cmd_states.add_nonload_cmds',
                  ],
      version=__version__,
      zip_safe=False,
      packages=['Chandra', 'Chandra.cmd_states', 'Chandra.cmd_states.tests'],
      tests_require=['pytest'],
      cmdclass=cmdclass,
      )
