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

import cStringIO

from tempfile import mkdtemp
from shutil import rmtree

import ZConfig

from ZConfig.components.logger.tests import test_logger

# NOTE: Large sections of this file were pulled from
# Zope2.Startup.tests.testStarter, since we can't reuse the test case class
# without running the test cases,

class ZopeStarterTestCase(test_logger.LoggingTestBase):

    schema = None
    TEMPNAME = None

    def setUp(self):
        test_logger.LoggingTestBase.setUp(self)
        self.TEMPNAME = mkdtemp()
        if self.schema is None:
            from Zope2.Startup.tests.testStarter import getSchema
            ZopeStarterTestCase.schema = getSchema()

    def tearDown(self):
        rmtree(self.TEMPNAME)
        test_logger.LoggingTestBase.tearDown(self)

    def load_config_text(self, text):
        # We have to create a directory of our own since the existence
        # of the directory is checked.  This handles this in a
        # platform-independent way.
        schema = self.schema
        sio = cStringIO.StringIO(
            text.replace("<<INSTANCE_HOME>>", self.TEMPNAME))
        conf, self.handler = ZConfig.loadConfigFile(schema, sio)
        self.assertEqual(conf.instancehome, self.TEMPNAME)
        return conf

    def get_starter(self, conf):
        import Zope2.Startup
        starter = Zope2.Startup.get_starter()
        starter.setConfiguration(conf)
        return starter

    def test_zserver_views_configuration(self):
        from ZServer.HTTPServer import zhttp_handler
        from Products.ZServerViews.handler import ZServerViewHandler
        from Products.ZServerViews.tests.common import current_thread_id_zserver_view
        from App.config import setConfiguration
        import Products.ZServerViews
        conf = self.load_config_text("""
            instancehome <<INSTANCE_HOME>>
            <http-server>
                address 18092
                fast-listen off
            </http-server>
            <ftp-server>
               address 18093
            </ftp-server>

            <product-config zserver-views>
                id-view /foo Products.ZServerViews.tests.common.current_thread_id_zserver_view
            </product-config>
        """)
        starter = self.get_starter(conf)
        setConfiguration(conf)
        # do the job the 'handler' would have done (call prepare)
        for server in conf.servers:
            server.prepare('', None, 'Zope2', {}, None)
        try:
            starter.setupServers()
            import ZServer
            # We should have two configured servers:
            zhttp_server, zftp_server = conf.servers
            self.assertEqual(zhttp_server.__class__,
                             ZServer.HTTPServer.zhttp_server)
            self.assertEqual(zftp_server.__class__,
                             ZServer.FTPServer)
            # At this point, Only the standard zhttp_handler should be present
            # in the HTTP server:
            self.assertEqual(
                [handler.__class__ for handler in zhttp_server.handlers],
                [zhttp_handler],)
            # Now we call the product initialization for Products.ZServerViews.
            # We don't need to pass a real context.
            Products.ZServerViews.initialize(None)
            # This configures the extra handler into the http_server,
            # inserting it first.
            self.assertEqual(
                [handler.__class__ for handler in zhttp_server.handlers],
                [ZServerViewHandler, zhttp_handler],)
            # Our installed handler should have the configuration we passed:
            handler, _ = zhttp_server.handlers
            env = dict(PATH_INFO='/foo', SCRIPT_NAME='')
            view = handler.get_view(env)
            self.assertEqual(view, current_thread_id_zserver_view)
            self.assertEqual(env, dict(PATH_INFO='', SCRIPT_NAME='/foo'))
        finally:
            del conf.servers # should release servers
            pass
