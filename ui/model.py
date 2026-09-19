#!/usr/bin/python3

import dbus


class MonitorModel:

    BUS_NAME = "org.example.DDCMonitor"
    OBJECT_PATH = "/org/example/DDCMonitor"
    INTERFACE = "org.example.DDCMonitor"

    BRIGHTNESS_VCP = 0x10
    CONTRAST_VCP = 0x12

    def __init__(self):

        self.bus = dbus.SystemBus()

        self.proxy = self.bus.get_object(
            self.BUS_NAME,
            self.OBJECT_PATH
        )

        self.interface = dbus.Interface(
            self.proxy,
            self.INTERFACE
        )

        self.monitors = []

    # -------------------------------------------------
    # Monitor detection
    # -------------------------------------------------

    def get_monitors(self):

        monitors = self.interface.GetMonitors()

        result = []

        for monitor in monitors:

            result.append({
                "id": int(monitor["id"]),
                "manufacturer": str(
                    monitor["manufacturer"]
                ),
                "model": str(
                    monitor["model"]
                )
            })

        self.monitors = result

        return result

    # -------------------------------------------------
    # VCP
    # -------------------------------------------------

    def get_vcp(self, display, code):

        current, maximum = (
            self.interface.GetVCP(
                int(display),
                int(code)
            )
        )

        return {
            "current": int(current),
            "max": int(maximum)
        }

    # -------------------------------------------------
    # Brightness
    # -------------------------------------------------

    def get_brightness(self, display):

        return self.get_vcp(
            display,
            self.BRIGHTNESS_VCP
        )

    def set_brightness(
        self,
        display,
        value
    ):

        self.interface.SetVCP(
            int(display),
            self.BRIGHTNESS_VCP,
            int(value)
        )

    # -------------------------------------------------
    # Contrast
    # -------------------------------------------------

    def get_contrast(self, display):

        return self.get_vcp(
            display,
            self.CONTRAST_VCP
        )

    def set_contrast(
        self,
        display,
        value
    ):

        self.interface.SetVCP(
            int(display),
            self.CONTRAST_VCP,
            int(value)
        )
