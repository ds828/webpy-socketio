
State of webpy-socketio
========================

webpy-socketio inherits from django-socketio. 
I just make it run on the webpy framewrok.

Introduction
============

The features provided by webpy-socketio are:

  * A channel subscription and broadcast system that extends
    Socket.IO allowing WebSockets and events to be partitioned into
    separate concerns
  * A `signals`_-like event system that abstracts away the various
    stages of a Socket.IO request
  * Support for out-of-band (non-event) broadcasts
  * The required views, urlpatterns, templatetags and tests for all
    the above

Installation
============

Note that if you've never installed gevent, you'll first need to
install the libevent development library. You may also need the Python
development library if not installed. This can be achieved on Debian
based sytems with the following commands::

    $ sudo apt-get install python-dev
    $ sudo apt-get install libevent-dev
    $ sudo apt-get install python-gevent

Download gevent from http://www.gevent.org/

	$ sudo python setup.py install
    
You can download webpy-socketio and install it directly
from source::

    $ python setup.py install

Once installed you can then add ``webpy_socketio.socketio_urls`` to your url conf::

	urls = (
		...
    )

	urls += socketio_urls

The client-side JavaScripts for Socket.IO and its extensions can then 
be added to any page with the ``socketio`` templatetag::

    <head>
		<!-- Mako template -->
        <%include file="socketio_scripts.html"/>
        <script>
            var socket = new io.Socket();
            socket.connect();
            // etc
        </script>
    </head>

Running
=======

Please see main_app.py in the example directory::

	#sample 
	import web
	from socketio import SocketIOServer
	from gevent import monkey 
	monkey.patch_all()
	from webpy_socketio import *
	
	urls = (
		...
    )

	urls += socketio_urls

	app = web.application(urls, globals())
    
    SOCKETIO_HOST = ""
	SOCKETIO_PORT = 8000
	
	application = app.wsgifunc()

	if __name__ == "__main__":

		SocketIOServer((SOCKETIO_HOST, SOCKETIO_PORT), application, resource="socket.io").serve_forever()

Note that the host and port can also configured by defining the following
settings in your project's settings module:

    * ``SOCKETIO_HOST`` - The host to bind the server to.
    * ``SOCKETIO_PORT`` - The numeric port to bind the server to.

.. note::

    On UNIX-like systems, in order for the ``flashsocket`` transport
    fallback to work, root privileges (eg by running the above command
    with ``sudo``) are required when running the server. This is due to
    the `Flash Policy Server`_ requiring access to a `low port`_ (843).
    This isn't strictly required for everything to work correctly, as
    the ``flashsocket`` transport is only used as one of several
    fallbacks when WebSockets aren't supported by the browser.

Channels
========

The WebSocket implemented by gevent-websocket provides two methods for
sending data to other clients, ``socket.send`` which sends data to the
given socket instance, and ``socket.broadcast`` which sends data to all
socket instances other than itself.

A common requirement for WebSocket based applications is to divide
communications up into separate channels. For example a chat site may
have multiple chat rooms and rather than using ``broadcast`` which
would send a chat message to all chat rooms, each room would need a
reference to each of the connected sockets so that ``send`` can be
called on each socket when a new message arrives for that room.

webpy-socketio extends Socket.IO both on the client and server to
provide channels that can be subscribed and broadcast to.

To subscribe to a channel client-side in JavaScript use the
``socket.subscribe`` method::

    var socket = new io.Socket();
    socket.connect();
    socket.on('connect', function() {
        socket.subscribe('my channel');
    });

Once the socket is subscribed to a channel, you can then
broadcast to the channel server-side in Python using the
``socket.broadcast_channel`` method::

  socket.broadcast_channel("my message")

Broadcast and Send Methods
==========================

Each server-side socket instance contains a handful of methods
for sending data. As mentioned above, the first two methods are
implemented by `gevent-socketio`_:

  * ``socket.send(message)`` - Sends the given message directly to
    the socket.
  * ``socket.broadcast(message)`` - Sends the given message to all
    other sockets.

