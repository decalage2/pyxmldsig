"""
Simple CherryProxy demo

This demo simply blocks EXE files (application/octet-stream) and allows
everything else.

usage: CherryProxy_noexe.py [-d]

-d: debug mode

Philippe Lagadec 2010-04-30
"""

import sys
sys.path.append('../..')
import cherryproxy

class CherryProxy_blockexe(cherryproxy.CherryProxy):
    """
    Sample CherryProxy class demonstrating how to adapt a response.
    This demo simply blocks EXE files and allows everything else.
    """
    def filter_response(self):
        if self.resp.content_type == 'application/octet-stream'\
        or (isinstance(self.resp.data, str) and self.resp.data.startswith('MZ')):
            # it's an exe file, return a 403 Forbidden response:
            self.set_response_forbidden()

cherryproxy.main(CherryProxy_blockexe)
