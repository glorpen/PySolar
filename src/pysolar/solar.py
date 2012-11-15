import pyudev
import os
import struct
import threading
import time
import logging

logging.basicConfig()

logger = logging.getLogger("solar")


class Report(object):
	def __init__(self, data, device_name):
		self.data = data
		self.device_name = device_name
	
	def has_lightness(self):
		return self.data["fcnt"] == 1
	
	def get_lightness(self):
		return self.data["lightness"] if self.has_lightness() else None
	
	def get_charge(self):
		return self.data["charge"]
	
	def from_button(self):
		return self.data["fcnt"] == 2
	
	def __str__(self):
		return "%s => charge: %d%%, lightness: %s (%s)" % (self.device_name, self.get_charge(), str(self.get_lightness()) if self.has_lightness() else "-", str(self.data))

class Solar(object):
	
	REPORT_LONG_ID = 0x11
	REPORT_SHORT_ID = 0x10
	
	REPORT_SHORT_LEN = 7
	REPORT_LONG_LEN = 20
	
	SOFTWARE_ID = 4
	FEATURE_SOLAR = 9
	
	FUNCTION_STATUS = 0
	FUNCTION_LIGHT = 1
	FUNCTION_CHARGE = 2
	
	def __del__(self):
		self.shutdown()

	def shutdown(self):
		try:
			os.close(self.fd)
		except OSError:
			pass
	
	def __init__(self, hidraw, dj_name, devpath):
		object.__init__(self)
		
		self.devpath = devpath
		self.dj_name = dj_name
		self.fd = os.open(hidraw, os.O_RDWR)
		self.devices = {}

	def send_report(self, device_index):
		if device_index not in self.devices:
			raise Exception("unknown device index")
		os.write(self.fd, struct.pack(">BBBB3s", self.REPORT_SHORT_ID, int(device_index), self.FEATURE_SOLAR, self.SOFTWARE_ID, "\x78\x01\x00"))
	
	def get_report(self):
		report = os.read(self.fd, self.REPORT_LONG_LEN)
		
		if report != "":
			r = self._parse_report(report)
			if r and r["device_index"] in self.devices:
				return Report(r, self.devices[r["device_index"]])

	def handle_one_report(self):
		rep = self.get_report()
		if rep is not None:
			if rep.from_button():
				self.send_report(rep.data["device_index"])
				logger.debug("sending lightness request to %s (%d)" % (self.dj_name, rep.data["device_index"]))
			return rep
	
	def iter_reports(self):
		while True:
			try:
				report = self.handle_one_report()
			except OSError:
				return
			
			if report: yield report

	def _parse_report(self, report):
		rep = self._unpack((('type','B'), ('device_index','B'), ('feature_index','B'), ('fcnt','B')), report[0:4])
		#rep._make(struct.unpack_from("BBBB",report[0:4]))
		rep["sw_id"] = rep["fcnt"] & 15
		rep["fcnt"] = rep["fcnt"]>>4
		
		#if fcnt == 1: with lightness
		#battery status level only with sw_id = 0 aka not used
		
		#fcnt == 2 = button, 1= event, 0 - ?
		if rep["type"] == self.REPORT_LONG_ID and rep["feature_index"] == self.FEATURE_SOLAR and rep["sw_id"] != self.SOFTWARE_ID:
			rep.update(self._unpack((('charge','B'), ('lightness','H'), ('_unk','H'), ('info','11s')), report[4:]))
			#rep["_unk2"] = (rep["_unk2"]>>4, rep["_unk2"]&15, rep["_unk2"])
			return rep

	def _unpack(self, fields, data):
		values = struct.unpack(">"+"".join(f[1] for f in fields), data)
		return dict((fields[i][0], values[i]) for i in range(len(values)))
		

class DjManager():
	
	def __init__(self):
		self.context = pyudev.Context()
		self.djs = {}
	
	def find_hidraw_devices(self, *devices):
		for d in self.context.list_devices(subsystem="hidraw"):
			if d.parent in devices:
				yield d
	
	def find_devices(self):
		djs=list()
		for d in self.context.list_devices(subsystem="hid", DRIVER='logitech-djreceiver'):
			self.add_dj_device(d)
			djs.append(d)
		
		for device in self.context.list_devices(subsystem="hid"):
			if device.parent in djs:
				self.add_unified_device(device)
	
	def add_dj_device(self, device):
		
		logger.debug("adding dj device %s" % repr(device))
		
		devpath = device.get("DEVPATH")
		if devpath in self.djs:
			raise Exception("device already added")
		
		solar_app = None
		for d in self.find_hidraw_devices(device):
			solar_app = Solar(os.path.join(self.context.device_path,d.get("DEVNAME")), device.get("HID_NAME"), devpath)
			break
		self.djs[devpath] = solar_app
		
		threading.Thread(target=self.report_loop, args=(devpath,)).start()
	
	def report_handler(self, dj, num, report):
		print report
	
	def report_loop(self, djpath):
		dj = self.djs[djpath]
		for r in dj.iter_reports():
			self.report_handler(dj, r.data["device_index"], r)
			
	def remove_dj_device(self, device):
		devpath = device.get("DEVPATH")
		logger.debug("removing dj device %s" % repr(device))
		del self.djs[devpath]
	
	def add_unified_device(self, device):
		logger.debug("adding unified device %s" % repr(device))
		
		pos = int(device.get("HID_PHYS").split(':')[-1])
		name = device.get("HID_NAME")
		devices = self.djs[device.parent.get("DEVPATH")].devices
		
		if pos in devices:
			raise Exception("unified device already exists")
		devices[pos] = name
		
	def remove_unified_device(self, device):
		logger.debug("removing unified device %s" % repr(device))
		pos = int(device.get("HID_PHYS").split(':')[-1])
		del self.djs[device.parent.get("DEVPATH")].devices[pos]

	def monitor_dj(self):
		
		monitor = pyudev.Monitor.from_netlink(self.context)
		
		monitor.filter_by(u"hid")
		
		def callback(device):
			if device.action == "add":
				for d in self.context.list_devices(subsystem="hid", DRIVER='logitech-djreceiver'):
					if d.get("DEVPATH") != device.get("DEVPATH"): continue
					self.add_dj_device(d)
				if device.parent.get("DEVPATH") in self.djs:
					self.add_unified_device(device)
			if device.action == "remove":
				if device.get("DEVPATH") in self.djs:
					self.remove_dj_device(device)
				if device.parent.get("DEVPATH") in self.djs:
					self.remove_unified_device(device)
		
		self.dj_observer = pyudev.MonitorObserver(monitor, callback=callback)
		self.dj_observer.start()
		
	
	def shutdown(self):
		self.dj_observer.stop()
		
		for d in self.djs.values():
			d.shutdown()
		
		for thread in threading.enumerate():
			if thread is not threading.currentThread():
				thread.join()
		
		self.djs.clear()

if __name__ == "__main__":
	
	logger.setLevel(logging.DEBUG)
	
	manager = DjManager()
	try:
		manager.find_devices() #initial devices scan
		manager.monitor_dj() #listen to udev
		manager.dj_observer.join()
	finally:
		logger.info("shutting down")
		manager.shutdown()
