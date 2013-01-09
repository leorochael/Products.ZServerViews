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
Handler classes for ZServer Views 
'''
from ZServer.HTTPServer import CONTENT_LENGTH
from ZServer.HTTPServer import zhttp_handler
from ZServer.medusa.http_server import get_header
from ZServer import DebugLogger
from ZServer.HTTPResponse import ChannelPipe as BaseChannelPipe

from logging import getLogger

log = getLogger(__name__)

class ChannelPipe(BaseChannelPipe):

    def start_response(self, status, headers, exc_info=None):
        header_map = dict((header.lower(), value) for header, value in headers)
        # close the connection if requested, or if we have no content length
        if header_map.get('connection', '') =='close':
            self._close = 1
        if (not header_map.get('content-length', None) and
            header_map.get('transfer-encoding', None) != 'chunked'):
            # missing lenght and not chunked encoding: non HTTP/1.1 compliant
            self._close = 1
            self._request.version = '1.0'
        return BaseChannelPipe.start_response(self, status, headers, exc_info)

class ZServerViewHandler(zhttp_handler):
    '''
    Handles connections and serves views directly from the ZServer thread
    '''

    def __init__(self, config):
        zhttp_handler.__init__(self, __name__, uri_base='/')
        self.config = config

    def match(self, request):
        # NOTE: request.split_url() is more like urlparse than urlsplit
        # so we don't use it here, but we don't need the full urlsplilt
        # functionality either
        path, _ = request.uri.split('?', 1)
        return path in self.config

    def get_view(self, env):
        #from ZServer.HTTPResponse import make_response
        #from ZPublisher.HTTPRequest import HTTPRequest
        #request = env['ZServer.medusa.http_server.http_request']
        #stdin = env['stdin']
        #zresponse=make_response(request,env)
        #zresponse._http_connection = 'close'
        #zrequest=HTTPRequest(stdin, env, zresponse)
        path = env['PATH_INFO']
        view = self.config[path]
        env['SCRIPT_NAME'] += path
        env['PATH_INFO'] = ''
        return view

    def continue_request(self, sin, request):
        "continue handling request now that we have the stdin"

        s=get_header(CONTENT_LENGTH, request.header)
        if s:
            s=int(s)
        else:
            s=0
        DebugLogger.log('I', id(request), s)
        env=self.get_environment(request)
        path, _ = request.uri.split('?', 1)
        env['PATH_INFO'] += path
        # why not do the above in self.get_environment(request)?
        env['stdin'] = sin
        env['ZServer.medusa.http_server.http_request'] = request
        try:
            channel_pipe = ChannelPipe(request)
            view = self.get_view(env)
            # mini WSGI server:
            result = view(env, channel_pipe.start_response)
            for part in result:
                channel_pipe.write(part)
            channel_pipe.close()
            request.channel.current_request=None
        except:
            log.exception("Failure calling view for %r with env:\n%s\n" %
                          (path, env))
            raise
