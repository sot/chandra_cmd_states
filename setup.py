from setuptools import setup
from Chandra.cmd_states.version import version
setup(name='Chandra.cmd_states',
      author='Tom Aldcroft',
      description=('Functions for creating, manipulating and updating '
                   'the Chandra commanded states database'),
      author_email='aldcroft@head.cfa.harvard.edu',
      py_modules=['Chandra.cmd_states.cmd_states',
                  'Chandra.cmd_states.get_cmd_states',
                  'Chandra.cmd_states.update_cmd_states',
                  'Chandra.cmd_states.interrupt_loads',
                  'Chandra.cmd_states.add_nonload_cmds',
                  'Chandra.cmd_states.version',
                  ],
      version=version,
      zip_safe=False,
      namespace_packages=['Chandra'],
      packages=['Chandra', 'Chandra.cmd_states'],
      )
