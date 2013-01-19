#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on 17-11-2012

@author: Arkadiusz Dzięgiel
'''

from distutils.core import setup

setup(
	name='PySolar',
	version='1.1',
	description='DBus service for providing lightness and battery levels for Logitech Solar devices',
	author='Arkadiusz Dzięgiel',
	author_email='arkadiusz.dziegiel@glorpen.pl',
	url='http://glorpen.pl',
	packages=['pysolar'],
	scripts=['scripts/pysolar-dbus'],
	#requires=["PythonDaemon"],
	data_files=[
		("/etc/dbus-1/system.d/", ["dbus-policy/pl.glorpen.PySolar.conf"])
	]
)
