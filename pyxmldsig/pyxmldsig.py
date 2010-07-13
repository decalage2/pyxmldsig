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
"""

__version__ = '0.05'

#=== CHANGELOG ================================================================

# 2009-09-10 v0.01 PL: - first version, inspired from pyxmlsec samples
# 2009-09-14 v0.02 PL: - small improvements, license
# 2010-05-11 v0.03 PL: - renamed to pyxmldsig
#                      - X509 cert is now optional
#                      - a key password may be provided
# 2010-06-29 v0.04 PL: - added Xmldsig class to load a key once for several
#                        signatures
#                      - added signature verification
#                      - added simple XML-DSIG templates
# 2010-07-06 v0.05 PL: - added load_cert to load several certificates at once

#=== TODO =====================================================================

# - add option to generate XML-DSig template automatically, appended to a chosen
#   node.
# - add option to improve detached signature with http URI: fix URI after
#   signature.
# - check if all temporary xmlsec objects are destroyed after each operation
# - find a solution to load a certificate with a key name to allow signature
#   verification without embedded X509 cert
# - add option to use keys manager or single key?

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


#=== CONSTANTS ================================================================

# XML Signature template with X509 certificate:
# - the X.509 cert tag must be empty, else another one will be appended
# - KeyName is optional
TEMPLATE_WITH_CERT = \
"""<Signature xmlns="http://www.w3.org/2000/09/xmldsig#">
<SignedInfo>
  <CanonicalizationMethod Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315"/>
  <SignatureMethod Algorithm="http://www.w3.org/2000/09/xmldsig#rsa-sha1"/>
  <Reference URI="">
    <Transforms>
      <Transform Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature"/>
    </Transforms>
    <DigestMethod Algorithm="http://www.w3.org/2000/09/xmldsig#sha1"/>
    <DigestValue>TEMPLATE</DigestValue>
  </Reference>
</SignedInfo>
<SignatureValue>TEMPLATE</SignatureValue>
<KeyInfo>
  <KeyName/>
  <X509Data>
    <X509Certificate></X509Certificate>
  </X509Data>
</KeyInfo>
</Signature>
"""

# XML Signature template without X509 certificate:
# - KeyInfo / KeyName is optional
TEMPLATE_WITHOUT_CERT = \
"""<Signature xmlns="http://www.w3.org/2000/09/xmldsig#">
<SignedInfo>
  <CanonicalizationMethod Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315"/>
  <SignatureMethod Algorithm="http://www.w3.org/2000/09/xmldsig#rsa-sha1"/>
  <Reference URI="">
    <Transforms>
      <Transform Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature"/>
    </Transforms>
    <DigestMethod Algorithm="http://www.w3.org/2000/09/xmldsig#sha1"/>
    <DigestValue>TEMPLATE</DigestValue>
  </Reference>
</SignedInfo>
<SignatureValue>TEMPLATE</SignatureValue>
<KeyInfo>
  <KeyName/>