The remaning methods are implemented by webpy-socketio.

  * ``socket.broadcast_channel(message, channel=None)`` - Sends the
    given message to all other sockets that are subscribed to the
    given channel. If no channel is given, all channels that the
    socket is subscribed to are used.
    the socket.
  * ``socket.send_and_broadcast(message)`` - Shortcut that sends the
    message to all sockects, including the sender.
  * ``socket.send_and_broadcast_channel(message, channel=None)``
    - Shortcut that sends the message to all sockects for the given
    channel, including the sender.

The following methods can be imported directly from
``webpy_socketio`` for broadcasting and sending out-of-band (eg: not
in response to a socket event). These methods map directly to the same
methods on a socket instance, and in each case an appropriate connected
socket will be chosen to use for sending the message, and the
``webpy_socketio.NoSocket`` exception will be raised if no connected
sockets exist.

  * ``webpy_socketio.broadcast(message)``
  * ``webpy_socketio.broadcast_channel(message, channel)``
  * ``webpy_socketio.send(session_id, message)``

Note that with the ``send`` method, the socket is identified by its
session ID, accessible via ``socket.session.session_id``. This is a
WebSocket session ID and should not be confused with a Webpy session
ID which is different.

Events
======

The ``webpy_socketio.events`` module provides a handful of events
that can be subscribed to, very much like connecting receiver
functions to webpy signals. Each of these events are raised
throughout the relevant stages of a Socket.IO request. These events
represent the main approach for implementing your socket handling
logic when using webpy-socketio.

Events are subscribed to by applying each event as a decorator
to your event handler functions::

    from webpy_socketio.events import on_message

    @on_message
    def my_message_handler(request, socket, context, message):
        ...

Where should these event handlers live in your webpy project? They
can go anywhere, so long as they're imported by webpy at startup
time.

Each event handler takes at least three arguments: the current webpy
``request``, the Socket.IO ``socket`` the event occurred for, and a
``context``, which is simply a dictionary that can be used to persist
variables across all events throughout the life-cycle of a single
WebSocket connection.

  * ``on_connect(request, socket, context)`` - occurs once when the
    WebSocket connection is first established.
  * ``on_message(request, socket, context, message)`` - occurs every
    time data is sent to the WebSocket. Takes an extra ``message``
    argument which contains the data sent.
  * ``on_subscribe(request, socket, context, channel)`` - occurs when
    a channel is subscribed to. Takes an extra ``channel`` argument
    which contains the channel subscribed to.
  * ``on_unsubscribe(request, socket, context, channel)`` - occurs
    when a channel is unsubscribed from. Takes an extra ``channel``
    argument which contains the channel unsubscribed from.
  * ``on_error(request, socket, context, exception)`` - occurs when
    an error is raised. Takes an extra ``exception`` argument which
    contains the exception for the error.
  * ``on_disconnect(request, socket, context)`` - occurs once when
    the WebSocket disconnects.
  * ``on_finish(request, socket, context)`` - occurs once when the
    Socket.IO request is finished.

Event handlers can be defined anywhere so long as they end up being imported. 
Consider adding them to their own module that gets imported by your urlconf,
or even adding them to your views module since they're conceptually similar
 to views.

Binding Events to Channels
==========================

All events other than the ``on_connect`` event can also be bound to
particular channels by passing a ``channel`` argument to the event
decorator. The channel argument can contain a regular expression
pattern used to match again multiple channels of similar function.

For example, suppose you implemented a chat site with multiple rooms.
WebSockets would be the basis for users communicating within each
chat room, however you may want to use them elsewhere throughout the
site for different purposes, perhaps for a real-time admin dashboard.
In this case there would be two distinct WebSocket uses, with the chat
rooms each requiring their own individual channels.

Suppose each chat room user subscribes to a channel client-side
using the room's ID::

    var socket = new io.Socket();
    var roomID = 42;
    socket.connect();
    socket.on('connect', function() {
        socket.subscribe('room-' + roomID);
    });

