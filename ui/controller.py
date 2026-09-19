#!/usr/bin/python3

from concurrent.futures import ThreadPoolExecutor
from threading import Lock

from gi.repository import GLib


class MonitorController:

    DEBOUNCE_MS = 200

    def __init__(self, model, view):

        self.model = model
        self.view = view

        self.monitors = []
        self.selected_display = None

        self.updating_ui = False

        # -------------------------------------------------
        # Debounce timers
        # -------------------------------------------------

        self.brightness_timer = None
        self.contrast_timer = None

        # -------------------------------------------------
        # Worker pool
        # -------------------------------------------------

        self.executor = ThreadPoolExecutor(
            max_workers=2,
            thread_name_prefix="ddc-worker"
        )

        # -------------------------------------------------
        # Operation queues
        #
        # Each setting has:
        #
        #   active  -> operation currently running
        #   pending -> newest requested value
        #
        # This gives us "latest value wins".
        # -------------------------------------------------

        self.operation_lock = Lock()

        self.brightness_operation = {
            "active": False,
            "pending": None
        }

        self.contrast_operation = {
            "active": False,
            "pending": None
        }

        self.connect_signals()

    # =====================================================
    # GTK SIGNALS
    # =====================================================

    def connect_signals(self):

        self.view.monitor_combo.connect(
            "changed",
            self.on_monitor_changed
        )

        self.view.brightness.connect(
            "value-changed",
            self.on_brightness_changed
        )

        self.view.contrast.connect(
            "value-changed",
            self.on_contrast_changed
        )

        self.view.refresh_button.connect(
            "clicked",
            self.on_refresh
        )

        self.view.connect(
            "destroy",
            self.on_destroy
        )

    # =====================================================
    # START
    # =====================================================

    def start(self):

        self.load_monitors()

    # =====================================================
    # GENERIC WORKER SUBMISSION
    # =====================================================

    def submit(self, function, callback, *args):

        future = self.executor.submit(
            function,
            *args
        )

        def finished(future):

            try:

                result = future.result()

                GLib.idle_add(
                    callback,
                    result,
                    None
                )

            except Exception as e:

                GLib.idle_add(
                    callback,
                    None,
                    e
                )

        future.add_done_callback(
            finished
        )

    # =====================================================
    # MONITOR DETECTION
    # =====================================================

    def load_monitors(self):

        self.view.set_status(
            "Detecting monitors..."
        )

        self.submit(
            self.model.get_monitors,
            self.on_monitors_loaded
        )

    def on_monitors_loaded(
        self,
        monitors,
        error
    ):

        if error is not None:

            self.view.set_status(
                "Monitor detection failed"
            )

            self.view.show_error(
                "Unable to detect monitors:\n\n"
                f"{error}"
            )

            return False

        self.monitors = monitors

        self.view.set_monitors(
            monitors
        )

        if monitors:

            self.view.set_status(
                f"{len(monitors)} monitor(s) detected"
            )

        else:

            self.view.set_status(
                "No monitors detected"
            )

        return False

    # =====================================================
    # MONITOR SELECTION
    # =====================================================

    def on_monitor_changed(self, combo):

        # Cancel anything waiting to be submitted.
        self.cancel_pending_updates()

        index = combo.get_active()

        if index < 0:
            return

        if index >= len(self.monitors):
            return

        monitor = self.monitors[index]

        self.selected_display = monitor["id"]

        self.view.set_monitor_info(
            monitor
        )

        self.load_vcp_values(
            self.selected_display
        )

    # =====================================================
    # READ MONITOR VALUES
    # =====================================================

    def load_vcp_values(self, display):

        self.updating_ui = True

        self.view.set_status(
            "Reading monitor settings..."
        )

        self.submit(
            self.read_monitor_values,
            self.on_vcp_values_loaded,
            display
        )

    def read_monitor_values(self, display):

        brightness = (
            self.model.get_brightness(
                display
            )
        )

        contrast = (
            self.model.get_contrast(
                display
            )
        )

        return {
            "display": display,
            "brightness": brightness,
            "contrast": contrast
        }

    def on_vcp_values_loaded(
        self,
        values,
        error
    ):

        if error is not None:

            self.updating_ui = False

            self.view.set_brightness_sensitive(
                False
            )

            self.view.set_contrast_sensitive(
                False
            )

            self.view.set_status(
                "Unable to read monitor settings"
            )

            print(
                "VCP read error:",
                error
            )

            return False

        # -------------------------------------------------
        # Important:
        #
        # Make sure the values received from the worker
        # still belong to the currently selected monitor.
        # -------------------------------------------------

        if (
            self.selected_display
            != values["display"]
        ):

            self.updating_ui = False

            return False

        self.updating_ui = True

        # -------------------------------------------------
        # Brightness
        # -------------------------------------------------

        brightness = values["brightness"]

        self.view.set_brightness_range(
            brightness["max"]
        )

        self.view.set_brightness(
            brightness["current"]
        )

        self.view.set_brightness_sensitive(
            True
        )

        # -------------------------------------------------
        # Contrast
        # -------------------------------------------------

        contrast = values["contrast"]

        self.view.set_contrast_range(
            contrast["max"]
        )

        self.view.set_contrast(
            contrast["current"]
        )

        self.view.set_contrast_sensitive(
            True
        )

        self.updating_ui = False

        self.view.set_status(
            "Ready"
        )

        return False

    # =====================================================
    # BRIGHTNESS EVENT
    # =====================================================

    def on_brightness_changed(self, slider):

        if self.updating_ui:
            return

        if not slider.is_sensitive():
            return

        if self.selected_display is None:
            return

        value = int(
            slider.get_value()
        )

        self.schedule_vcp_update(
            "brightness",
            self.selected_display,
            value
        )

    # =====================================================
    # CONTRAST EVENT
    # =====================================================

    def on_contrast_changed(self, slider):

        if self.updating_ui:
            return

        if not slider.is_sensitive():
            return

        if self.selected_display is None:
            return

        value = int(
            slider.get_value()
        )

        self.schedule_vcp_update(
            "contrast",
            self.selected_display,
            value
        )

    # =====================================================
    # DEBOUNCE
    # =====================================================

    def schedule_vcp_update(
        self,
        setting,
        display,
        value
    ):

        if setting == "brightness":

            timer_attr = (
                "brightness_timer"
            )

        else:

            timer_attr = (
                "contrast_timer"
            )

        old_timer = getattr(
            self,
            timer_attr
        )

        if old_timer is not None:

            GLib.source_remove(
                old_timer
            )

        def submit_update():

            setattr(
                self,
                timer_attr,
                None
            )

            self.queue_vcp_update(
                setting,
                display,
                value
            )

            return False

        timer = GLib.timeout_add(
            self.DEBOUNCE_MS,
            submit_update
        )

        setattr(
            self,
            timer_attr,
            timer
        )

    # =====================================================
    # LATEST-VALUE-WINS QUEUE
    # =====================================================

    def queue_vcp_update(
        self,
        setting,
        display,
        value
    ):

        if setting == "brightness":

            operation = (
                self.brightness_operation
            )

        else:

            operation = (
                self.contrast_operation
            )

        with self.operation_lock:

            # -------------------------------------------------
            # If an operation is already running:
            #
            # Don't start another one.
            #
            # Just replace the pending value.
            # -------------------------------------------------

            if operation["active"]:

                operation["pending"] = {
                    "display": display,
                    "value": value
                }

                return

            # -------------------------------------------------
            # No operation running.
            # -------------------------------------------------

            operation["active"] = True

        self.execute_vcp_operation(
            setting,
            display,
            value
        )

    # =====================================================
    # EXECUTE VCP OPERATION
    # =====================================================

    def execute_vcp_operation(
        self,
        setting,
        display,
        value
    ):

        self.view.set_status(
            f"Updating {setting}..."
        )

        self.submit(
            self.set_vcp,
            lambda result, error:
                self.on_vcp_operation_finished(
                    setting,
                    result,
                    error
                ),
            setting,
            display,
            value
        )

    # =====================================================
    # ACTUAL VCP OPERATION
    #
    # This executes in the worker thread.
    # =====================================================

    def set_vcp(
        self,
        setting,
        display,
        value
    ):

        if setting == "brightness":

            self.model.set_brightness(
                display,
                value
            )

        elif setting == "contrast":

            self.model.set_contrast(
                display,
                value
            )

        return {
            "setting": setting,
            "display": display,
            "value": value
        }

    # =====================================================
    # OPERATION COMPLETE
    # =====================================================

    def on_vcp_operation_finished(
        self,
        setting,
        result,
        error
    ):

        if error is not None:

            print(
                f"{setting} update failed:",
                error
            )

        # -------------------------------------------------
        # Get corresponding queue
        # -------------------------------------------------

        if setting == "brightness":

            operation = (
                self.brightness_operation
            )

        else:

            operation = (
                self.contrast_operation
            )

        next_operation = None

        with self.operation_lock:

            # Current operation is complete.
            operation["active"] = False

            # -------------------------------------------------
            # Check whether a newer value arrived while the
            # previous operation was running.
            # -------------------------------------------------

            if operation["pending"] is not None:

                next_operation = (
                    operation["pending"]
                )

                operation["pending"] = None

                operation["active"] = True

        # -------------------------------------------------
        # Start latest pending value.
        # -------------------------------------------------

        if next_operation is not None:

            self.execute_vcp_operation(
                setting,
                next_operation["display"],
                next_operation["value"]
            )

        else:

            if error is not None:

                self.view.set_status(
                    f"{setting.capitalize()} update failed"
                )

            else:

                self.view.set_status(
                    f"{setting.capitalize()} "
                    f"set to "
                    f"{result['value']}"
                )

        return False

    # =====================================================
    # CANCEL PENDING DEBOUNCE
    # =====================================================

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
        # Discard queued-but-not-started values.
        #
        # Do NOT cancel an operation already executing in
        # ddcutil because Python cannot safely kill that
        # worker operation.
        # -------------------------------------------------

        with self.operation_lock:

            self.brightness_operation[
                "pending"
            ] = None

            self.contrast_operation[
                "pending"
            ] = None

    # =====================================================
    # REFRESH
    # =====================================================

    def on_refresh(self, button):

        self.cancel_pending_updates()

        self.load_monitors()

    # =====================================================
    # SHUTDOWN
    # =====================================================

    def on_destroy(self, widget):

        self.cancel_pending_updates()

        self.executor.shutdown(
            wait=False,
            cancel_futures=True
        )

        return False
