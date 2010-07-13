"""
pyxmldsig.py:
A Python module to create and verify XML Digital Signatures (XML-DSig)

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


USAGE: pyxmldsig.py <data.xml> -k <key-file.pem> [-c cert-file.pem] [-p password]

SAMPLE USAGE IN A PYTHON APPLICATION:

import pyxmldsig
signed_xml = pyxmldsig.sign_file(template_file='myfile.xml',
    key_file='mykey.pem', cert_file='myx509cert.pem', password='mypassword')
print signed_xml

REQUIREMENTS:
- pyxmlsec: http://pyxmlsec.labs.libre-entreprise.org/
- xmlsec: http://www.aleksey.com/xmlsec/
- libxml2: http://xmlsoft.org
- On Windows see also this site for convenient compiled binaries:
  http://returnbooleantrue.blogspot.com/2009/04/pyxmlsec-windows-binary.html

REFERENCES:
- http://www.w3.org/TR/xmldsig-core/
"""

__version__ = '0.03'

#=== CHANGELOG ================================================================

# 2009-09-10 v0.01 PL: - first version, inspired from pyxmlsec samples
# 2009-09-14 v0.02 PL: - small improvements, license
# 2010-05-11 v0.03 PL: - renamed to pyxmldsig
#                      - X509 cert is now optional
#                      - a key password may be provided

#=== TODO =====================================================================

# - add signature verification
# - more flexible class-based interface, supporting all use cases
#   (and to load keyfile only once when signing several files)
# - add option to generate XML-DSig template automatically, appended to a chosen
#   node.
# - add option to improve detached signature with http URI: fix URI after
#   signature.

#=== IMPORTS ==================================================================

import sys

try:
    import libxml2
except ImportError:
    raise ImportError, "libxml2 is required: see http://xmlsoft.org"

try:
    import xmlsec
except ImportError:
    raise ImportError, "pyxmlsec is required: see http://pyxmlsec.labs.libre-entreprise.org"


#=== FUNCTIONS ================================================================

def sign_file(template_file, key_file, cert_file=None, password=''):
    """
    Sign a XML file using private key from key_file and the signature template
    in the XML file.
    The certificate from cert_file is placed in the <dsig:X509Data/> node.

    - template_file: str, filename of XML file containing an XML-DSig template.
    - key_file: str, filename of PEM file containing the private key.
                (the file should NOT be password-protected)
    - cert_file: str, filename of PEM file containing the X509 certificate.
                 (optional: can be None)
    - password: str, password to open key file, or None if no password.

    Returns a string containing the signed XML data.
    Raises an exception if an error occurs.
    """
    xmlstring = open(template_file).read()
    return sign_xmlstring(xmlstring, key_file, cert_file, password)


