#!/usr/bin/env python3
# juminai @ github

import dbus
import json
import sys
import time

from mpris import get_player_property, format_time, clean_name
    
def get_positions():
    session_bus = dbus.SessionBus()
    bus_names = session_bus.list_names()
    
    positions = {}

    for name in bus_names:
        if "org.mpris.MediaPlayer2." in name:
            try:
                player = session_bus.get_object(name, "/org/mpris/MediaPlayer2")
                player_interface = dbus.Interface(player, "org.freedesktop.DBus.Properties")

                position = get_player_property(player_interface, "Position")
                position = position // 1000000 if position is not None else -1
                
                positions[clean_name(name)] = {
                    "position": position, 
                    "positionStr": format_time(position) if position != -1 else -1
                }

            except dbus.exceptions.DBusException:
                pass
    
    return positions

if __name__ == "__main__":
    try:
        while True:
            sys.stdout.write(json.dumps(get_positions()) + "\n")
            sys.stdout.flush()
            time.sleep(1)
    except KeyboardInterrupt:
        sys.exit(0)
