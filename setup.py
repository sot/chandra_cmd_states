from setuptools import setup
setup(name='Chandra.cmd_states',
      author='Tom Aldcroft',
      description=('Functions for creating, manipulating and updating '
                   'the Chandra commanded states database'),
      author_email='aldcroft@head.cfa.harvard.edu',
      py_modules=['Chandra.cmd_states.get_cmd_states',
                  'Chandra.cmd_states.update_cmd_states'],
      version='0.08',
      zip_safe=False,
      namespace_packages=['Chandra'],
      packages=['Chandra', 'Chandra.cmd_states'],
      )
