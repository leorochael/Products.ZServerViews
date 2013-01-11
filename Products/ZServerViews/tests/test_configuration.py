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
    zope_conf = None

    def setUp(self):
        test_logger.LoggingTestBase.setUp(self)
        self.TEMPNAME = mkdtemp()
        if self.schema is None:
            from Zope2.Startup.tests.testStarter import getSchema
            ZopeStarterTestCase.schema = getSchema()

    def tearDown(self):
        rmtree(self.TEMPNAME)
        test_logger.LoggingTestBase.tearDown(self)
        if self.zope_conf is not None:
            del self.zope_conf.servers # should release servers

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

    def load_config_text_and_start_servers(self, zope_conf_text):
        from App.config import setConfiguration
        self.zope_conf = self.load_config_text(zope_conf_text)
        starter = self.get_starter(self.zope_conf)
        setConfiguration(self.zope_conf)
    # do the job the 'handler' would have done (call prepare)
        for server in self.zope_conf.servers:
            server.prepare('', None, 'Zope2', {}, None)
        
        starter.setupServers()
        return self.zope_conf

    def test_zserver_views_configuration(self):
        from ZServer.HTTPServer import zhttp_handler
        from Products.ZServerViews.handler import ZServerViewHandler
        from Products.ZServerViews.tests.common import current_thread_id_zserver_view
        import Products.ZServerViews
        zope_conf_text = """
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
        """
        conf = self.load_config_text_and_start_servers(zope_conf_text)
        import ZServer
        # We should have two configured servers:
        zhttp_server, zftp_server = conf.servers
        self.assertEqual(zhttp_server.__class__,
                         ZServer.HTTPServer.zhttp_server)
        self.assertEqual(zftp_server.__class__,
                         ZServer.FTPServer)
        # At this point, Only the standard zhttp_handler should be present
        # in the HTTP server:
        self.assertEqual([handler.__class__ for handler in zhttp_server.handlers],
                         [zhttp_handler])
        original_handler, = zhttp_server.handlers
        # Now we call the product initialization for Products.ZServerViews.
        # We don't need to pass a real context.
        Products.ZServerViews.initialize(None)
        # This configures the extra handler into the http_server,
        # inserting it first.
        self.assertEqual(
            [handler.__class__ for handler in zhttp_server.handlers],
            [ZServerViewHandler, zhttp_handler],)
        self.assertEqual(zhttp_server.handlers[-1], original_handler,)
        # Our installed handler should have the configuration we passed:
        zserver_handlers = zhttp_server.handlers
        handler, _ = zserver_handlers
        self.assertTrue(handler._match_uri('/foo'))
        env = dict(PATH_INFO='/foo', SCRIPT_NAME='')
        view = handler.get_view(env)
        self.assertEqual(view, current_thread_id_zserver_view)
        self.assertEqual(env, dict(PATH_INFO='', SCRIPT_NAME='/foo'))
        self.assertFalse(handler._match_uri('/bar'))
        self.assertFalse(handler._match_uri('/'))
        # The configuration should be idempotent. I.e. calling it again
        # should result in the same state.
        Products.ZServerViews.initialize(None)
        self.assertEqual(zserver_handlers, zhttp_server.handlers)
        # Emptying the configuration should remove our special handler
        del conf.product_config['zserver-views']
        Products.ZServerViews.initialize(None)
        self.assertEqual([original_handler], zhttp_server.handlers)
        # And there's an API for other products to insert their own keys
        # into our configuration
        Products.ZServerViews.update_configuration(
            {'id-view-2': '/bar Products.ZServerViews.tests.common.current_thread_id_zserver_view'})
        env = dict(PATH_INFO='/bar', SCRIPT_NAME='')
        handler = zhttp_server.handlers[0]
        view = handler.get_view(env)
        self.assertEqual(view, current_thread_id_zserver_view)
        self.assertEqual(env, dict(PATH_INFO='', SCRIPT_NAME='/bar'))
        # the old url for the view no longer works because we had cleared it
        # earlier.
        self.assertTrue(handler._match_uri('/bar'))
        self.assertFalse(handler._match_uri('/foo'))
        # But the update is additive:
        Products.ZServerViews.update_configuration(
            {'id-view-3': '/foo Products.ZServerViews.tests.common.current_thread_id_zserver_view'})
        handler = zhttp_server.handlers[0]
        self.assertTrue(handler._match_uri('/bar'))
        self.assertTrue(handler._match_uri('/foo'))
        self.assertFalse(handler._match_uri('/baz'))
