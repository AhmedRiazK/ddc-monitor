# DDC Monitor

A GTK3-based Linux desktop application for controlling and monitoring external displays through **DDC/CI** using `ddcutil` and **D-Bus**.

The project follows a clean **MVC architecture** with asynchronous monitor operations to keep the UI responsive. It supports monitor detection, brightness and contrast control, debounced slider updates, and latest-value-wins command handling.

### Features

- Monitor detection through DDC/CI
- Brightness control
- Contrast control
- GTK3 desktop interface
- D-Bus-based monitor control daemon
- Asynchronous DDC operations
- 200 ms slider debounce
- Latest-value-wins update queue
- GNOME application launcher integration
- systemd/D-Bus service integration
- Designed for Linux/Ubuntu

### Architecture

```text
GTK3 UI
   │
   ▼
Controller
   │
   ▼
Model
   │
   ▼
D-Bus
   │
   ▼
DDC Monitor Daemon
   │
   ▼
ddcutil
   │
   ▼
Monitor DDC/CI
```

### Project Structure

```text
ddc-monitor/
├── daemon/       # D-Bus monitor-control daemon
├── dbus/         # D-Bus service and policy configuration
├── ui/           # GTK3 UI, MVC components and launcher
├── systemd/      # systemd service configuration
└── install.sh    # Installation script
```

The project is intended as a foundation for a native Linux monitor-control application with future GNOME desktop integration and support for additional DDC/CI features.
