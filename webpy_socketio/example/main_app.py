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
from settings import chat_db, my_render, csrf_protected, notfound, internalerror,session_dir
#import socketio libs
from socketio import SocketIOServer
from gevent import monkey 
monkey.patch_all()
from webpy_socketio import *

web.config.debug = True

urls = (
	'/','rooms',
	'/room/(\S+)','room',
	'/sysmsg','system_message',
    )

urls += socketio_urls

app = web.application(urls, globals())

app.notfound = notfound
app.internalerror = internalerror

if web.config.debug:
	if web.config.get('_session') is None:
		session = web.session.Session(app, web.session.DiskStore(session_dir))
		web.config._session = session
	else:
		session = web.config._session
else:	
	session = web.session.Session(app, web.session.DiskStore(session_dir))

#share session with sub-app    
def session_hook():
	web.ctx.session = session
		
app.add_processor(web.loadhook(session_hook))

#page handlers
class room(object):
	
	def GET(myself,slug):
		"""
		Show a room.
		"""
		rooms = chat_db.select("chat_chatroom",dict(slug=slug),where="slug = $slug")
		for room in rooms:
			return my_render.render("room",room=room)
		raise web.notfound()
		
class rooms(object):

	def GET(myself):
		"""
		Homepage - lists all rooms.
		"""
		rooms = chat_db.select('chat_chatroom')
		return my_render.render("rooms",**locals())
		
	@csrf_protected	
	def POST(myself):
		"""
		Handles post from the "Add room" form on the homepage, and
		redirects to the new room.
		"""
		input_data = web.input()
		room_name = input_data.name
		if room_name:
			slug_name = "-".join(room_name.lower().split(" "))
			name_id = chat_db.insert('chat_chatroom', name=room_name,slug=slug_name)
			raise web.seeother("/room/" + slug_name)
		raise web.seeother("/rooms")
	
class system_message(object):
	"""
	Send a system message. If you like, you can add a admin role checking fucntion
	"""
	def GET(myself):
		rooms = chat_db.select("chat_chatroom")
		message = ""
		selected_room = ""
		return my_render.render("system_message",**locals())
		
	@csrf_protected
	def POST(myself):
		input_data = web.input()
		selected_room = input_data["room"]
		data = {"action": "system", "message": input_data["message"]}
		try:
			if selected_room:
				broadcast_channel(data, channel="room-" + selected_room)
			else:
				broadcast(data)
		except NoSocket, e:
			message = e
		else:
			message = "Message sent"
		rooms = chat_db.select("chat_chatroom")
		return my_render.render("system_message",**locals())

SOCKETIO_HOST = ""
SOCKETIO_PORT = 8000
application = app.wsgifunc()

import events

if __name__ == "__main__":
	print 'Listening on http://127.0.0.1:%s and on port 843 (flash policy server)' % SOCKETIO_PORT
	SocketIOServer((SOCKETIO_HOST, SOCKETIO_PORT), application, resource="socket.io").serve_forever()
