"""Installs CherryProxy using distutils

Run:
    python setup.py install

to install this package.
"""

##try:
##    from setuptools import setup
##except ImportError:
from distutils.core import setup

from distutils.command.install import INSTALL_SCHEMES
import sys
import os
import cherryproxy

###############################################################################
# arguments for the setup command
###############################################################################
name = "CherryProxy"
version = cherryproxy.__version__
desc = "A simple, extensible HTTP proxy for content filtering in Python"
long_desc = """CherryProxy is a simple, extensible HTTP proxy for content filtering written in Python.
It is based on the CherryPy WSGI server and httplib.
See http://www.decalage.info/python/cherryproxy for more information.
"""
classifiers=[
    "Development Status :: 3 - Alpha",
    "Environment :: Web Environment",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: BSD License",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 2",
#    "Programming Language :: Python :: 3",
    "Topic :: Internet :: WWW/HTTP",
    "Topic :: Internet :: Proxy Servers",
    "Topic :: Software Development :: Libraries",
    "Topic :: Security",
]
author="Philippe Lagadec"
author_email="decalage at laposte dot net"
url="http://www.decalage.info/python/cherryproxy"
license="BSD"
packages=[
    "cherryproxy", 'cherryproxy.examples',
    'cherryproxy.cherrypy', 'cherryproxy.cherrypy.wsgiserver',
]
download_url="http://www.decalage.info/python/cherryproxy"
data_files=[
    ('cherryproxy', [
        'cherryproxy/README.txt',
                  ]),
    ('cherryproxy.cherrypy', [
        'cherryproxy/cherrypy/README.txt',
        'cherryproxy/cherrypy/LICENSE.txt',
                  ]),
]
##if sys.version_info >= (3, 0):
##    required_python_version = '3.0'
##    setupdir = 'py3'
##else:
##    required_python_version = '2.3'
##    setupdir = 'py2'
setupdir = '.'
package_dir={'': setupdir}
##data_files = [(install_dir, ['%s/%s' % (setupdir, f) for f in files])
##              for install_dir, files in data_files]
#scripts = ["%s/cherrypy/cherryd" % setupdir]

###############################################################################
# end arguments for setup
###############################################################################

##def fix_data_files(data_files):
##    """
##    bdist_wininst seems to have a bug about where it installs data files.
##    I found a fix the django team used to work around the problem at
##    http://code.djangoproject.com/changeset/8313 .  This function
##    re-implements that solution.
##    Also see http://mail.python.org/pipermail/distutils-sig/2004-August/004134.html
##    for more info.
##    """
##    def fix_dest_path(path):
##        return '\\PURELIB\\%(path)s' % vars()
##
##    if not 'bdist_wininst' in sys.argv: return
##
##    data_files[:] = [
##        (fix_dest_path(path), files)
##        for path, files in data_files]
##fix_data_files(data_files)

def main():
##    if sys.version < required_python_version:
##        s = "I'm sorry, but %s %s requires Python %s or later."
##        print(s % (name, version, required_python_version))
##        sys.exit(1)
##    # set default location for "data_files" to
##    # platform specific "site-packages" location
##    for scheme in list(INSTALL_SCHEMES.values()):
##        scheme['data'] = scheme['purelib']

    dist = setup(
        name=name,
        version=version,
        description=desc,
        long_description=long_desc,
        classifiers=classifiers,
        author=author,
        author_email=author_email,
        url=url,
        license=license,
        package_dir=package_dir,
        packages=packages,
        download_url=download_url,
        data_files=data_files,
#        scripts=scripts,
    )


if __name__ == "__main__":
    main()
