pyxmldsig is a Python module to create and verify XML Digital Signatures (XML-DSig).

This is a simple interface to the PyXMLSec library, aiming to provide a more
pythonic API suitable for Python applications.
See http://www.decalage.info/python/pyxmldsig to download the latest version.

May be used as a command-line tool or as a Python module.
This code is inspired from PyXMLSec samples, with a more pythonic interface:
http://pyxmlsec.labs.libre-entreprise.org/index.php?section=examples

AUTHOR: Philippe Lagadec (decalage at laposte dot net)

PROJECT WEBSITE: http://www.decalage.info/python/pyxmldsig

LICENSE:

Copyright (c) 2009-2010, Philippe Lagadec (decalage at laposte dot net)

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above copyright
notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
PERFORMANCE OF THIS SOFTWARE.


USAGE AS A TOOL:
pyxmldsig.py <data.xml> -k <key-file.pem> [-c cert-file.pem] [-p password]

USAGE IN A PYTHON APPLICATION:

import pyxmldsig

# simple function interface:
signed_xml = pyxmldsig.sign_file(template_file='myfile.xml',
    key_file='mykey.pem', cert_file='myx509cert.pem', password='mypassword')
print signed_xml

# sign with class interface:
xdsig = pyxmldsig.Xmldsig(key_file='mykey.pem', cert_file='myx509cert.pem',
    password='mypassword')
signed_xml1 = xdsig.sign_file('myfile.xml')
signed_xml2 = xdsig.sign_file(pyxmldsig.TEMPLATE_WITH_CERT)

# verify with class interface:
xdsig2 = pyxmldsig.Xmldsig()
xdsig2.load_certs(['cacert.pem', 'myx509cert.pem'])
assert xdsig2.verify_xmlstring(signed_xml1) == True
assert xdsig2.verify_xmlstring(signed_xml2) == True


REQUIREMENTS:
- pyxmlsec: http://pyxmlsec.labs.libre-entreprise.org/
- xmlsec: http://www.aleksey.com/xmlsec/
- libxml2: http://xmlsoft.org
- On Windows see also this site for convenient compiled binaries:
  http://returnbooleantrue.blogspot.com/2009/04/pyxmlsec-windows-binary.html

REFERENCES:
- http://www.w3.org/TR/xmldsig-core/
