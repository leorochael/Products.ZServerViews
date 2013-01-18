Introduction
============

This Zope add-on product provides for easy configuration of ZServer Views.

It was authored by Leonardo Rochael Almeida, and sponsored by OpenMultimedia.

A ZServer View is a (supposedly) small and fast WSGI_ application that runs
directly from within the ZServer thread (a.k.a. medusa thread).

This means that a ZServer View will run even if all Zope worker-threads are
busy handling other requests. It also means that if a ZServer View is not fast,
then it is blocking the ZServer from handling incoming requests for all worker
threads, so be mindful when using this product.

ZServer Views are mostly useful for system monitoring tools, like
`DeadlockDebugger` or Zope resource monitoring.

Installation
============

Add `Products.ZServerViews` to the list of eggs of the part that defines your
Zope instance.

Configuration
=============

Add a `product-config` section for `zserver-views` to your Zope
configuration (e.g. the `zope.conf` file or a `zope-conf-additional` parameter
in your buildout configuration).

Each entry in this section should contain an identifier (must be unique within
the section but are currently unused [1]_), a URL path and the dotted
name of the view which will be served from that URL path, all separated by
whitespace. For example::

  <product-config zserver-views>
      my-package /my/view my.package.mymodule.my_view
      thread-id /thr-id Products.ZServerViews.tests.common.current_thread_id_zserver_view
  </environment>

This means that the `http://yourserver/my/view` URL will run the WSGI app at
`my.package.mymodule.my_view` and the url at `http://yourserver/thr-id` will
run the `Products.ZServerViews.tests.common.current_thread_id_zserver_view`
WSGI view.

Query strings, if present, will be passed to the ZServer Views, but sub-paths
will not. I.e., `http://yourserver/my/view?foo=bar` will run
`my.package.mymodule.my_view`, but `http://yourserver/thrid/fred` will not run
the `Products.ZServerViews.tests.common.current_thread_id_zserver_view` view,
but will be handled by Zope directly.

This behaviour is intentional, and reflects the fact that ZServer View location
is decided by a single dictionary lookup, instead of multiple regex or
substring matching.

.. [1] The identifiers in `product-config` keys cannot be composed
   of many valid URL characters, and are forcibly lower-cased, so they're
   useless for either the URL or the dotted name of the view.

Writing ZServer Views
=====================

ZServer Views are mini WSGI apps, which mean they take an `env` and a
`start_response` parameter, and return the bytes that must be
sent to the browser. The query string, if any, will be passed into
`env['QUERY_STRING']`.

For HTTP/1.1 compatibility they must either pass a "Content-Lenght" header into
`start_response()` or a "Transfer-Encoding=chunked" header and chunk the
content. If neither is done, the response will fall back to `HTTP/1.0`
automatically, and the connection will be forced close.

To ease the creation of these mini apps, a decorator exists
(`Products.ZServerViews.base import TextView`) that can wrap
a function receiving only the `env` parameter and returns a single `unicode`
string. This decorator will take care of all the WSGI conversation around that
response.

Check `Products.ZServerViews.tests.common.current_thread_id_zserver_view` for
an example.

.. _WSGI: http://wsgi.org/
