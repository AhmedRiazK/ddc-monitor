#!/usr/bin/python3

import dbus
import dbus.service
import dbus.mainloop.glib

from gi.repository import GLib

from ddcutil import DDCUtil, DDCUtilError


BUS_NAME = "org.example.DDCMonitor"
OBJECT_PATH = "/org/example/DDCMonitor"


class DDCMonitorService(dbus.service.Object):

    def __init__(self, bus):

        bus_name = dbus.service.BusName(
            BUS_NAME,
            bus=bus
        )

        super().__init__(
            bus_name,
            OBJECT_PATH
        )

        self.ddc = DDCUtil()

    @dbus.service.method(
        "org.example.DDCMonitor",
        in_signature="",
        out_signature="aa{sv}"
    )
    def GetMonitors(self):

        monitors = self.ddc.detect()

        result = []

        for monitor in monitors:

            result.append({
                "id": dbus.Int32(monitor["id"]),
                "model": dbus.String(monitor["model"]),
                "manufacturer": dbus.String(
                    monitor["manufacturer"]
                )
            })

        return result

    @dbus.service.method(
        "org.example.DDCMonitor",
        in_signature="ii",
        out_signature="ii"
    )
    def GetVCP(self, display, code):

        try:

            result = self.ddc.get_vcp(
                display,
                hex(code)
            )

            return (
                dbus.Int32(result["current"]),
                dbus.Int32(result["max"])
            )

        except DDCUtilError as e:

            raise dbus.DBusException(str(e))

    @dbus.service.method(
        "org.example.DDCMonitor",
        in_signature="iii",
        out_signature=""
    )
    def SetVCP(self, display, code, value):

        try:

            self.ddc.set_vcp(
                display,
                hex(code),
                value
            )

        except DDCUtilError as e:

            raise dbus.DBusException(str(e))


def main():

    dbus.mainloop.glib.DBusGMainLoop(
        set_as_default=True
    )

    bus = dbus.SystemBus()

    DDCMonitorService(bus)

    loop = GLib.MainLoop()

    loop.run()


if __name__ == "__main__":
    main()
