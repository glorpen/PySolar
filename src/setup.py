#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on 17-11-2012

@author: Arkadiusz Dzięgiel
'''

from distutils.core import setup

setup(
	name='PySolar',
	version='1.0',
	description='DBus service for providing lightness and battery levels for Logitech Solar devices',
	author='Arkadiusz Dzięgiel',
	author_email='arkadiusz.dziegiel@glorpen.pl',
	url='http://www.python.org/sigs/distutils-sig/',
	packages=['pysolar'],
	data_files=[
		("/etc/dbus-1/system.d/", ["dbus-policy/pl.glorpen.PySolar.conf"])
	]
)