import pyudev
import os
import struct
import threading
import time

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
	
	def __init__(self, hidraw, dj_name):
		object.__init__(self)
		
		self.dj_name = dj_name
		self.fd = os.open(hidraw, os.O_RDWR | os.O_NONBLOCK)
		self.devices = {}

	def send_report(self, device_index):
		if device_index not in self.devices:
			raise Exception("unknown device index")
		os.write(self.fd, struct.pack(">BBBB3s", self.REPORT_SHORT_ID, int(device_index), self.FEATURE_SOLAR, self.SOFTWARE_ID, "\x78\x01\x00"))
	
	def get_report(self):
		report = os.read(self.fd, self.REPORT_LONG_LEN)
		
		r = self.parse_report(report)
		if r and r["device_index"] in self.devices:
			return Report(r, self.devices[r["device_index"]])

	def handle_one_report(self):
		try:
			rep = self.get_report()
			if rep is not None:
				if rep.from_button():
					self.send_report(rep.data["device_index"])
					#print "send report", rep.data["device_index"]
				return rep
			time.sleep(0.3)
		except OSError as e:
			return None if e.errno == os.errno.EAGAIN else False

	def parse_report(self, report):
		rep = self.unpack((('type','B'), ('device_index','B'), ('feature_index','B'), ('fcnt','B')), report[0:4])
		#rep._make(struct.unpack_from("BBBB",report[0:4]))
		rep["sw_id"] = rep["fcnt"] & 15
		rep["fcnt"] = rep["fcnt"]>>4
		
		#if fcnt == 1: with lightness
		#battery status level only with sw_id = 0 aka not used
		
		#fcnt == 2 = button, 1= event, 0 - ?
		if rep["type"] == self.REPORT_LONG_ID and rep["feature_index"] == self.FEATURE_SOLAR and rep["sw_id"] != self.SOFTWARE_ID:
			rep.update(self.unpack((('charge','B'), ('lightness','H'), ('_unk','H'), ('info','11s')), report[4:]))
			#rep["_unk2"] = (rep["_unk2"]>>4, rep["_unk2"]&15, rep["_unk2"])
			return rep

	def unpack(self, fields, data):
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
		#print "add device", device
		
		devpath = device.get("DEVPATH")
		if devpath in self.djs:
			raise Exception("device already added")
		
		solar_app = None
		for d in self.find_hidraw_devices(device):
			solar_app = Solar(os.path.join(self.context.device_path,d.get("DEVNAME")), device.get("HID_NAME"))
			break
		self.djs[devpath] = solar_app
		
		threading.Thread(target=self.report_loop, args=(devpath,)).start()
	
	def report_loop(self, djpath):
		while True:
			try:
				dj = self.djs[djpath]
			except KeyError:
				return
			
			r = dj.handle_one_report()
			if r is False: return
			if r: print r
			
	def remove_dj_device(self, device):
		devpath = device.get("DEVPATH")
		#print "removing dj", devpath
		del self.djs[devpath]
	
	def add_unified_device(self, device):
		#print "add unified device", device
		
		pos = int(device.get("HID_PHYS").split(':')[-1])
		name = device.get("HID_NAME")
		devices = self.djs[device.parent.get("DEVPATH")].devices
		
		if pos in devices:
			raise Exception("unified device already exists")
		devices[pos] = name
		
	def remove_unified_device(self, device):
		pos = int(device.get("HID_PHYS").split(':')[-1])
		del self.djs[device.parent.get("DEVPATH")].devices[pos]

	def monitor_dj(self):
		
		monitor = pyudev.Monitor.from_netlink(self.context)
		
		monitor.filter_by(u"hid")
		monitor.start()
		
		for device in iter(monitor.poll, None):
			
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
	
	def shutdown(self):
		for d in self.djs.values():
			d.shutdown()
		
		for thread in threading.enumerate():
			if thread is not threading.currentThread():
				thread.join()
		
		self.djs.clear()

if __name__ == "__main__":
	manager = DjManager()
	try:
		manager.find_devices()
		#print "sleeping"
		manager.monitor_dj()
		#print "shutdown"
	finally:
		manager.shutdown()

