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
# 2011-09-03 v0.06 PL: - replaced attributes by thread local variables to
#                        support multithreading
# 2011-09-07 v0.07 PL: - use logging instead of print for debugging
#                      - split proxy_app into several methods
#                      - close each http connection to server


#------------------------------------------------------------------------------
# TODO:
# + fix examples, using CT+filename, blocking some requests
# + simple doc describing API
# + methods to parse useful headers: content-type, content-disposition, etc
# + methods to send generic responses: 404, 403, ...
# + method to send a response anytime (need to store start_response in self.req)
# + method to disable logging (if log_level=None) and to add a dummy handler
# + init option to enable debug messages or not
# + init option to set parent proxy
# + only read request body and response body when needed, or add methods
#   adapt_req_headers and adapt_resp_headers
# + close http connection after receiving response from server
# - later, reuse http connection when no connection close header or keep-alive
# - CLI parameters to set options (should be extensible by subclasses)
# ? config file to set options?
# ? use urllib2 instead of httplib?


#--- IMPORTS ------------------------------------------------------------------

from cherrypy import wsgiserver
import urlparse, urllib2, httplib, sys, threading, logging


#--- CONSTANTS ----------------------------------------------------------------

__version__ = '0.07'

SERVER_NAME = 'CherryProxy/%s' % __version__


#=== CLASSES ==================================================================

class CherryProxy (object):

    def __init__(self, address='0.0.0.0', port=8070, server_name=SERVER_NAME,
        debug=False, log_level=logging.INFO):
        """
        CherryProxy constructor
        """
        print 'CherryProxy listening on %s:%d (press Ctrl+C to stop)' % (address, port)
        self.server = wsgiserver.CherryPyWSGIServer((address, port),
            self.proxy_app, server_name=server_name)
        # thread local variables to store request/response data per thread:
        self.req = threading.local()
        self.resp = threading.local()
        if debug:
            self.debug = self.debug_enabled
            self.debug_mode = True
        else:
            self.debug = self.debug_disabled
            self.debug_mode = False
        self.log = logging.getLogger('CProxy')
        self.log.setLevel(log_level)


    def start(self):
        """
        start proxy server
        """
        self.server.start()


    def stop(self):
        """
        stop proxy server
        """
        self.server.stop()


    def debug_enabled(self, string):
        """
        debug method when debug mode is enabled
        """
        #print string
        self.log.debug(string)

    def debug_disabled(self, string):
        """
        debug method when debug mode is disabled (does nothing)
        """
        pass


    def init_request_response(self):
        """
        Initialize variables when a new request is received
        """
        # request variables
        self.req.environ = {}
        self.req.headers = {}
        self.req.method = None
        self.req.scheme = None
        self.req.netloc = None
        self.req.path = None
        self.req.query = None
        self.req.url = None
        self.req.length = 0
        self.req.data = None
        # response variables
        self.resp.response = None
        self.resp.status = None
        self.resp.reason = None
        self.resp.headers = {}
        self.resp.data = None


    def parse_request(self, environ):
        """
        parse a request received from a client
        """
        self.req.environ = environ
        self.debug('_'*50)
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
        self.debug('- '*25)
        self.log.info('Request %s' % (self.req.url))
        # init values before reading request body
        self.req.length = 0
        self.req.data = None


    def read_request_body(self):
        """
        read the request body if available
        """
        environ = self.req.environ
        # if request has data, read it:
        if 'CONTENT_LENGTH' in environ:
            self.req.length = int(environ['CONTENT_LENGTH'])
            self.debug('REQUEST BODY: content-length=%d' % self.req.length)
            self.req.data = environ['wsgi.input'].read(self.req.length)
            self.debug(self.req.data)
        else:
            self.req.length = 0
            self.req.data = None
            self.debug('No request body.')


    def adapt_request(self):
        """
        Method to be overridden:
        Called to analyse/filter/modify the request received from the client,
        after reading the full request with its body if there is one,
        before it is sent to the server.
        """
        pass


    def send_request(self):
        """
        forward a request received from a client to the server
        Get the response (but not the response body yet)
        """
        self.debug('- '*25)
        # send request to server:
        conn = httplib.HTTPConnection(self.req.netloc)
        if self.debug_mode:
            conn.set_debuglevel(1)
        conn.request(self.req.method, self.req.url, body=self.req.data, headers=self.req.headers)
        self.resp.response = conn.getresponse()
        self.resp.status = self.resp.response.status
        self.resp.reason = self.resp.response.reason
        status = "%d %s" % (self.resp.status, self.resp.reason) #'200 OK'
        self.debug('- '*25)
        self.debug('RESPONSE RECEIVED FROM SERVER:')
        self.debug(status)
        self.resp.headers = self.resp.response.getheaders() #[('Content-type','text/plain')]
        for h in self.resp.headers:
            self.debug(' - %s: %s' % (h[0], h[1]))
        self.log.info('Response %s' % (status))



    def read_response_body(self):
        """
        read the response body and close the connection
        """
        # TODO: check content-length?
        self.resp.data = self.resp.response.read()
##        print '- '*39
##        print repr(self.data)
        # For now we always close the connection, even if the client sends
        # several requests in one connection:
        # (not optimal performance-wise, but simpler to code)
        self.resp.response.close()


    def adapt_response(self):
        """
        Method to be overridden:
        Called to analyse/filter/modify the response received from the server,
        after reading the full response with its body if there is one,
        before it is sent back to the client.
        """
        pass


    def send_response(self, start_response):
        """
        send the response with headers (but no body yet)
        """
        status = "%d %s" % (self.resp.status, self.resp.reason) #'200 OK'
        self.debug('- '*25)
        self.debug('RESPONSE SENT TO CLIENT:')
        self.debug(status)
        for h in self.resp.headers:
            self.debug(' - %s: %s' % (h[0], h[1]))
        start_response(status, self.resp.headers)


    def proxy_app(self, environ, start_response):
        """
        main method called when a request is received from a client
        (WSGI application)
        """
        # parse request headers:
        self.parse_request(environ)
        # if request has data, read it:
        self.read_request_body()
        # adapt request before sending it to server:
        self.adapt_request()
        # send request to server:
        self.send_request()
        # read the response body
        self.read_response_body()
        # adapt response before sending it to client:
        self.adapt_response()
        # send response to client:
        self.send_response(start_response)
        # send response body:
        return [self.resp.data]


#=== MAIN =====================================================================

if __name__ == '__main__':
    # simple CherryProxy without filter:
    debug=False
    log_level = logging.INFO
    try:
        if sys.argv[1] == '-d':
            debug=True
            log_level = logging.DEBUG
    except:
        pass

    # setup logging
    logging.basicConfig(format='%(name)s-%(thread)05d: %(levelname)-8s %(message)s', level=logging.DEBUG)

    print __doc__
    proxy = CherryProxy(debug=debug, log_level=log_level)
    while True:
        try:
            proxy.start()
        except KeyboardInterrupt:
            proxy.stop()
            sys.exit()