def sign_xmlstring(xmlstring, key_file, cert_file=None, password=''):
    """
    Sign xmlstring using private key from key_file and the signature template
    in xmlstring.
    The certificate from cert_file is placed in the <dsig:X509Data/> node.

    - xmlstring: str, XML data containing an XML-DSig template.
    - key_file: str, filename of PEM file containing the private key.
                (the file should NOT be password-protected)
    - cert_file: str, filename of PEM file containing the X509 certificate.
                 (optional: can be None)
    - password: str, password to open key file, or "" if no password.
                (never use None because libxmlsec will ask on the console)

    Returns a string containing the signed XML data.
    Raises an exception if an error occurs.
    """
    # Load template
    #doc = libxml2.parseFile(tmpl_file)
    doc = libxml2.parseDoc(xmlstring)
    if doc is None or doc.getRootElement() is None:
        raise RuntimeError, "Error: unable to parse XML data"

    # try block to ensure cleanup is called even if an exception is raised:
    try:
        dsig_ctx = None

        # Find XML-DSig start node
        node = xmlsec.findNode(doc.getRootElement(), xmlsec.NodeSignature,
                               xmlsec.DSigNs)
        if node is None:
    	    raise RuntimeError, "Error: start node not found"

        # Create signature context, we don't need keys manager in this example
        dsig_ctx = xmlsec.DSigCtx()
        if dsig_ctx is None:
            raise RuntimeError, "Error: failed to create signature context"

        # Load private key, assuming that there is not password
        #print 'PASSWORD: %s' % password
        key = xmlsec.cryptoAppKeyLoad(filename = key_file,
            format = xmlsec.KeyDataFormatPem, pwd = password,
            pwdCallback = None, pwdCallbackCtx = None)
        # API references:
        # http://pyxmlsec.labs.libre-entreprise.org/docs/html/xmlsec-module.html#cryptoAppKeyLoad
        # http://www.aleksey.com/xmlsec/api/xmlsec-app.html#XMLSECCRYPTOAPPKEYLOAD
        # http://www.aleksey.com/xmlsec/api/xmlsec-keysdata.html#XMLSECKEYDATAFORMAT
        if key is None:
            raise RuntimeError, "Error: failed to load private PEM key from \"%s\"" % key_file
        dsig_ctx.signKey = key

        if cert_file is not None:
            # Load certificate and add to the key
            ##    if not check_filename(cert_file):
            ##        return cleanup(doc, dsig_ctx)
            if xmlsec.cryptoAppKeyCertLoad(key, cert_file, xmlsec.KeyDataFormatPem) < 0:
                raise RuntimeError, "Error: failed to load PEM certificate \"%s\"" % cert_file

        # Set key name to the file name, this is just an example!
        if key.setName(key_file) < 0:
            raise RuntimeError, "Error: failed to set key name for key from \"%s\"" % key_file

        # Sign the template
        if dsig_ctx.sign(node) < 0:
            raise RuntimeError, "Error: signature failed"

        ##    # Print signed document to stdout
        ##    doc.dump("-")
        ##    doc.saveFile("test.xml")
        output = str(doc)
    finally:
        # cleanup, even if an exception has been raised:
        cleanup(doc, dsig_ctx)
    # return output if no exception was raised:
    return output


def cleanup(doc=None, dsig_ctx=None, res=-1):
    """
    Cleans libxml2 context after usage.
    """
    if dsig_ctx is not None:
        dsig_ctx.destroy()
    if doc is not None:
        doc.freeDoc()
    return res


def _init():
    """
    Initialize necessary libraries (libxml2 and xmlsec).
    Should be called once only: this is automatic when this module is imported.
    Raises an exception if an error occurs.
    """
    # Init libxml library
    libxml2.initParser()
    libxml2.substituteEntitiesDefault(1)
    # Init xmlsec library
    assert xmlsec.init() >= 0, "Error: xmlsec initialization failed."
    # Check loaded library version
    assert xmlsec.checkVersion() == 1, "Error: loaded xmlsec library version is not compatible."
    # Init crypto library
    assert xmlsec.cryptoAppInit(None) >= 0, "Error: crypto initialization failed."
    # Init xmlsec-crypto library
    assert xmlsec.cryptoInit() >= 0, "Error: xmlsec-crypto initialization failed."


def shutdown():
    """
    Shutdown all libraries cleanly.
    Should only be called at the end of all xmlsec actions.
    """
    # Shutdown xmlsec-crypto library
    xmlsec.cryptoShutdown()
    # Shutdown crypto library
    xmlsec.cryptoAppShutdown()
    # Shutdown xmlsec library
    xmlsec.shutdown()
    # Shutdown LibXML2
    libxml2.cleanupParser()


#=== MAIN =====================================================================

# always initialize the xmlsec and libxml2 libraries:
_init()

def main():
    """
    To use this module as a command-line tool.
    """
    from optparse import OptionParser
    usage = "usage: %prog [options] file.xml"
    parser = OptionParser(usage=usage, version='%prog '+__version__)
    parser.add_option("-k", "--keyfile",
        metavar="KEYFILE", help="PEM file containing private key",
        action="store", type="string", dest="keyfile")
    parser.add_option("-c", "--certfile",
        metavar="CERTFILE", help="PEM file containing the X.509 certificate",
        action="store", type="string", dest="certfile")
    parser.add_option("-p", "--password", default='', # not None!
        metavar="PASSWORD", help="Password of the private key file",
        action="store", type="string", dest="password")
    (options, args) = parser.parse_args()

    if len(args) != 1 and not options.keyfile:
        print __doc__
        parser.print_help()
        sys.exit()

    signed_xml = sign_file(template_file=args[0], key_file=options.keyfile,
        cert_file=options.certfile, password=options.password)
    print signed_xml
    shutdown()


if __name__ == "__main__":
    main()

# This code was developed while listening to Fleet Foxes
