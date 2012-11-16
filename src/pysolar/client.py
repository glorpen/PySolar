# -*- coding: utf-8 -*-
'''
Created on 07-10-2012

@author: Arkadiusz Dzięgiel
'''

import dbus
from pprint import pprint
bus = dbus.SystemBus()
remote_object = bus.get_object('pl.glorpen.PySolar', '/pl/glorpen/PySolar')
#hello = helloservice.get_dbus_method('ListDevices', 'pl.glorpen.PySolar')
#print hello()

#remote_object = bus.get_object("org.freedesktop.DBus", "/org/freedesktop/DBus" )
iface = dbus.Interface(remote_object, 'pl.glorpen.PySolar')
for name, device, num in iface.ListDevices():
	print name, device, num
