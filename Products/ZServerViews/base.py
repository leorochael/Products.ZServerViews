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

'''
Base classes for ZServer Views
'''

class TextView(object):
    """Decorator for a ZServer view callable to render a small text snippet
    
    The text snippet must be unicode, but the view doesn't have to care about
    start_response(), only return the text
    """

    def __init__(self, func):
        self.func = func

    def __call__(self, environment, start_response):
        result = self.func(environment).encode('utf-8')
        length = str(len(result))
        start_response('200 OK', [('Content-Type', 'text/plain; charset=utf-8'),
                                  ('Content-Length', length),],)
        return [result]