</KeyInfo>
</Signature>
"""

#=== CLASSES ==================================================================

class Xmldsig (object):
    """
    class to sign and verify XML signatures (XML DSig)
    """

    def __init__(self, key_file=None, cert_file=None, password='', key_name=None):
        """
        - key_file: str, filename of PEM file containing the private key.
                    (the file should NOT be password-protected)
        - cert_file: str, filename of PEM file containing the X509 certificate.
                     (optional: can be None)
        - password: str, password to open key file, or None if no password.
        - key_name: str, name for the key in the signature, or None if omitted.
        """
        self.dsig_ctx = None
        # TEST: single key
        self.key = None
        # Create and initialize keys manager
        self.keysmngr = xmlsec.KeysMngr()
        if self.keysmngr is None:
            raise RuntimeError, "Error: failed to create keys manager."
        if xmlsec.cryptoAppDefaultKeysMngrInit(self.keysmngr) < 0:
            self.keysmngr.destroy()
            raise RuntimeError, "Error: failed to initialize keys manager."
        # load key
        self.load(key_file, cert_file, password, key_name)


    def load(self, key_file=None, cert_file=None, password='', key_name=None):
        """
        load a private key and/or a public certificate for signature and verification

        - key_file: str, filename of PEM file containing the private key.
                    (the file should NOT be password-protected)
        - cert_file: str, filename of PEM file containing the X509 certificate.
                     (optional: can be None)
        - password: str, password to open key file, or None if no password.
        """
        #TODO: try except block to destroy key if error
        if key_file is not None:
            # Load private key, with optional password
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
            if key_name is not None:
                # Set key name
                if key.setName(key_name) < 0:
                    raise RuntimeError, "Error: failed to set key name to \"%s\"" % key_name
            if cert_file is not None:
                # Load certificate and add to the key
                if xmlsec.cryptoAppKeyCertLoad(key, cert_file, xmlsec.KeyDataFormatPem) < 0:
                    raise RuntimeError, "Error: failed to load PEM certificate \"%s\"" % cert_file
            # load key into manager:
            if xmlsec.cryptoAppDefaultKeysMngrAdoptKey(self.keysmngr, key) < 0:
                raise RuntimeError, "Error: failed to load key into keys manager"

        elif cert_file is not None:
            # case when we only want to load a cert without private key
            if self.keysmngr.certLoad(cert_file, xmlsec.KeyDataFormatPem,
                             xmlsec.KeyDataTypeTrusted) < 0:
                # is it better to keep the keys manager if an error occurs?
                #self.keysmngr.destroy()
                raise RuntimeError, "Error: failed to load PEM certificate from \"%s\"" % cert_file
            # THIS DOES NOT WORK: it seems a certificate cannot be loaded like a key with a name...
##            key = xmlsec.cryptoAppKeyLoad(filename = cert_file,
##                format = xmlsec.KeyDataFormatPem, pwd = password,
##                pwdCallback = None, pwdCallbackCtx = None)
##            if key is None:
##                raise RuntimeError, "Error: failed to load PEM certificate from \"%s\"", cert_file
##            if key_name is not None:
##                # Set key name
##                if key.setName(key_name) < 0:
##                    raise RuntimeError, "Error: failed to set key name to \"%s\"" % key_name
##            # load key into manager:
##            if xmlsec.cryptoAppDefaultKeysMngrAdoptKey(self.keysmngr, key) < 0:
##                raise RuntimeError, "Error: failed to load certificate into keys manager"

    def load_certs(self, certificates):
        """
        load one or several certificates into the keys manager for signature
        verification. For example, load the CA cert, any number of intermediate
        certs, and the cert corresponding to the key used for the signature.

        certificates: list or tuple containing certificate file names
        """
        for cert in certificates:
            self.load(cert_file=cert)


    def sign_file (self, template_file):
        """
        Sign a XML file using the signature template in the XML file.
        The certificate from cert_file is placed in the <dsig:X509Data/> node.

        - template_file: str, filename of XML file containing an XML-DSig template.

        Returns a string containing the signed XML data.
        Raises an exception if an error occurs.
        """
        xmlstring = open(template_file).read()
        return self.sign_xmlstring(xmlstring)


    def sign_xmlstring (self, xmlstring):
        """
        Sign xmlstring using the signature template in xmlstring.
        The certificate from cert_file is placed in the <dsig:X509Data/> node.

        - xmlstring: str, XML data containing an XML-DSig template.

        Returns a string containing the signed XML data.
        Raises an exception if an error occurs.
        """
        # try block to ensure cleanup is called even if an exception is raised:
        try:
            # Create signature context
            self._create_context()
            # Load template
            doc = self._parse_xmlstring(xmlstring)
            # find the XML-DSig start node
            node = xmlsec.findNode(doc.getRootElement(), xmlsec.NodeSignature,
                                   xmlsec.DSigNs)
            if node is None:
        	    raise RuntimeError, "Error: XML-DSIG node not found"
            # Sign the template
            if self.dsig_ctx.sign(node) < 0:
                raise RuntimeError, "Error: signature failed"
            output = str(doc)
        finally:
            # cleanup, even if an exception has been raised:
            self._cleanup_context()
            if doc is not None:
                doc.freeDoc()
        # return output if no exception was raised:
        return output


    def verify_file (self, xmlfile):
        """
        Verify signature in XML file using the loaded certificate.

        - xmlfile: str, filename of XML file containing an XML-DSig signature.

        Returns True if the signature is valid, False otherwise.
        Raises an exception if an error occurs.
        """
        xmlstring = open(xmlfile).read()
        return self.verify_xmlstring(xmlstring)


    def verify_xmlstring (self, xmlstring):
        """
        Verify signature in xmlstring using the loaded certificate.

        - xmlstring: str, XML data containing an XML-DSig signature.

        Returns True if the signature is valid, False otherwise.
        Raises an exception if an error occurs.
        """
        doc = None
        # try block to ensure cleanup is called even if an exception is raised:
        try:
            # Create signature context
            self._create_context()
            # Load XML data
            doc = self._parse_xmlstring(xmlstring)
            # find the XML-DSig start node
            node = xmlsec.findNode(doc.getRootElement(), xmlsec.NodeSignature,
                                   xmlsec.DSigNs)
            if node is None:
        	    raise RuntimeError, "Error: XML-DSIG node not found"
            # Verify signature
            if self.dsig_ctx.verify(node) < 0:
                # An error occured, the signature could not be verified
                raise RuntimeError, "Error: An error occured, the signature could not be verified"
            if self.dsig_ctx.status == xmlsec.DSigStatusSucceeded:
                # Signature is OK
                return True
            else:
                # Signature is INVALID
                return False
        finally:
            # cleanup, even if an exception has been raised:
            self._cleanup_context()
            if doc is not None:
                doc.freeDoc()
        # return output if no exception was raised:
        return output


    def _parse_xmlstring(self, xmlstring):
        """
        parse XML string containing XML-DSIG nodes for signature (template) or
        verification (signed data)
        """
        #doc = libxml2.parseFile(tmpl_file)
        doc = libxml2.parseDoc(xmlstring)
        if doc is None or doc.getRootElement() is None:
            raise RuntimeError, "Error: unable to parse XML data"
        return doc


    def _create_context(self):
        """
        create the xmlsec context for signature or verification
        """
        self.dsig_ctx = xmlsec.DSigCtx(self.keysmngr)
        if self.dsig_ctx is None:
            raise RuntimeError, "Error: failed to create signature context"


    def _cleanup_context (self):
        """
        cleanup the xmlsec context in case of error
        """
        if self.dsig_ctx is not None:
            self.dsig_ctx.destroy()
        self.dsig_ctx = None




#=== FUNCTIONS ================================================================

def sign_file(template_file, key_file, cert_file=None, password='', key_name=None):
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
    xmldsig = Xmldsig(key_file, cert_file, password, key_name)
    return xmldsig.sign_file(template_file)
##    xmlstring = open(template_file).read()
##    return sign_xmlstring(xmlstring, key_file, cert_file, password)


def sign_xmlstring(xmlstring, key_file, cert_file=None, password='', key_name=None):
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
    xmldsig = Xmldsig(key_file, cert_file, password, key_name)
    return xmldsig.sign_xmlstring(xmlstring)
##    # Load template
##    #doc = libxml2.parseFile(tmpl_file)
##    doc = libxml2.parseDoc(xmlstring)
##    if doc is None or doc.getRootElement() is None:
##        raise RuntimeError, "Error: unable to parse XML data"
##
##    # try block to ensure cleanup is called even if an exception is raised:
##    try:
##        dsig_ctx = None
##
##        # Find XML-DSig start node
##        node = xmlsec.findNode(doc.getRootElement(), xmlsec.NodeSignature,
##                               xmlsec.DSigNs)
##        if node is None:
##    	    raise RuntimeError, "Error: start node not found"
##
##        # Create signature context, we don't need keys manager in this example
##        dsig_ctx = xmlsec.DSigCtx()
##        if dsig_ctx is None:
##            raise RuntimeError, "Error: failed to create signature context"
##
##        # Load private key, assuming that there is not password
##        #print 'PASSWORD: %s' % password
##        key = xmlsec.cryptoAppKeyLoad(filename = key_file,
##            format = xmlsec.KeyDataFormatPem, pwd = password,
##            pwdCallback = None, pwdCallbackCtx = None)
##        # API references:
##        # http://pyxmlsec.labs.libre-entreprise.org/docs/html/xmlsec-module.html#cryptoAppKeyLoad
##        # http://www.aleksey.com/xmlsec/api/xmlsec-app.html#XMLSECCRYPTOAPPKEYLOAD
##        # http://www.aleksey.com/xmlsec/api/xmlsec-keysdata.html#XMLSECKEYDATAFORMAT
##        if key is None:
##            raise RuntimeError, "Error: failed to load private PEM key from \"%s\"" % key_file
##        dsig_ctx.signKey = key
##
##        if cert_file is not None:
##            # Load certificate and add to the key
##            ##    if not check_filename(cert_file):
##            ##        return cleanup(doc, dsig_ctx)
##            if xmlsec.cryptoAppKeyCertLoad(key, cert_file, xmlsec.KeyDataFormatPem) < 0:
##                raise RuntimeError, "Error: failed to load PEM certificate \"%s\"" % cert_file
##
##        # Set key name to the file name, this is just an example!
##        if key.setName(key_file) < 0:
##            raise RuntimeError, "Error: failed to set key name for key from \"%s\"" % key_file
##
##        # Sign the template
##        if dsig_ctx.sign(node) < 0:
##            raise RuntimeError, "Error: signature failed"
##
##        ##    # Print signed document to stdout
##        ##    doc.dump("-")
##        ##    doc.saveFile("test.xml")
##        output = str(doc)
##    finally:
##        # cleanup, even if an exception has been raised:
##        cleanup(doc, dsig_ctx)
##    # return output if no exception was raised:
##    return output


##def cleanup(doc=None, dsig_ctx=None, res=-1):
##    """
##    Cleans libxml2 context after usage.
##    """
##    if dsig_ctx is not None:
##        dsig_ctx.destroy()
##    if doc is not None:
##        doc.freeDoc()
##    return res


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
