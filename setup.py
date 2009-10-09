from setuptools import setup
setup(name='Chandra.cmd_states',
      author = 'Tom Aldcroft',
      description='Functions for creating, manipulating and updating the Chandra commanded states database',
      author_email = 'taldcroft@cfa.harvard.edu',
      py_modules = ['Chandra.cmd_states'],
      version='0.02',
      zip_safe=False,
      namespace_packages=['Chandra'],
      packages=['Chandra'],
      package_dir={'Chandra' : 'Chandra'},
      package_data={}
      )