"""
Logitech Unifying Device. Wireless PID:4002 => charge: 28%, lightness: - ({'info': 'GOOD\x00\x00\x00\x00\x00\x00\x00', 'sw_id': 0, 'fcnt': 0, 'lightness': 0, 'device_index': 1, '_unk2': (15, 2, 242), '_unk1': 5, 'charge': 28, 'type': 17, 'feature_index': 9})
Logitech Unifying Device. Wireless PID:4002 => charge: 28%, lightness: - ({'info': 'GOOD\x00\x00\x00\x00\x00\x00\x00', 'sw_id': 0, 'fcnt': 0, 'lightness': 0, 'device_index': 1, '_unk2': (15, 1, 241), '_unk1': 5, 'charge': 28, 'type': 17, 'feature_index': 9})
Logitech Unifying Device. Wireless PID:4002 => charge: 27%, lightness: 13 ({'info': 'GOOD\x00\x00\x00\x00\x00\x00\x00', 'sw_id': 0, 'fcnt': 1, 'lightness': 13, 'device_index': 1, '_unk2': (15, 0, 240), '_unk1': 5, 'charge': 27, 'type': 17, 'feature_index': 9})
Logitech Unifying Device. Wireless PID:4002 => charge: 26%, lightness: - ({'info': 'GOOD\x00\x00\x00\x00\x00\x00\x00', 'sw_id': 0, 'fcnt': 0, 'lightness': 0, 'device_index': 1, '_unk2': (14, 15, 239), '_unk1': 5, 'charge': 26, 'type': 17, 'feature_index': 9})
Logitech Unifying Device. Wireless PID:4002 => charge: 26%, lightness: 21 ({'info': 'GOOD\x00\x00\x00\x00\x00\x00\x00', 'sw_id': 0, 'fcnt': 1, 'lightness': 21, 'device_index': 1, '_unk2': (14, 14, 238), '_unk1': 5, 'charge': 26, 'type': 17, 'feature_index': 9})
Logitech Unifying Device. Wireless PID:4002 => charge: 25%, lightness: 21 ({'info': 'GOOD\x00\x00\x00\x00\x00\x00\x00', 'sw_id': 0, 'fcnt': 1, 'lightness': 21, 'device_index': 1, '_unk2': (14, 13, 237), '_unk1': 5, 'charge': 25, 'type': 17, 'feature_index': 9})
Logitech Unifying Device. Wireless PID:4002 => charge: 24%, lightness: - ({'info': 'GOOD\x00\x00\x00\x00\x00\x00\x00', 'sw_id': 0, 'fcnt': 0, 'lightness': 0, 'device_index': 1, '_unk2': (14, 12, 236), '_unk1': 5, 'charge': 24, 'type': 17, 'feature_index': 9})
Logitech Unifying Device. Wireless PID:4002 => charge: 24%, lightness: - ({'info': 'GOOD\x00\x00\x00\x00\x00\x00\x00', 'sw_id': 0, 'fcnt': 0, 'lightness': 0, 'device_index': 1, '_unk2': (14, 11, 235), '_unk1': 5, 'charge': 24, 'type': 17, 'feature_index': 9})
Logitech Unifying Device. Wireless PID:4002 => charge: 22%, lightness: - ({'info': 'GOOD\x00\x00\x00\x00\x00\x00\x00', 'sw_id': 0, 'fcnt': 0, 'lightness': 0, 'device_index': 1, '_unk2': (14, 8, 232), '_unk1': 5, 'charge': 22, 'type': 17, 'feature_index': 9})
Logitech Unifying Device. Wireless PID:4002 => charge: 21%, lightness: - ({'info': 'GOOD\x00\x00\x00\x00\x00\x00\x00', 'sw_id': 0, 'fcnt': 0, 'lightness': 0, 'device_index': 1, '_unk2': (14, 7, 231), '_unk1': 5, 'charge': 21, 'type': 17, 'feature_index': 9})
Logitech Unifying Device. Wireless PID:4002 => charge: 20%, lightness: - ({'info': 'GOOD\x00\x00\x00\x00\x00\x00\x00', 'sw_id': 0, 'fcnt': 0, 'lightness': 0, 'device_index': 1, '_unk2': (14, 5, 229), '_unk1': 5, 'charge': 20, 'type': 17, 'feature_index': 9})
Logitech Unifying Device. Wireless PID:4002 => charge: 17%, lightness: - ({'info': 'GOOD\x00\x00\x00\x00\x00\x00\x00', 'sw_id': 0, 'fcnt': 0, 'lightness': 0, 'device_index': 1, '_unk2': (14, 1, 225), '_unk1': 5, 'charge': 17, 'type': 17, 'feature_index': 9})
Logitech Unifying Device. Wireless PID:4002 => charge: 75%, lightness: 8 ({'info': 'GOOD\x00\x00\x00\x00\x00\x00\x00', 'sw_id': 0, 'fcnt': 1, 'lightness': 8, 'device_index': 1, '_unk2': (3, 9, 57), '_unk1': 6, 'charge': 75, 'type': 17, 'feature_index': 9})
"""