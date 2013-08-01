# -*- coding: utf-8 -*-

import gtk
from gtk import gdk
import pkg_resources
from pysolar.client import SolarClient
from PIL import Image

import StringIO

class GtkSystrayClient(SolarClient):
    def __init__(self):
        super(GtkSystrayClient, self).__init__()
        
        self.cache = {}
        
        discharged_icon = pkg_resources.resource_filename(__name__, "resources/battery_discharging.png")
        charged_icon = pkg_resources.resource_filename(__name__, "resources/battery_charged.png")
        
        self.charged_icon = Image.open(charged_icon)
        self.discharged_icon = Image.open(discharged_icon)
        
        pixbuf = gdk.pixbuf_new_from_file(discharged_icon)
        self.statusicon = gtk.status_icon_new_from_pixbuf(pixbuf)
        self.statusicon.connect("query-tooltip", self.tooltip)
        self.statusicon.set_has_tooltip(True)
    
    def tooltip(self, item, x, y, keyboard_mode, tooltip):
        labels = ["Name","Charge","Lightness"]
        table = gtk.Table(3, len(self.cache)+1)
        
        for pos,text in enumerate(labels):
            label = gtk.Label()
            label.set_text(text)
            table.attach(label, 0+pos, 1+pos, 0, 1, xpadding=3, ypadding=3)
        
        for row, v in enumerate(self.cache.values()):
            sorted_l = (v["name"], "%d%%" % v["charge"], ("%d lux" % v["lightness"]) if v["lightness"] else "-")
            for pos, i in enumerate(sorted_l):
                label = gtk.Label()
                label.set_text(i)
                table.attach(label, 0+pos, 1+pos, row+1, row+2, xpadding=3, ypadding=3)
        
        tooltip.set_custom(table)
        table.show_all()
        return True
        
    def image_to_pixbuf(self, image):
        fd = StringIO.StringIO()
        image.save(fd, "png")
        contents = fd.getvalue()
        fd.close()
        loader = gtk.gdk.PixbufLoader("png")
        loader.write(contents, len(contents))
        pixbuf = loader.get_pixbuf()
        loader.close()
        return pixbuf

    def update_status(self):
        w,h = self.charged_icon.size
        top_padding = 9
        bottom_padding = 7
        
        if self.cache:
            charge = self.cache.values()[0]["charge"]
            split = charge/100.0 if charge else 0
        else:
            split = 0
        
        split_h = int((h-top_padding-bottom_padding)*(1.0-split))+top_padding
        
        up = self.discharged_icon.crop([0,0,w,split_h])
        down = self.charged_icon.crop([0,split_h,w,h])
        
        icon = Image.new("RGBA", (w,h))
        icon.paste(up, (0,0))
        icon.paste(down, (0,split_h))
        
        self.statusicon.set_from_pixbuf(self.image_to_pixbuf(icon))
        
    def on_load_devices(self, devices):
        self.cache = {}
        for device in devices:
            self.cache[device.id] = {"name":device.name, "charge":None, "lightness":None}
        self.update_status()
        
    def on_charge_event(self, device, charge, lightness):
        self.cache[device.id]["charge"] = charge
        self.cache[device.id]["lightness"] = lightness
        
        self.update_status()
    
    def on_initial_charge(self, device, charge):
        self.cache[device.id]["charge"] = charge
        
        self.update_status()
    

if __name__ == '__main__':
    try:
        GtkSystrayClient().start()
    except KeyboardInterrupt:
        pass
