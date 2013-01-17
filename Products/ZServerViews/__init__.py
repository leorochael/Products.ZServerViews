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

GRAFT_SERVER_CLASS_SET = set('''
ZServer.HTTPServer.zhttp_server
'''.strip().splitlines())
# TODO: perhaps allow configuration of the set above through zope.conf.
# In any case, it can be safely updated by other modules at import time, since
# it's only used at "Product initialization" time.

CONFIG_KEY = 'zserver-views'

_zserver_view_handler = None

def initialize(context):
    from App.config import getConfiguration
    zope_conf = getConfiguration()
    configure_server_handler(zope_conf)

def remove_handler(server_list):
    global _zserver_view_handler
    if _zserver_view_handler is not None:
        for server in server_list:
            server.remove_handler(_zserver_view_handler)
    _zserver_view_handler = None

def add_handler(handler, server_list):
    global _zserver_view_handler
    _zserver_view_handler = handler
    for server in server_list:
        server.install_handler(_zserver_view_handler)

def configure_server_handler(zope_conf):
    from Products.ZServerViews.handler import ZServerViewHandler
    product_config = get_product_config(zope_conf)
    server_list = get_server_to_graft_list(zope_conf)
    if not server_list:
        return
    if product_config:
        handler_config = get_handler_configuration(product_config)
        if _zserver_view_handler is None:
            handler = ZServerViewHandler(handler_config)
            add_handler(handler, server_list)
        else:
            _zserver_view_handler.update_configuration(handler_config)
    else:
        # configuration is empty, remove handler
        remove_handler(server_list)

def get_product_config(zope_conf):
    return zope_conf.product_config.get(CONFIG_KEY)

def update_configuration(new_conf):
    from App.config import getConfiguration
    zope_conf = getConfiguration()
    product_config = zope_conf.product_config.setdefault(CONFIG_KEY, {})
    product_config.update(new_conf)
    configure_server_handler(zope_conf)

def get_handler_configuration(product_config):
    from Zope2.Startup.datatypes import importable_name
    handler_config = {}
    for entry in product_config.values():
        path, dotted_name = entry.split()
        handler_config[path] = importable_name(dotted_name)
    return handler_config

def get_class_dotted_name(instance):
    cls = instance.__class__
    return cls.__module__ + '.' + cls.__name__

def get_server_to_graft_list(zope_conf):
    result = [server for server in getattr(zope_conf, 'servers', ())
              if get_class_dotted_name(server) in GRAFT_SERVER_CLASS_SET]
    return result
