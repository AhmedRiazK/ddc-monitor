#!/usr/bin/python3

import gi

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk

from model import MonitorModel
from view import MonitorView
from controller import MonitorController


def main():

    model = MonitorModel()

    view = MonitorView()

    controller = MonitorController(
        model,
        view
    )

    controller.start()

    view.show_all()

    Gtk.main()


if __name__ == "__main__":
    main()
