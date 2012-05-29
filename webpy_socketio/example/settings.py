#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       untitled.py
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

import web
import os
from web.contrib.template import render_mako

##################################################
#
#
# SETUP DATABASE
#
#
##################################################

curdir = os.path.abspath(os.path.dirname(__file__))

DATABASE_ARGS = {
	"dbn": "sqlite", 
	"db": os.path.join(curdir,"chat.db"),
	"check_same_thread":False,
	#avoid dead lock
	"isolation_level":"IMMEDIATE",
	# DBUtils 
	"mincached" : 1, 
	"maxcached": 4, 
	"maxshared": 4, 
	"maxconnections": 4, 
	"blocking": True, 
	"setsession": "",
}

chat_db = web.database(**DATABASE_ARGS)

##################################################
#
#
# SETUP MAKO TEMPLATE
#
# input_encoding and output_encoding is important for unicode
# template file. Reference:
# http://www.makotemplates.org/docs/documentation.html#unicode
#
##################################################

render = render_mako(
        directories=['templates'],
        input_encoding='utf-8',
        output_encoding='utf-8',
        )
        
#decoration for using session in the template
def add_session(f):
	"""
	decoration for using session in the template
	"""
	def decorated(*args,**kwargs):
		return f(*args,session=web.ctx.session,**kwargs)
	return decorated
	
#wrap function for render template	
class render_decorator:
	"""
	wrap function for render template
	"""
	def __init__(self, render):
		self._render = render
	@add_session
	def render(self, template,*args,**kwargs):
		return getattr(self._render,template)(*args,**kwargs)
        
my_render = render_decorator(render)

##################################################
#
#
# SETUP CSRF Function
#
#
##################################################

def csrf_token():
	
	if not web.ctx.session.has_key('csrf_token'):
		from uuid import uuid4
		web.ctx.session.csrf_token=uuid4().hex
	return web.ctx.session.csrf_token

def csrf_protected(f):
	"""
	decoration for using csrf protected function
	"""
	def decorated(*args,**kwargs):
		inp = web.input()
		if not (inp.has_key('csrf_token') and inp.csrf_token==web.ctx.session.pop('csrf_token',None)):
			raise web.HTTPError(
				"400 Bad request",
				{'content-type':'text/html'},
				"""Cross-site request forgery (CSRF) attempt (or stale browser form).<a href="">Back to the form</a>.""",
				)
		return f(*args,**kwargs)
	return decorated

##################################################
#
#
# ERROR PAGE
#
#
##################################################

def notfound():
	return web.notfound("Sorry, the chat room you were looking for was not found.")

def internalerror():
	return web.internalerror("Bad, bad server. No donut for you.")	
