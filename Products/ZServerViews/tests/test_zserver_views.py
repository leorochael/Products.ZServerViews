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

import unittest2 as unittest
from urlparse import urljoin
from urllib2 import urlopen

from threading import Thread, Event
from .common import __name__ as bobo_app_name
from .common import patch_ZServerPublisher
from .common import unpatch_ZServerPublisher
from .common import current_thread_id_zserver_view
import os
import sys
import time

# Attribution: large blocks of text related to ZServer handling were lifted
# from plone.testing.z2 and changed slightly.

class ZServerThread(Thread):
    """Thread for the main asyncore loop.
    """

    __timeout = 1
    __should_stop = False
    __started = Event()

    def start(self):
        result = super(ZServerThread, self).start()
        self.__started.wait()
        return result

    def run(self):
        try:
            self.__started.set()
            import asyncore
            # Poll
            socket_map = asyncore.socket_map
            while not self.__should_stop and socket_map:
                asyncore.poll(self.__timeout, socket_map)
        except:
            import traceback
            traceback.print_exc()
            raise

    def stop(self):
        self.__should_stop = True
        self.join()

class DumperThread(Thread):
    """Used only while debugging"""

    __timeout = 4
    __should_stop = False

    def __init__(self, *args, **kw):
        super(DumperThread, self).__init__(*args, **kw)
        self.start()

    def dump_frames(self):
        import traceback
        current_frames = sys._current_frames()
        print >> sys.stderr, "@@@ Dumping:", current_frames.keys()
        for ident, frame in current_frames.items():
            print >> sys.stderr, "Thread:", ident
            traceback.print_stack(frame, sys.stderr)
        print >> sys.stderr

    def run(self):
        try:
            while not self.__should_stop:
                self.dump_frames()
                time.sleep(self.__timeout)
        except:
            import traceback
            traceback.print_exc()
            raise

    def stop(self):
        self.__should_stop = True
        self.join()

class TestZServerViews(unittest.TestCase):

    host = os.environ.get('ZSERVER_HOST', 'localhost')
    port = int(os.environ.get('ZSERVER_PORT', 55001))

    def setUp(self):
        patch_ZServerPublisher()
        self.base_url = 'http://%s:%s/' % (self.host, self.port)
        #self.dthread = DumperThread() # XXX: remove
        self.setUpZServerThread()

    def tearDown(self):
        self.tearDownZServerThread() # XXX: remove
        #self.dthread.stop()
        unpatch_ZServerPublisher()

    def setUpZServerThread(self):
        """Create a ZServer server instance and its thread

        Save them, respectively, in self.zserver and self.thread
        """

        from ZServer import zhttp_server, zhttp_handler, logger
        from cStringIO import StringIO

        zlog = logger.file_logger(StringIO())

        zserver = zhttp_server(ip=self.host,
                               port=self.port, 
                               resolver=None,
                               logger_object=zlog)
        zhandler = zhttp_handler(module=bobo_app_name, uri_base='')
        zserver.install_handler(zhandler)

        self.zserver = zserver
        name = self.__class__.__name__
        self.zthread = ZServerThread(name="%s server" % name)
        self.zthread.start()

    def tearDownZServerThread(self):
        """Close the ZServer socket
        """
        self.zserver.close()
        self.zthread.stop()

    def _request(self, url='', data=None):
        full_url = urljoin(self.base_url, url)
        conn = urlopen(full_url, data)
        return conn.read()

    def xtest_dummy(self):
        #self.dthread = DumperThread() # XXX: remove
        import IPython; IPython.embed()
        return
        try:
            while True:
                time.sleep(1)
                #break
        except KeyboardInterrupt:
            pass
        finally:
            #self.dthread.stop()
            pass

    def test_worker_thread_not_zserver_thread(self):
        # this is the default behaviour of the worker thread, we test it to
        # make sure our test infrastructure works.
        for url in "/ /foo/bar /foo/?query".split():
            # get the worker thread id which the published module returns to us
            result = self._request(url)
            worker_thread_id = int(result)
            current_frames = sys._current_frames()
            # both the medusa thread and the worker thread used are alive:
            self.assertIn(worker_thread_id, current_frames)
            self.assertIn(self.zthread.ident, current_frames)
            # but they aren't the same:
            self.assertNotEqual(worker_thread_id, self.zthread.ident)

    def test_manually_configure_ZServerView_handler(self):
        from Products.ZServerViews.handler import ZServerViewHandler
        config = {'/foo': current_thread_id_zserver_view}
        handler = ZServerViewHandler(config)
        self.zserver.install_handler(handler)
        self.addCleanup(lambda: self.zserver.remove_handler(handler))
        # check the view was installed in the requested url
        result = self._request('/foo?bar=baz')
        view_thread_id = int(result)
        # the thread_id used by the ZServerView should be the zserver thread_id
        self.assertEqual(view_thread_id, self.zthread.ident)

    # TODO: test which URLs are handled which way.

def test_suite():
    return unittest.TestSuite((
         unittest.makeSuite(TestZServerViews),
    ))
