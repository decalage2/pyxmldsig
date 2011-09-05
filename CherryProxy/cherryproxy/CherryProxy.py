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
# + methods to parse useful headers: content-type, content-disposition, etc
# + methods to send generic responses: 404, 403, ...
# + proper logging using the standard logging module (use a logger object or
#   integrate with CherryPy?)
# + init option to enable debug messages or not
# + init option to set parent proxy
# + only read request body and response body when needed, or add methods
#   adapt_req_headers and adapt_resp_headers
# - CLI parameters to set options (should be extensible by subclasses)
# ? config file to set options?
# ? use urllib2 instead of httplib?


#--- IMPORTS ------------------------------------------------------------------

from cherrypy import wsgiserver
import urlparse, urllib2, httplib, sys, threading


#--- CONSTANTS ----------------------------------------------------------------

__version__ = '0.06'

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
        # thread local variables to store request/response data per thread:
        self.req = threading.local()
        self.resp = threading.local()
        # TODO: move these to thread local
        self.req.environ = {}
        self.req.headers = {}
        self.req.data = None
        self.resp.headers = {}
        self.resp.data = None
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
        t = threading.current_thread()
        self.debug('Thread %d - %s' % (t.ident, t.name))
        self.req.environ = environ
        self.debug('_'*79)
        self.debug('REQUEST RECEIVED FROM CLIENT:')
        for env in environ:
            self.debug('%s: %s' % (env, environ[env]))
        #print environ
        self.req.headers = {}
        for h in environ:
            if h.startswith('HTTP_'):
                hname = h[5:].replace('_', '-')
                self.req.headers[hname] = environ[h]
        #print headers
        self.req.method = environ['REQUEST_METHOD']
        self.req.scheme = environ['wsgi.url_scheme']
        self.req.netloc = environ['SERVER_NAME']
        self.req.path = environ['PATH_INFO']
        self.req.query = environ['QUERY_STRING']
        self.req.url = urlparse.urlunsplit(
            ('', '', self.req.path, self.req.query, ''))
        self.debug('- '*39)
        # if request has data, read it:
        if 'CONTENT_LENGTH' in environ:
            self.req.length = int(environ['CONTENT_LENGTH'])
            self.debug('REQUEST BODY: content-length=%d' % self.req.length)
            self.req.data = environ['wsgi.input'].read(self.req.length)
            self.debug(self.req.data)
        else:
            self.debug('No request body.')
            self.req.data = None
        # adapt request before sending it:
        self.adapt_request()
        self.debug('- '*39)
        # send request to server:
        conn = httplib.HTTPConnection(self.req.netloc)
        if self.debug_mode:
            conn.set_debuglevel(1)
        conn.request(self.req.method, self.req.url, body=self.req.data, headers=self.req.headers)
        self.resp.response = conn.getresponse()
        self.resp.status = self.resp.response.status
        self.resp.reason = self.resp.response.reason
        status = "%d %s" % (self.resp.status, self.resp.reason) #'200 OK'
        self.debug('- '*39)
        self.debug('RESPONSE RECEIVED FROM SERVER:')
        self.debug(status)
        self.resp.headers = self.resp.response.getheaders() #[('Content-type','text/plain')]
        for h in self.resp.headers:
            self.debug(' - %s: %s' % (h[0], h[1]))
        self.resp.data = self.resp.response.read()
##        print '- '*39
##        print repr(self.data)
        # adapt response before sending it to client:
        self.adapt_response()
        # send response to client:
        status = "%d %s" % (self.resp.status, self.resp.reason) #'200 OK'
        self.debug('- '*39)
        self.debug('RESPONSE SENT TO CLIENT:')
        self.debug(status)
        for h in self.resp.headers:
            self.debug(' - %s: %s' % (h[0], h[1]))
        start_response(status, self.resp.headers)
        return [self.resp.data]


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
