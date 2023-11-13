#!/usr/bin/env python3
# juminai @ github

import json
import subprocess
import gi
import dbus
import dbus.service

gi.require_version("Gtk", "3.0")

from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import Gio, Gtk, GLib


class Apps(dbus.service.Object):
    def __init__(self):
        super().__init__(dbus.service.BusName("com.juminai.Apps", bus=dbus.SessionBus()), "/com/juminai/Apps")

        self.apps_list = {
            "apps": [],
            "dock_apps": []
        }
        
        self.DOCK_LIST = [
            "spotify",
            "discord",
            "foot",
            "kotatogram desktop",
            "code - oss",
            "thunar file manager",
            "brave",
            "transmission",
        ]


    def installed_apps(self):
        app_info = Gio.AppInfo
        app_infos = app_info.get_all()

        app_list = []
        
        for app_info in app_infos:
            get_icon = app_info.get_icon()
            
            if get_icon:
                if get_icon.get_names():
                    icon_name = get_icon.get_names()[0]
                    icon_location = self.get_themed_icon(icon_name)
                else:
                    icon_location = None
            else:
                icon_location = None
            
            if app_info.should_show():
                app_dict = {
                    "name": app_info.get_display_name(),
                    "icon": icon_location,
                    "description": app_info.get_description(),
                    "desktop": app_info.get_id()
                }
                
                app_list.append(app_dict)
        return app_list


    def get_themed_icon(self, icon_name):
        theme = Gtk.IconTheme.get_default()
        icon_info = theme.lookup_icon(icon_name, 128, 0)

        if icon_info is not None:
            return icon_info.get_filename()


    def get_dock_apps(self):
        app_list = self.installed_apps()
        dock_apps_list = []

        for app in app_list:
            if app["name"].lower() in self.DOCK_LIST:
                dock_apps_list.append(app)
        return dock_apps_list


    def populate(self):
        self.apps_list["apps"] = self.installed_apps()
        self.apps_list["dock_apps"] = self.get_dock_apps()


    @dbus.service.method("com.juminai.Apps", in_signature="s", out_signature="")
    def FilterApps(self, query):
        self.apps_list["apps"] = self.installed_apps()
        
        filtered_data = []
        for entry in self.apps_list["apps"]:
            if query.lower() in entry["name"].lower() or (
                entry["description"] and query.lower() in entry["description"].lower()):
                filtered_data.append(entry)
        
        self.apps_list["apps"] = filtered_data
        self.update_eww()


    def update_eww(self):
        subprocess.run([
            "eww", "update", f"apps={json.dumps(self.apps_list)}"
        ])


if __name__ == "__main__":
    DBusGMainLoop(set_as_default=True)
    loop = GLib.MainLoop()
    apps = Apps()
    apps.populate()
    apps.update_eww()
    try:
        loop.run()
    except KeyboardInterrupt:
        exit(0)
