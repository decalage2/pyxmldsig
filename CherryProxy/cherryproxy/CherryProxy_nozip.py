"""
Simple CherryProxy demo

This demo simply blocks zip files and allows everything else.

Philippe Lagadec 2010-04-25
"""

import CherryProxy, sys

class CherryProxy_nozip(CherryProxy.CherryProxy):
    """
    Sample CherryProxy class demonstrating how to adapt a response.
    This demo simply blocks zip files and allows everything else.
    """
    def adapt_response(self):
        headers = dict([(key.lower(),value) for key, value in self.resp_headers])
        if headers.get('content-type', '').lower() == 'application/zip':
            # it's a zip file, return a 403 Forbidden response:
            self.status = 403
            self.reason = 'Unauthorized by policy'
            self.data = "%d %s" % (self.status, self.reason)
            self.resp_headers = []
            self.resp_headers.append(('content-type', 'text/plain'))
            self.resp_headers.append(('content-length', str(len(self.data))))

proxy = CherryProxy_nozip()
while True:
    try:
        proxy.start()
    except KeyboardInterrupt:
        proxy.stop()
        sys.exit()
