##############################################################################
#
# Copyright (c) 2013 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
import sys

'''
Base classes for ZServer Views
'''

class ViewError(Exception):

    def __init__(self, status, headers=(), message=u''):
        self.status = status
        self.headers = headers
        self.message = message
        super(ViewError, self).__init__(status + '\n'+ message)

class TextView(object):
    """Decorator for a ZServer view callable to render a small text snippet
    
    The text snippet must be unicode, but the view doesn't have to care about
    start_response(), only return the text
    """

    def __init__(self, func):
        self.func = func

    def __call__(self, environment, start_response):
        headers = [('Content-Type', 'text/plain; charset=utf-8'),]
        try:
            result = self.func(environment)
        except ViewError:
            # python 3 compat: get exception from sys.exc_info()
            # instead of directly
            _c, error, _tb = sys.exc_info()
            status = error.status
            headers.extend(error.headers)
            result = error.message
            del _c, error, _tb
        else:
            status = '200 OK'
        result = result.encode('utf-8')
        length = str(len(result))
        headers.append(('Content-Length', length))
        start_response(status, headers)
        return [result]
