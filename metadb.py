#!/bin/env python
#-*- coding: utf-8 -*-

import sqlite3
import os
import re

class metadb(object):
	def __init__(self,sounddb="sound.db",picdb="pic.db"):
		self.__sounddbname = sounddb
		self.__picdbname = picdb 
		self.__soundcon = None
		self.__piccon = None
		self.__open()
	
	def __del__(self):
		self.close()

	def __open(self):
		sql = '''
			create table if not exists "sound" (
				"word" VARCHAR(64) PRIMARY KEY,
				"data" BLOB
			)
		'''
		
		self.__soundcon = sqlite3.connect(self.__sounddbname)
		self.__soundcon.executescript(sql);
		self.__soundcon.commit()
		
		sql = '''
			create table if not exists "pic" (
				"word" VARCHAR(64) PRIMARY KEY,
				"data" BLOB
			)
		'''
		
		self.__piccon = sqlite3.connect(self.__picdbname)
		self.__piccon.executescript(sql);
		self.__piccon.commit()
		
	def close(self):
		if self.__soundcon :
			self.__soundcon.close()
			self.__soundcon = None
		if self.__piccon:
			self.__piccon.close()
			self.__piccon.close()
		
	def query_pic(self,key):
		c = self.__piccon.cursor()
		c.execute("select data from pic where word = ?",(key,))
		data = c.fetchone()
		return data
		
	def update_pic(self,key,pic):
		c = self.__piccon.cursor()
		c.execute("insert or replace into pic(word,data) values(?,?); ",(key,pic))
		self.__piccon.commit()
		
	def query_sound(self,key):
		c = self.__soundcon.cursor()
		c.execute("select data from sound where word = ?",(key,))
		data = c.fetchone()
		return data
		
	def update_sound(self,key,sound):
		c = self.__soundcon.cursor()
		c.execute("insert or replace into sound(word,data) values(?,?); ",(key,sound))
		self.__soundcon.commit()		
		
	def get(self,key):
		pic = self.query_pic(key)
		sound = self.query_sound(key)
		return (pic,sound)
		
	def __getitem__ (self,key):
		return self.get(key)
