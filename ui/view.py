#!/usr/bin/python3

import gi

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk


class MonitorView(Gtk.Window):

    def __init__(self):

        Gtk.Window.__init__(
            self,
            title="Monitor Control"
        )

        self.set_default_size(
            600,
            500
        )

        self.set_border_width(20)

        self.build_ui()

    # -------------------------------------------------
    # Build UI
    # -------------------------------------------------

    def build_ui(self):

        main = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=15
        )

        self.add(main)

        # -------------------------------------------------
        # Title
        # -------------------------------------------------

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

        # -------------------------------------------------
        # Monitor selector
        # -------------------------------------------------

        self.monitor_combo = (
            Gtk.ComboBoxText()
        )

        main.pack_start(
            self.monitor_combo,
            False,
            False,
            0
        )

        # -------------------------------------------------
        # Monitor information
        # -------------------------------------------------

        self.monitor_label = Gtk.Label()

        self.monitor_label.set_xalign(0)

        main.pack_start(
            self.monitor_label,
            False,
            False,
            0
        )

        # -------------------------------------------------
        # Brightness
        # -------------------------------------------------

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

        self.brightness = (
            Gtk.Scale.new_with_range(
                Gtk.Orientation.HORIZONTAL,
                0,
                100,
                1
            )
        )

        self.brightness.set_draw_value(True)

        main.pack_start(
            self.brightness,
            False,
            False,
            0
        )

        # -------------------------------------------------
        # Contrast
        # -------------------------------------------------

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

        self.contrast = (
            Gtk.Scale.new_with_range(
                Gtk.Orientation.HORIZONTAL,
                0,
                100,
                1
            )
        )

        self.contrast.set_draw_value(True)

        main.pack_start(
            self.contrast,
            False,
            False,
            0
        )

        # -------------------------------------------------
        # Status
        # -------------------------------------------------

        self.status_label = Gtk.Label()

        self.status_label.set_xalign(0)

        main.pack_start(
            self.status_label,
            False,
            False,
            0
        )

        # -------------------------------------------------
        # Refresh
        # -------------------------------------------------

        self.refresh_button = Gtk.Button(
            label="Refresh"
        )

        main.pack_start(
            self.refresh_button,
            False,
            False,
            0
        )

    # -------------------------------------------------
    # Monitor list
    # -------------------------------------------------

    def set_monitors(self, monitors):

        self.monitor_combo.remove_all()

        for monitor in monitors:

            text = (
                f"{monitor['manufacturer']} "
                f"{monitor['model']} "
                f"(Display {monitor['id']})"
            )

            self.monitor_combo.append(
                str(monitor["id"]),
                text
            )

        if monitors:

            self.monitor_combo.set_active(0)

        else:

            self.monitor_label.set_text(
                "No monitors detected"
            )

    # -------------------------------------------------
    # Selected monitor
    # -------------------------------------------------

    def get_selected_monitor_index(self):

        return self.monitor_combo.get_active()

    # -------------------------------------------------
    # Monitor information
    # -------------------------------------------------

    def set_monitor_info(self, monitor):

        if monitor is None:

            self.monitor_label.set_text(
                "No monitor selected"
            )

            return

        self.monitor_label.set_text(
            f"{monitor['manufacturer']} "
            f"{monitor['model']}"
        )

    # -------------------------------------------------
    # Brightness
    # -------------------------------------------------

    def set_brightness_range(self, maximum):

        self.brightness.set_range(
            0,
            maximum
        )

    def set_brightness(self, value):

        self.brightness.set_value(
            value
        )

    def set_brightness_sensitive(self, enabled):

        self.brightness.set_sensitive(
            enabled
        )

    # -------------------------------------------------
    # Contrast
    # -------------------------------------------------

    def set_contrast_range(self, maximum):

        self.contrast.set_range(
            0,
            maximum
        )

    def set_contrast(self, value):

        self.contrast.set_value(
            value
        )

    def set_contrast_sensitive(self, enabled):

        self.contrast.set_sensitive(
            enabled
        )

    # -------------------------------------------------
    # Status
    # -------------------------------------------------

    def set_status(self, text):

        self.status_label.set_text(
            text
        )

    # -------------------------------------------------
    # Error
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
