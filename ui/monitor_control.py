#!/usr/bin/python3

import gi
gi.require_version("Gtk", "3.0")

from gi.repository import Gtk, GLib
import dbus


BUS_NAME = "org.example.DDCMonitor"
OBJECT_PATH = "/org/example/DDCMonitor"
INTERFACE = "org.example.DDCMonitor"


class MonitorControl(Gtk.Window):

    def __init__(self):

        Gtk.Window.__init__(
            self,
            title="Monitor Control"
        )

        self.set_default_size(600, 500)
        self.set_border_width(20)

        # D-Bus
        self.bus = dbus.SystemBus()

        self.proxy = self.bus.get_object(
            BUS_NAME,
            OBJECT_PATH
        )

        self.interface = dbus.Interface(
            self.proxy,
            INTERFACE
        )

        # State
        self.monitors = []

        # Prevent programmatic slider updates from
        # triggering DDC writes.
        self.updating_ui = False

        # Debounce timers
        self.brightness_timer = None
        self.contrast_timer = None

        # Build UI
        self.build_ui()

        # Detect monitors
        self.load_monitors()

    # -------------------------------------------------
    # UI
    # -------------------------------------------------

    def build_ui(self):

        main = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=15
        )

        self.add(main)

        # Title

        title = Gtk.Label()

        title.set_markup(
            "<big><b>Displays</b></big>"
        )

        title.set_xalign(0)

        main.pack_start(
            title,
            False,
            False,
            0
        )

        # Monitor selection

        self.monitor_combo = Gtk.ComboBoxText()

        self.monitor_combo.connect(
            "changed",
            self.monitor_changed
        )

        main.pack_start(
            self.monitor_combo,
            False,
            False,
            0
        )

        # Monitor information

        self.monitor_label = Gtk.Label()

        self.monitor_label.set_xalign(0)

        main.pack_start(
            self.monitor_label,
            False,
            False,
            0
        )

        # Brightness

        brightness_label = Gtk.Label(
            label="Brightness"
        )

        brightness_label.set_xalign(0)

        main.pack_start(
            brightness_label,
            False,
            False,
            0
        )

        self.brightness = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL,
            0,
            100,
            1
        )

        self.brightness.set_draw_value(True)

        self.brightness.connect(
            "value-changed",
            self.brightness_changed
        )

        main.pack_start(
            self.brightness,
            False,
            False,
            0
        )

        # Contrast

        contrast_label = Gtk.Label(
            label="Contrast"
        )

        contrast_label.set_xalign(0)

        main.pack_start(
            contrast_label,
            False,
            False,
            0
        )

        self.contrast = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL,
            0,
            100,
            1
        )

        self.contrast.set_draw_value(True)

        self.contrast.connect(
            "value-changed",
            self.contrast_changed
        )

        main.pack_start(
            self.contrast,
            False,
            False,
            0
        )

        # Refresh button

        button = Gtk.Button(
            label="Refresh"
        )

        button.connect(
            "clicked",
            self.refresh
        )

        main.pack_start(
            button,
            False,
            False,
            0
        )

    # -------------------------------------------------
    # Monitor detection
    # -------------------------------------------------

    def load_monitors(self):

        try:

            self.monitors = (
                self.interface.GetMonitors()
            )

            self.monitor_combo.remove_all()

            for monitor in self.monitors:

                monitor_id = int(
                    monitor["id"]
                )

                manufacturer = str(
                    monitor["manufacturer"]
                )

                model = str(
                    monitor["model"]
                )

                text = (
                    f"{manufacturer} {model}"
                    f"  (Display {monitor_id})"
                )

                self.monitor_combo.append(
                    str(monitor_id),
                    text
                )

            if self.monitors:

                self.monitor_combo.set_active(0)

            else:

                self.monitor_label.set_text(
                    "No monitors detected"
                )

        except Exception as e:

            self.show_error(
                f"Unable to detect monitors:\n\n{e}"
            )

    # -------------------------------------------------
    # Get selected monitor
    # -------------------------------------------------

    def get_display(self):

        active = (
            self.monitor_combo.get_active()
        )

        if active < 0:
            return None

        if active >= len(self.monitors):
            return None

        return int(
            self.monitors[active]["id"]
        )

    # -------------------------------------------------
    # Cancel pending timers
    # -------------------------------------------------

    def cancel_pending_updates(self):

        if self.brightness_timer is not None:

            GLib.source_remove(
                self.brightness_timer
            )

            self.brightness_timer = None

        if self.contrast_timer is not None:

            GLib.source_remove(
                self.contrast_timer
            )

            self.contrast_timer = None

    # -------------------------------------------------
    # Debounced VCP update
    # -------------------------------------------------

    def schedule_vcp_update(
        self,
        display,
        code,
        value,
        timer_attr
    ):

        old_timer = getattr(
            self,
            timer_attr
        )

        # Cancel previous pending update
        if old_timer is not None:

            GLib.source_remove(
                old_timer
            )

            setattr(
                self,
                timer_attr,
                None
            )

        def apply_value():

            try:

                self.interface.SetVCP(
                    display,
                    code,
                    value
                )

                print(
                    f"VCP 0x{code:02X}: "
                    f"display={display}, "
                    f"value={value}"
                )

            except Exception as e:

                print(
                    f"VCP 0x{code:02X} error: {e}"
                )

            setattr(
                self,
                timer_attr,
                None
            )

            return False

        timer = GLib.timeout_add(
            200,
            apply_value
        )

        setattr(
            self,
            timer_attr,
            timer
        )

    # -------------------------------------------------
    # Monitor changed
    # -------------------------------------------------

    def monitor_changed(self, combo):

        # Do not allow an update intended for the
        # previous monitor to execute.
        self.cancel_pending_updates()

        display = self.get_display()

        if display is None:
            return

        index = combo.get_active()

        if index < 0 or index >= len(self.monitors):
            return

        monitor = self.monitors[index]

        self.monitor_label.set_text(
            f"{monitor['manufacturer']} "
            f"{monitor['model']}"
        )

        self.read_values(display)

    # -------------------------------------------------
    # Read monitor values
    # -------------------------------------------------

    def read_values(self, display):

        self.updating_ui = True

        try:

            # Brightness
            try:

                brightness = (
                    self.interface.GetVCP(
                        display,
                        0x10
                    )
                )

                self.brightness.set_range(
                    0,
                    int(brightness[1])
                )

                self.brightness.set_value(
                    int(brightness[0])
                )

                self.brightness.set_sensitive(
                    True
                )

            except Exception as e:

                print(
                    "Unable to read brightness:",
                    e
                )

                self.brightness.set_sensitive(
                    False
                )

            # Contrast
            try:

                contrast = (
                    self.interface.GetVCP(
                        display,
                        0x12
                    )
                )

                self.contrast.set_range(
                    0,
                    int(contrast[1])
                )

                self.contrast.set_value(
                    int(contrast[0])
                )

                self.contrast.set_sensitive(
                    True
                )

            except Exception as e:

                print(
                    "Unable to read contrast:",
                    e
                )

                self.contrast.set_sensitive(
                    False
                )

        finally:

            self.updating_ui = False

    # -------------------------------------------------
    # Brightness
    # -------------------------------------------------

    def brightness_changed(self, slider):

        if self.updating_ui:
            return

        if not slider.is_sensitive():
            return

        display = self.get_display()

        if display is None:
            return

        value = int(
            slider.get_value()
        )

        self.schedule_vcp_update(
            display,
            0x10,
            value,
            "brightness_timer"
        )

    # -------------------------------------------------
    # Contrast
    # -------------------------------------------------

    def contrast_changed(self, slider):

        if self.updating_ui:
            return

        if not slider.is_sensitive():
            return

        display = self.get_display()

        if display is None:
            return

        value = int(
            slider.get_value()
        )

        self.schedule_vcp_update(
            display,
            0x12,
            value,
            "contrast_timer"
        )

    # -------------------------------------------------
    # Refresh
    # -------------------------------------------------

    def refresh(self, button):

        self.cancel_pending_updates()

        self.load_monitors()

    # -------------------------------------------------
    # Error dialog
    # -------------------------------------------------

    def show_error(self, message):

        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=message
        )

        dialog.run()
        dialog.destroy()


# -----------------------------------------------------
# Main
# -----------------------------------------------------

def main():

    window = MonitorControl()

    window.connect(
        "destroy",
        Gtk.main_quit
    )

    window.show_all()

    Gtk.main()


if __name__ == "__main__":
    main()
