#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       events.py
#       
#       Copyright 2012 Di SONG <songdi19@gmail.com>
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

from webpy_socketio.events import *
from settings import chat_db
import base64

@on_message(channel="^room-")
def message(request, socket, context, message):
	"""
    Event handler for a room receiving a message. First validates a
    joining user's name and sends them the list of users.
	"""
	room_id = message["room"]
	room = chat_db.where("chat_chatroom", id = room_id)

	if message["action"] == "start":
		raw_user_name = message["name"]
		user_name =  base64.b64decode(raw_user_name).decode("utf_8")
		user = chat_db.where("chat_chatuser",name=user_name)
		if user:
			socket.send({"action": "in-use"})
		else:

			users = [base64.b64encode(u.name.encode("utf_8")) for u in chat_db.select("chat_chatuser",dict(room_id=room_id),where="room_id=$room_id")]			
			socket.send({"action": "started", "users": users})
			
			user_session = socket.session.session_id
			user_id = chat_db.insert("chat_chatuser",name=user_name,room_id=room_id,session=user_session)
			context["user"] = {"id":user_id,"name":raw_user_name,"room_id":room_id,"session":user_session}
			
			joined = {"action": "join", "name": context["user"]["name"], "id": context["user"]["id"]}
			socket.send_and_broadcast_channel(joined)
	else:
		try:
			user = context["user"]
		except KeyError:
			return
		if message["action"] == "message":		
			message["name"] = user["name"]
			socket.send_and_broadcast_channel(message)

@on_finish(channel="^room-")
def finish(request, socket, context):
	"""
    Event handler for a socket session ending in a room. Broadcast
    the user leaving and delete them from the DB.
	"""
	try:
		user = context["user"]
	except KeyError:
		return
	chat_db.delete("chat_chatuser",where = "id = $user_id",vars={"user_id":user["id"]})
	left = {"action": "leave", "name": user["name"], "id": user["id"]}
	socket.broadcast_channel(left)
	
