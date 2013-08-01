# -*- coding: utf-8 -*-
'''
Created on 07-10-2012

@author: Arkadiusz Dzięgiel
'''

import dbus
from dbus.mainloop.glib import DBusGMainLoop
import gobject

class Device(object):
    def __init__(self, name, device, num):
        
        self.name = name
        self.device = device
        self.num = num
        
        super(Device, self).__init__()
    
    def __eq__(self, other):
        return self.name == other.name and self.device == other.device and self.num == other.num
    
    def __unicode__(self):
        return '<Device: %s #%d>' % (self.name, self.num)
    def __repr__(self):
        return self.__unicode__()

class SolarClient(object):
    def __init__(self):
        
        DBusGMainLoop(set_as_default=True)
        
        self.loop = gobject.MainLoop()
        
        bus = dbus.SystemBus()
        remote_object = bus.get_object('pl.glorpen.PySolar', '/pl/glorpen/PySolar')
        self._solar = dbus.Interface(remote_object, 'pl.glorpen.PySolar')
        
        super(SolarClient, self).__init__()
        
        self.load_devices()
        
        self._solar.connect_to_signal('DevicesChangedEvent', self.load_devices)
        self._solar.connect_to_signal('ChargeEvent', self.handle_charge_event)
        self._solar.connect_to_signal('LightnessEvent', self.handle_charge_event)
    
    def handle_charge_event(self, path, num, charge, lightness=None):
        dev = self.get_device(path, num)
        self.on_charge_event(dev, charge, lightness)
    
    def load_devices(self):
        self._devices = {}
        
        for name, device, num in self._solar.ListDevices():
            key = (str(device), int(num))
            self._devices[key] = Device(str(name), *key)
        
        self.on_load_devices()
        
        return self._devices
    
    def get_device(self, devpath, num):
        return self._devices[(devpath, num)]
    
    def list_devices(self):
        return self._devices.values()
    
    def start(self):
        self.loop.run()
    def stop(self):
        self.loop.quit()
        
    def on_charge_event(self, device, charge, lightness):
        print device, charge, lightness
    def on_load_devices(self):
        print "reloading devices"
    
if __name__ == '__main__':
    
    s = SolarClient()
    
    #devs = list(s.list_devices())
    #print devs
    
    def handle_charge_event(device, charge, lightness):
        print "%s #%d: battery level %d%%, lightness: %s" % (device.name, device.num, charge, '-' if lightness is None else str(lightness))
    
    s.on_charge_event = handle_charge_event
    
    s.start()
