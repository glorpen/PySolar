-------
PySolar
-------

Main purpose of this package is to provide end-user with charge data and lightness meter from Logitech Solar Keyboard.

For now, package consists of:

- DBus service
- simple python console client
- gnome-shell extension


Simple console client
---------------------

After installation you can run client with:

::

   python -m pysolar.client


it will output events captured by DBus service

::

   Logitech Unifying Device. Wireless PID:4002 #1: battery level 53%, lightness: -
   Logitech Unifying Device. Wireless PID:4002 #1: battery level 53%, lightness: 51
   Logitech Unifying Device. Wireless PID:4002 #1: battery level 53%, lightness: 52
   Logitech Unifying Device. Wireless PID:4002 #1: battery level 53%, lightness: 52


DBus service
------------

In addition to script for use in */etc/init.d*, there is simple script for starting pysolar service as true daemon.

::

   # pysolar-dbus -h
   usage: pysolar-dbus [-h] [--pid-file PID_FILE] [--background]
   
   Run PySolar service
   
   optional arguments:
     -h, --help            show this help message and exit
     --pid-file PID_FILE, -p PID_FILE
                           Pid file to use
     --background, -b      Run service in background


To simply run from console, without daemon tools:

::

   python -m pysolar.dbus_service


Daemon events:

- ChargeEvent(dj_path, device_num, charge)
- LightnessEvent(dj_path, device_num, charge, lightness)
- DevicesChangedEvent() - happens when logitech device is removed or added to the system

Daemon methods:

- ListDevices() - returns list of found devices as (name[string], dj_path[string], device_num[uint])


You can event start only "core" module, that is one responsible for reading events from USB devices. Useful for debugging, if you ever needed one.

::

   python -m pysolar.solar  


If you get error similar to *dbus.exceptions.DBusException: org.freedesktop.DBus.Error.AccessDenied: Connection ":1.55" is not allowed to own the service "pl.glorpen.PySolar" due to security policies in the configuration file*, you should:

- check if **/etc/dbus-1/system.d/pl.glorpen.PySolar.conf** exists
- restart dbus
- start pysolar service as **root**

gnome-shell extension
---------------------

Named PySolar, connects to DBus service and listen for events.

Lists every found solar logitech device, its charge level and lightness if available.
