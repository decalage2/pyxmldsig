"""
CherryProxy

a lightweight HTTP proxy based on the CherryPy WSGI server and httplib,
extensible for content analysis and filtering.

AUTHOR: Philippe Lagadec (decalage at laposte dot net)

PROJECT WEBSITE: http://www.decalage.info/python/cherryproxy

LICENSE:

Copyright (c) 2008-2011, Philippe Lagadec (decalage at laposte dot net)

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

Usage:
- either run this script directly for a demo, and use localhost:8070 as proxy.
- or create a class inheriting from CherryProxy and implement the methods
  adapt_request and adapt_response as desired. See the example scripts for
  more information.

usage: CherryProxy.py [-d]

-d: debug mode


IMPORTANT NOTE: This version can only handle one request at a time, this will be
                fixed in a new version soon.
"""

#------------------------------------------------------------------------------
# CHANGELOG:
# 2008-11-01 v0.01 PL: - first version
# 2008-11-02 v0.02 PL: - extensible CherryProxy class instead of functions
# 2009-05-05 v0.03 PL: - added comments and license
#                      - option to set server name in constructor
# 2009-05-06 v0.04 PL: - forward request body to server
# 2010-04-25 v0.05 PL: - moved nozip demo to separate script
#                      - debug option to enable/disable debug output


#------------------------------------------------------------------------------
# TODO:
# + thread local attributes to store request and response attributes
# + methods to parse useful headers: content-type, content-disposition, etc
# + methods to send generic responses: 404, 403, ...
# + proper logging using the standard logging module (use a logger object or
#   integrate with CherryPy?)
# + init option to enable debug messages or not
# + init option to set parent proxy
# + only read request body and response body when needed
# - CLI parameters to set options (should be extensible by subclasses)
# ? config file to set options?
# ? use urllib2 instead of httplib?


#--- IMPORTS ------------------------------------------------------------------

from cherrypy import wsgiserver
import urlparse, urllib2, httplib, sys


#--- CONSTANTS ----------------------------------------------------------------

__version__ = '0.05'

SERVER_NAME = 'CherryProxy/%s' % __version__


#=== CLASSES ==================================================================

class CherryProxy (object):

    def __init__(self, address='0.0.0.0', port=8070, server_name=SERVER_NAME,
        debug=False):
        """
        CherryProxy constructor
        """
        print 'CherryProxy listening on %s:%d (press Ctrl+C to stop)' % (address, port)
        self.server = wsgiserver.CherryPyWSGIServer((address, port),
            self.proxy_app, server_name=server_name)
        self.environ = {}
        self.req_headers = {}
        self.req_data = None
        self.resp_headers = {}
        self.resp_data = None
        if debug:
            self.debug = self.debug_enabled
            self.debug_mode = True
        else:
            self.debug = self.debug_disabled
            self.debug_mode = False


    def start(self):
        self.server.start()


    def stop(self):
        self.server.stop()

    def debug_enabled(self, string):
        print string

    def debug_disabled(self, string):
        pass


    def adapt_request(self):
        pass

    def adapt_response(self):
        pass


    def proxy_app(self, environ, start_response):
        self.environ = environ
        self.debug('_'*79)
        self.debug('REQUEST RECEIVED FROM CLIENT:')
        for env in environ:
            self.debug('%s: %s' % (env, environ[env]))
        #print environ
        self.req_headers = {}
        for h in environ:
            if h.startswith('HTTP_'):
                hname = h[5:].replace('_', '-')
                self.req_headers[hname] = environ[h]
        #print headers
        method = environ['REQUEST_METHOD']
        scheme = environ['wsgi.url_scheme']
        self.netloc = environ['SERVER_NAME']
        path = environ['PATH_INFO']
        query = environ['QUERY_STRING']
        self.url = urlparse.urlunsplit(('', '', path, query, ''))
        self.debug('- '*39)
        # if request has data, read it:
        if 'CONTENT_LENGTH' in environ:
            length = int(environ['CONTENT_LENGTH'])
            self.debug('REQUEST BODY: content-length=%d' % length)
            self.req_data = environ['wsgi.input'].read(length)
            self.debug(self.req_data)
        else:
            self.debug('No request body.')
            self.req_data = None
        # adapt request before sending it:
        self.adapt_request()
        self.debug('- '*39)
        # send request to server:
        conn = httplib.HTTPConnection(self.netloc)
        if self.debug_mode:
            conn.set_debuglevel(1)
        conn.request(method, self.url, body=self.req_data, headers=self.req_headers)
        self.resp = conn.getresponse()
        self.status = self.resp.status
        self.reason = self.resp.reason
        status = "%d %s" % (self.status, self.reason) #'200 OK'
        self.debug('- '*39)
        self.debug('RESPONSE RECEIVED FROM SERVER:')
        self.debug(status)
        self.resp_headers = self.resp.getheaders() #[('Content-type','text/plain')]
        for h in self.resp_headers:
            self.debug(' - %s: %s' % (h[0], h[1]))
        self.data = self.resp.read()
##        print '- '*39
##        print repr(self.data)
        # adapt response before sending it to client:
        self.adapt_response()
        # send response to client:
        status = "%d %s" % (self.status, self.reason) #'200 OK'
        self.debug('- '*39)
        self.debug('RESPONSE SENT TO CLIENT:')
        self.debug(status)
        for h in self.resp_headers:
            self.debug(' - %s: %s' % (h[0], h[1]))
        start_response(status, self.resp_headers)
        return [self.data]


#=== MAIN =====================================================================

if __name__ == '__main__':
    # simple CherryProxy without filter:
    debug=False
    try:
        if sys.argv[1] == '-d':
            debug=True
    except:
        pass

    print __doc__
    proxy = CherryProxy(debug=debug)
    while True:
        try:
            proxy.start()
        except KeyboardInterrupt:
            proxy.stop()
            sys.exit()
