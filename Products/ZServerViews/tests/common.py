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

import thread
from Products.ZServerViews.base import TextView

def current_thread_id():
    return str(thread.get_ident())

@TextView
def current_thread_id_zserver_view(environment):
    return current_thread_id()

class App(object):
    "A publishable app"
    # docstring above necessary for this object to be traversable

    def __bobo_traverse__(self, REQUEST, name):
        return self

    def __call__(self, REQUEST):
        return current_thread_id()

# Enable this module to be published by ZServer
bobo_application = App()

import logging
LOG = logging.getLogger('ZServerPublisher')

# XXX: Horrible, horrible patch because the experimental implementation of
# wsgi on Zope broke regular module publishing for anything other than a module
# called "Zope2"
def patch_ZServerPublisher():

    # define the patched function here to keep the same indentation
    def ZServerPublisher__init__(self, accept):
        from sys import exc_info
        from ZPublisher import publish_module
        from ZPublisher.WSGIPublisher import publish_module as publish_wsgi
        while 1:
          try:
            name, a, b=accept()
            if name == "Zope2WSGI":
                try:
                    res = publish_wsgi(a, b)
                    for r in res:
                        a['wsgi.output'].write(r)
                finally:
                    # TODO: Support keeping connections open.
                    a['wsgi.output']._close = 1
                    a['wsgi.output'].close()
            else: # originally "if name == "Zope2"
                try:
                    publish_module(
                        name,
                        request=a,
                        response=b)
                finally:
                    b._finish()
                    a=b=None

          except:
            LOG.error('exception caught', exc_info=True)
    from ZServer.PubCore.ZServerPublisher import ZServerPublisher
    _original = ZServerPublisher.__init__
    ZServerPublisher__init__._original = _original
    ZServerPublisher__init__.__name__ = _original.__name__
    ZServerPublisher.__init__ = ZServerPublisher__init__

def unpatch_ZServerPublisher():
    from ZServer.PubCore.ZServerPublisher import ZServerPublisher
    ZServerPublisher.__init__ = ZServerPublisher.__init__._original
