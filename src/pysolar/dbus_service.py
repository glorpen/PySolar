# -*- coding: utf-8 -*-
'''
Created on 15-11-2012

@author: Arkadiusz Dzięgiel
'''
import dbus.service
from dbus.service import Object, signal
from pysolar.solar import DjManager, logger
import threading
import logging
from dbus.mainloop.glib import DBusGMainLoop
import gobject, signal

class SolarDBus(dbus.service.Object):
	def __init__(self):
		
		self.manager = DjManager()
		self.manager.report_handler = self.report_handler
		self.manager.devices_changed_handler = self.DevicesChangedEvent
		
		DBusGMainLoop(set_as_default=True)
		self.mainloop = gobject.MainLoop()
		
		bus = dbus.SystemBus()
		self.name = dbus.service.BusName("pl.glorpen.PySolar", bus)
		
		dbus.service.Object.__init__(self, bus, "/pl/glorpen/PySolar")
		
		signal.signal(signal.SIGINT, self.stop)
		signal.signal(signal.SIGTERM, self.stop)
		
		logger.debug("dbus service started")

		
	def start(self):
		self.manager.find_devices() #initial devices scan
		self.manager_thread = threading.Thread(target=self.manager.monitor)
		self.manager_thread.start()
		
		self.mainloop.run()
	
	def stop(self):
		self.manager.shutdown()
		self.manager_thread.join()
		
		self.mainloop.quit()

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
	
	@dbus.service.signal(dbus_interface='pl.glorpen.PySolar', signature='')
	def DevicesChangedEvent(self):
		pass
	
	def report_handler(self, dj, num, report):
		if report.has_lightness():
			self.LightnessEvent(dj.devpath, num, report.get_charge(), report.get_lightness())
		else:
			self.ChargeEvent(dj.devpath, num, report.get_charge())
	
if __name__ == "__main__":
	logger.setLevel(logging.DEBUG)
	gobject.threads_init()
	
	service = SolarDBus()
	try:
		service.start()
	except KeyboardInterrupt:
		pass
	except Exception as e:
		logger.error("error: %s" % e)
	finally:
		service.stop()
