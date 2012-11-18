#!/sbin/runscript
# Distributed under the terms of the GNU General Public License v2

PIDFILE=/var/run/pysolar.pid

depend() {
	need localmount
	use logger dbus udev
	after dbus
}

start() {
	ebegin "Starting PySolar"
	start-stop-daemon --start --pidfile ${PIDFILE} --exec /usr/bin/pysolar-dbus -- --background --pid_file ${PIDFILE}
	eend $?
}

stop() {
	ebegin "Stopping PySolar"
	start-stop-daemon --stop --pidfile ${PIDFILE}
	eend $?
}