Then server-side the different message handlers are bound to each
type of channel::

    @on_message(channel="dashboard")
    def my_dashboard_handler(request, socket, context, message):
        ...

    @on_message(channel="^room-")
    def my_chat_handler(request, socket, context, message):
        ...

Logging
=======

The following setting can be used to configure logging:

    * ``SOCKETIO_MESSAGE_LOG_FORMAT`` - A format string used for logging
      each message sent via a socket. The string is formatted using
      interpolation with a dictionary. The dictionary contains all the
      keys found in webpy's ``web.ctx.env``, as well as ``TIME``
      and ``MESSAGE`` keys which contain the time of the message and
      the message contents respectively. Set this setting to ``None``
      to disable message logging.

Chat Demo
=========

The "hello world" of WebSocket applications is naturally the chat
room. As such webpy-socketio comes with a demo chat application
that provides examples of the different events, channel and broadcasting
features available. The demo can be found in the ``example``
directory of the ``webpy_socketio`` package.

Working with nginx
====================

	* Recomplie nginx with nginx_tcp_proxy_module.
     $ sudo nginx -V
     
     You may be see below:
     
     $ configure arguments: --prefix=/etc/nginx/ --sbin-path=/usr/sbin/nginx --conf-path=/etc/nginx/nginx.conf --error-log-path=/var/log/nginx/error.log --http-log-path=/var/log/nginx/access.log --pid-path=/var/run/nginx.pid --lock-path=/var/run/nginx.lock --http-client-body-temp-path=/var/cache/nginx/client_temp --http-proxy-temp-path=/var/cache/nginx/proxy_temp --http-fastcgi-temp-path=/var/cache/nginx/fastcgi_temp --http-uwsgi-temp-path=/var/cache/nginx/uwsgi_temp --http-scgi-temp-path=/var/cache/nginx/scgi_temp --user=nginx --group=nginx --with-http_ssl_module --with-http_realip_module --with-http_addition_module --with-http_sub_module --with-http_dav_module --with-http_flv_module --with-http_mp4_module --with-http_gzip_static_module --with-http_random_index_module --with-http_secure_link_module --with-http_stub_status_module --with-mail --with-mail_ssl_module --with-file-aio --with-ipv6

    * Download ngnix source from http://nginx.org/en/download.html
    * Download nginx_tcp_proxy_module from https://github.com/yaoweibin/nginx_tcp_proxy_module
    * Unzip nginx_tcp_proxy_module.zip
	* Do follow
     $ cd nginx-src-dir
     $ patch -p1 < /path/to/nginx_tcp_proxy_module/tcp.patch
     $ ./configure before_configure_arguments_with_nginx_-V --add-module=/path/to/nginx_tcp_proxy_module
     $ make
     $ sudo make install

    * Edit /etc/nginx/nginx.conf

     tcp {
       upstream websocket {
       # This is the local port running on your app
       # server, which is inaccessible from outside
       server 127.0.0.1:8000;
       #check interval=3000 rise=2 fall=5 timeout=1000;
       }
     } 
     http{
	       ...

	* If not exists, add /etc/nginx/proxy_params
     
     proxy_set_header Host $host;
     proxy_set_header X-Real-IP $remote_addr;
     proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

	* Touch /etc/nginx/conf.d/your_app.conf

     upstream socketio_server {
        # For a TCP configuration:
        # Replace 8000 with app servers port
        server 127.0.0.1:8000 fail_timeout=0;

        # For a Unix Socket
        # server unix:/tmp/yourappserver.sock fail_timeout=0;
        }

    server {
        listen 80;
        client_max_body_size 4G;
        #server_name _;
	    server_name your_server_name;
        access_log /var/log/your_app_access.log;
	    error_log /var/log/your_app_error.log;
        keepalive_timeout 5;

        # path for static files
	    location /static {
	        root   /path/to/static/files;
	    }

        location / {
	        include proxy_params;
	        proxy_pass http://socketio_server;
        }
    }
}

reference: http://readthedocs.org/docs/django-socketio/en/latest/#installation
