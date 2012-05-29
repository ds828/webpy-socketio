#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       untitled.py
#       
#       Copyright 2012 Di SONG <di@di-debian>
#       
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#       
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#       
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.

import web
from webpy_socketio import events
from webpy_socketio.channels import SocketIOChannelProxy
from webpy_socketio.clients import client_start, client_end
from webpy_socketio.utils import format_log

socketio_urls = ('/socket\.io/.*', 'socketio',)

class socketio(object):
	
	def GET(self):
		"""
	    Socket.IO handler - maintains the lifecycle of a Socket.IO
	    request, sending the each of the events. Also handles
	    adding/removing request/socket pairs to the CLIENTS dict
	    which is used for sending on_finish events when the server
	    stops.
	    """
		context = {}
		socket = SocketIOChannelProxy(web.ctx.env["socketio"])
		request = web.ctx.env
		client_start(request, socket, context)
		try:
			if socket.on_connect():
				events.on_connect.send(request, socket, context)
				
			while True:
				messages = socket.recv()
				if not messages and not socket.connected():
					events.on_disconnect.send(request, socket, context)
					break
				messages = iter(messages)
				for message in messages:
					if message == "__subscribe__":
						message = messages.next()
						message_type = "subscribe"
						socket.subscribe(message)
						events.on_subscribe.send(request, socket, context, message)
					elif message == "__unsubscribe__":
						message = messages.next()
						message_type = "unsubscribe"
						socket.unsubscribe(message)
						events.on_unsubscribe.send(request, socket, context, message)
					else:
	                    # Socket.IO sends arrays as individual messages, so
	                    # they're put into an object in socketio_scripts.html
	                    # and given the __array__ key so that they can be
	                    # handled consistently in the on_message event.
						message_type = "message"
						if message == "__array__":
							message = messages.next()
						events.on_message.send(request, socket, context, message)
					log_message = format_log(request, message_type, message)
					if log_message:
						socket.handler.server.log.write(log_message)
		except Exception, exception:
			from traceback import print_exc
			print_exc()
			events.on_error.send(request, socket, context, exception)
		client_end(request, socket, context)
		return ""
