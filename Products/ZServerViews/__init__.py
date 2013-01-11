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

def initialize(context):
    from App.config import getConfiguration
    zope_conf = getConfiguration()
    install_handler(zope_conf)

def install_handler(zope_conf):
    from Products.ZServerViews.handler import ZServerViewHandler
    product_config = get_product_config(zope_conf)
    server_list = get_server_to_graft_list(zope_conf)
    if product_config and server_list:
        handler_config = get_handler_configuration(product_config)
        handler = ZServerViewHandler(handler_config)
        for server in server_list:
            server.install_handler(handler)

def get_product_config(zope_conf):
    return getattr(zope_conf, 'product_config', {}).get('zserver-views')

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
    return [server for server in zope_conf.servers
            if get_class_dotted_name(server) in GRAFT_SERVER_CLASS_SET]
