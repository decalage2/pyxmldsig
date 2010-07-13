"""
Setup script for pyxmldsig
"""

import distutils.core
from pyxmldsig import __version__ as VERSION

DESCRIPTION = "A Python module to create and verify XML Digital Signatures (XML-DSig)"

LONG_DESCRIPTION = \
"""pyxmldsig is a Python module to create and verify XML Digital Signatures (XML-DSig).
This is a simple interface to the PyXMLSec library, aiming to provide a more
pythonic API suitable for Python applications.
See http://www.decalage.info/python/pyxmldsig for more information and to
download the latest version.
"""

kw = {
    'name': "pyxmldsig",
    'version': VERSION,
    'description': DESCRIPTION,
    'long_description': LONG_DESCRIPTION,
    'author': "Philippe Lagadec",
    'author_email': "decalage (a) laposte.net",
    'url': "http://www.decalage.info/python/pyxmldsig",
    'license': "BSD",
    'py_modules': ['pyxmldsig']
    }


# If we're running Python 2.3+, add extra information
if hasattr(distutils.core, 'setup_keywords'):
    if 'classifiers' in distutils.core.setup_keywords:
        kw['classifiers'] = [
            'Development Status :: 4 - Beta',
            'License :: OSI Approved :: BSD License',
            'Natural Language :: English',
            'Intended Audience :: Developers',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            'Topic :: Security',
            'Topic :: Software Development :: Libraries :: Python Modules'
          ]
    if 'download_url' in distutils.core.setup_keywords:
        kw['download_url'] = "http://www.decalage.info/python/pyxmldsig"


distutils.core.setup(**kw)
