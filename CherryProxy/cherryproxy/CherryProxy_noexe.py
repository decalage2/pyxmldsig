"""
Simple CherryProxy demo

This demo simply blocks EXE files (application/octet-stream) and allows
everything else.

usage: CherryProxy_noexe.py [-d]

-d: debug mode

Philippe Lagadec 2010-04-30
"""

import CherryProxy, sys

class CherryProxy_noexe(CherryProxy.CherryProxy):
    """
    Sample CherryProxy class demonstrating how to adapt a response.
    This demo simply blocks EXE files and allows everything else.
    """
    def adapt_response(self):
        headers = dict([(key.lower(),value) for key, value in self.resp_headers])
        if headers.get('content-type', '').lower() == 'application/octet-stream':
            # it's a zip file, return a 403 Forbidden response:
            self.status = 403
            self.reason = 'Unauthorized by policy'
            self.data = "%d %s" % (self.status, self.reason)
            self.resp_headers = []
            self.resp_headers.append(('content-type', 'text/plain'))
            self.resp_headers.append(('content-length', str(len(self.data))))

debug=False
try:
    if sys.argv[1] == '-d':
        debug=True
except:
    pass

print __doc__
proxy = CherryProxy_noexe(debug=debug)
print 'Press Ctrl+C to stop the proxy'
while True:
    try:
        proxy.start()
    except KeyboardInterrupt:
        proxy.stop()
        sys.exit()
