# -*- coding: utf-8 -*-
'''
Created on 15-11-2012

@author: Arkadiusz Dzięgiel
'''
import dbus.service.Object
import dbus.service.signal
from pysolar.solar import DjManager, logger
import threading
import logging

class SolarDBus(dbus.service.Object):
	def __init__(self, object_path):
		dbus.service.Object.__init__(self, dbus.SystemBus(), "pl.glorpen.PySolar")
		
		self.manager = DjManager()
		self.manager.report_handler = self.report_handler
		
		self.manager.find_devices() #initial devices scan
		
		self.monitor_thread = threading.Thread(target=self.manager.monitor_dj)
		self.monitor_thread.start()
		#self.manager.monitor_dj() #listen to udev
		
	def stop(self):
		self.manager.shutdown()
		self.monitor_thread.join()

	@dbus.service.method(dbus_interface='pl.glorpen.PySolar', in_signature='', out_signature='a(ssu)')
	def ListDevices(self):
		for dj_path, solar in self.manager.djs.items():
			for num, name in solar.devices.items():
				yield name, dj_path, num

	@dbus.service.signal(dbus_interface='pl.glorpen.PySolar', signature='suu')
	def ChargeEvent(self, dj_path, device_num, charge):
		logger.debug("charge event")
	
	@dbus.service.signal(dbus_interface='pl.glorpen.PySolar', signature='suuu')
	def LightnessEvent(self, dj_path, device_num, charge, lightness):
		logger.debug("lightness event")
	
	def report_handler(self, dj, num, report):
		if report.has_lightness():
			self.LightnessEvent(dj.devpath, num, report.get_charge(), report.get_lightness())
		else:
			self.ChargeEvent(dj.devpath, num, report.get_charge())
	
if __name__ == "__main__":
	
	from dbus.mainloop.glib import DBusGMainLoop
	DBusGMainLoop(set_as_default=True)
	
	logger.setLevel(logging.DEBUG)
	
	s = SolarDBus()
	
	#s.stop()