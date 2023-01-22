# Licensed under a 3-clause BSD style license - see LICENSE.rst
from setuptools import setup
from ska_helpers.setup_helper import duplicate_package_info
from testr.setup_helper import cmdclass

name = "chandra_cmd_states"
namespace = "Chandra.cmd_states"

packages = ["chandra_cmd_states", "chandra_cmd_states.tests"]
package_dir = {name: name}

duplicate_package_info(packages, name, namespace)
duplicate_package_info(package_dir, name, namespace)

setup(name=name,
      author='Tom Aldcroft',
      description=('(DEPRECATED) Functions for creating, manipulating and updating '
                   'the Chandra commanded states database'),
      author_email='taldcroft@cfa.harvard.edu',
      use_scm_version=True,
      setup_requires=['setuptools_scm', 'setuptools_scm_git_archive'],
      zip_safe=False,
      packages=packages,
      package_dir=package_dir,
      tests_require=['pytest'],
      cmdclass=cmdclass,
      )
