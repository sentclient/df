#!/usr/bin/env python3
# juminai @ github

import json
import os
import subprocess
import sys

SIGNATURE = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE")

def run_command(command):
    result = subprocess.check_output(command, text=True)
    return json.loads(result)

def get_class():
    app_class = run_command(["hyprctl", "activewindow", "-j"])
    if app_class:
        return app_class['class']
    return None

def get_icon():
    app_class = get_class()
    if app_class is not None:
        if app_class == "foot":
            app_icon = ""
        elif app_class == "Brave-browser":
            app_icon = ""
        elif app_class == "code-oss":
            app_icon = ""
        elif app_class == "kotatogram":
            app_icon = ""
        else:
            app_icon = None
        return app_icon
        
def get_workspaces():
    return run_command(["hyprctl", "workspaces", "-j"])

def get_active():
    active_data = run_command(["hyprctl", "monitors", "-j"])
    return active_data[0]['activeWorkspace']['id']

def workspaces():
    WORKSPACE_WINDOWS = get_workspaces()
    workspace_data_dict = {item["id"]: item["windows"] for item in WORKSPACE_WINDOWS}

    workspace_ids = range(1, 7)
    workspaces_data = [{"id": ws, "windows": workspace_data_dict.get(ws, 0)} for ws in workspace_ids]
    return workspaces_data

def get_active_empty():
    workspaces_data = get_workspaces()
    active_workspace_id = get_active()
    
    return all(workspace['windows'] == 0 for workspace in workspaces_data if workspace['id'] == active_workspace_id)

def monitor_socat_output():
    socat_command = ["socat", "-u", f"UNIX-CONNECT:/tmp/hypr/{SIGNATURE}/.socket2.sock", "-"]
    with subprocess.Popen(socat_command, stdout=subprocess.PIPE, text=True) as process:
        for line in process.stdout:
            result = {
                "workspaces": workspaces(),
                "active": get_active(),
                "active_empty": get_active_empty(),
                "class": {"app_name": get_class(), "app_icon": get_icon()}
            }
            sys.stdout.write(json.dumps(result) + "\n")
            sys.stdout.flush()

if __name__ == "__main__":
    result = {
        "workspaces": workspaces(),
        "active": get_active(),
        "active_empty": get_active_empty(),
        "class": {"app_name": get_class(), "app_icon": get_icon()}
    }
    sys.stdout.write(json.dumps(result) + "\n")
    sys.stdout.flush()
    monitor_socat_output()
