#!/usr/bin/env python3
# juminai @ github

import dbus
import json
import gi
import subprocess
import os 
import requests
from io import BytesIO
from PIL import Image, ImageFilter, ImageEnhance

from gi.repository import GLib
from dbus.mainloop.glib import DBusGMainLoop

cache_dir = os.path.expandvars("$XDG_CACHE_HOME/eww/mpris")
os.makedirs(cache_dir, exist_ok=True)

favorite = 'spotify'

def get_player_property(player_interface, prop):
    try:
        return player_interface.Get("org.mpris.MediaPlayer2.Player", prop)
    except dbus.exceptions.DBusException:
        return None


def format_time(seconds):
    if seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes:02d}:{remaining_seconds:02d}"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        remaining_seconds = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{remaining_seconds:02d}"
    

def clean_name(name):
    name = name.split(".instance")[0]
    name = name.replace("org.mpris.MediaPlayer2.", "")
    return name


def get_icon(name):
    player_name = clean_name(name)

    if player_name == "firefox":
        icon = ""
    elif player_name == "brave":
        icon = ""
    elif player_name == "spotify":
        icon = ""
    elif player_name == "cider":
        icon = ""
    elif player_name in ["chrome", "chromium"]:
        icon = ""
    else:
        icon = ""

    return icon


def artwork_blur(artwork, title):
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        title = title.replace(char, "_")

    if not artwork:
        return os.path.expandvars("$XDG_CONFIG_HOME/eww/assets/default.png")

    file = f"{cache_dir}/{title}.png"

    if os.path.isfile(file):
        return file
    else:
        if artwork.startswith("https://"):
            link = requests.get(artwork)
            if link.status_code == 200:
                image = Image.open(BytesIO(link.content))
        else:
            artwork = artwork.replace("file://", "")
            image = Image.open(artwork)
        
        blurred = image.filter(ImageFilter.GaussianBlur(radius=8))
        blurred_darkened = ImageEnhance.Brightness(blurred).enhance(0.4)
        blurred_darkened.save(file)
        return file

   
def mpris_data():
    bus_names = session_bus.list_names()

    players = []
    favorite_player = None

    for name in bus_names:
        if "org.mpris.MediaPlayer2" in name:
            player = session_bus.get_object(name, "/org/mpris/MediaPlayer2")
            player_interface = dbus.Interface(player, "org.freedesktop.DBus.Properties")
            metadata = get_player_property(player_interface, "Metadata")
            playback_status = get_player_property(player_interface, "PlaybackStatus")
            
            shuffle = bool(get_player_property(player_interface, "Shuffle"))
            loop_status = get_player_property(player_interface, "LoopStatus")
            can_go_next = bool(get_player_property(player_interface, "CanGoNext"))
            can_go_previous = bool(get_player_property(player_interface, "CanGoPrevious"))
            can_play = bool(get_player_property(player_interface, "CanPlay"))
            can_pause = bool(get_player_property(player_interface, "CanPause"))
            volume = get_player_property(player_interface, "Volume")
            length = metadata.get("mpris:length") 
            length = length // 1000000 if length is not None else -1
            position = get_player_property(player_interface, "Position")
            position = position // 1000000 if position is not None else -1
            artist = metadata.get("xesam:artist", ["Unknown"])
            artwork = metadata.get("mpris:artUrl", None)
            title = metadata.get("xesam:title", "Unknown")
            album = metadata.get("xesam:album", "Unknown")
            player_name = clean_name(name)

            player_data = {
                "name": player_name,
                "title": title,
                "artist": artist[0] if artist else None,
                "album": album,
                "artUrl": artwork_blur(artwork, title),
                "status": playback_status,
                "length": length,
                "lengthStr": format_time(length) if length != -1 else -1,
                "loop": loop_status,
                "shuffle": shuffle,
                "volume": int(volume * 100) if volume is not None else -1,
                "canGoNext": can_go_next,
                "canGoPrevious": can_go_previous,
                "canPlay": can_play,
                "canPause": can_pause,
                "icon": get_icon(name),
            }

            players.append(player_data)

            if favorite == player_name:
                favorite_player = player_data

    media = {"players": players}
    
    if favorite_player is not None:
        media["favorite"] = favorite_player
    elif players:
        media["favorite"] = players[0]
    else:
        media["favorite"] = None

    return media


def properties_changed():
    session_bus.add_signal_receiver(
        update_eww,
        dbus_interface="org.freedesktop.DBus.Properties",
        signal_name="PropertiesChanged",
        path="/org/mpris/MediaPlayer2"
    )


def player_changed():
    session_bus.add_signal_receiver(
        update_eww,
        dbus_interface="org.freedesktop.DBus",
        signal_name="NameOwnerChanged",
        path="/org/freedesktop/DBus"
    )


def update_eww(interface, changed_properties, invalidated_properties):
    if "org.mpris.MediaPlayer2" in interface:
        subprocess.run([
          "eww", "update", f"mpris={json.dumps(mpris_data())}"
        ])


if __name__ == "__main__":
    DBusGMainLoop(set_as_default=True)
    session_bus = dbus.SessionBus()
    loop = GLib.MainLoop()
    
    try:
        subprocess.run([
           "eww", "update", f"mpris={json.dumps(mpris_data())}"
        ])
        properties_changed()
        player_changed()
        loop.run()
    except KeyboardInterrupt:
        loop.quit()
