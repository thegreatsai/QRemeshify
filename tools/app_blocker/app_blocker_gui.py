#!/usr/bin/env python3
"""
App Internet Blocker (Norton 360 compatible)
=============================================

A small Tkinter GUI that blocks/unblocks selected applications' internet
access on Windows.

Why not talk to Norton 360 directly?
-------------------------------------
Norton 360's Smart Firewall does not expose a public command-line or
scripting interface for adding per-application block rules, so it cannot be
driven directly from a script. What Norton *does* respect is the underlying
Windows Filtering Platform: when Norton's firewall is installed it normally
runs alongside the Windows Firewall service rather than disabling it, and a
block rule created in Windows Firewall (via `netsh advfirewall`) still
prevents the process from reaching the network even while Norton is active.
This tool therefore manages standard Windows Firewall outbound/inbound
rules, tagged with a recognizable name prefix, so they are easy to find,
list, and remove again. Run it elevated (as Administrator) since firewall
rule changes require admin rights.

If you have Norton's firewall set to fully take over filtering and it
still lets blocked traffic through, add the same executable to Norton's
own "Program Control" list as Restricted/Blocked -- this script cannot
reach into Norton's private rule store, only Windows Firewall's.

Usage
-----
    python app_blocker_gui.py

Requires: Windows, Python 3.8+, run as Administrator.
"""

import ctypes
import os
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

RULE_PREFIX = "AppBlocker_"


def is_admin() -> bool:
    if os.name != "nt":
        return False
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def run_netsh(args):
    """Run a netsh command and return (success, output)."""
    try:
        result = subprocess.run(
            ["netsh"] + args,
            capture_output=True,
            text=True,
            timeout=15,
        )
        ok = result.returncode == 0
        output = (result.stdout or "") + (result.stderr or "")
        return ok, output.strip()
    except FileNotFoundError:
        return False, "netsh not found (this tool only works on Windows)."
    except Exception as exc:
        return False, str(exc)


def rule_name_for(app_path: str) -> str:
    base = os.path.basename(app_path)
    return f"{RULE_PREFIX}{base}"


def block_app(app_path: str):
    name = rule_name_for(app_path)
    ok_out, out1 = run_netsh(
        [
            "advfirewall", "firewall", "add", "rule",
            f"name={name}_out",
            "dir=out",
            "action=block",
            f"program={app_path}",
            "enable=yes",
        ]
    )
    ok_in, out2 = run_netsh(
        [
            "advfirewall", "firewall", "add", "rule",
            f"name={name}_in",
            "dir=in",
            "action=block",
            f"program={app_path}",
            "enable=yes",
        ]
    )
    return (ok_out and ok_in), (out1 + "\n" + out2).strip()


def unblock_app(app_path: str):
    name = rule_name_for(app_path)
    ok1, out1 = run_netsh(
        ["advfirewall", "firewall", "delete", "rule", f"name={name}_out"]
    )
    ok2, out2 = run_netsh(
        ["advfirewall", "firewall", "delete", "rule", f"name={name}_in"]
    )
    return (ok1 or ok2), (out1 + "\n" + out2).strip()


def list_blocked_rule_names():
    ok, out = run_netsh(["advfirewall", "firewall", "show", "rule", "name=all"])
    if not ok:
        return []
    names = set()
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("Rule Name:"):
            rule_name = line.split(":", 1)[1].strip()
            if rule_name.startswith(RULE_PREFIX):
                for suffix in ("_out", "_in"):
                    if rule_name.endswith(suffix):
                        rule_name = rule_name[: -len(suffix)]
                names.add(rule_name[len(RULE_PREFIX):])
    return sorted(names)


class AppBlockerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("App Internet Blocker (Norton 360 compatible)")
        self.geometry("560x420")
        self.resizable(False, False)

        self.blocked_apps = {}  # display name -> full path

        self._build_widgets()
        self._refresh_blocked_list()

        if os.name == "nt" and not is_admin():
            messagebox.showwarning(
                "Administrator required",
                "This tool must be run as Administrator to change firewall "
                "rules. Restart it with elevated privileges.",
            )

    def _build_widgets(self):
        header = tk.Label(
            self,
            text="Block or unblock an application's internet access.\n"
            "Rules are applied via Windows Firewall and are honored\n"
            "alongside Norton 360's Smart Firewall.",
            justify="left",
            fg="#333",
        )
        header.pack(padx=12, pady=(12, 4), anchor="w")

        pick_frame = tk.Frame(self)
        pick_frame.pack(fill="x", padx=12, pady=6)

        self.path_var = tk.StringVar()
        entry = tk.Entry(pick_frame, textvariable=self.path_var, width=55)
        entry.pack(side="left", fill="x", expand=True)

        browse_btn = tk.Button(pick_frame, text="Browse...", command=self._browse)
        browse_btn.pack(side="left", padx=(6, 0))

        action_frame = tk.Frame(self)
        action_frame.pack(fill="x", padx=12, pady=6)

        block_btn = tk.Button(
            action_frame, text="Block Selected App", command=self._block_selected,
            bg="#c0392b", fg="white", width=20,
        )
        block_btn.pack(side="left")

        unblock_btn = tk.Button(
            action_frame, text="Unblock Selected App", command=self._unblock_selected,
            bg="#27ae60", fg="white", width=20,
        )
        unblock_btn.pack(side="left", padx=(8, 0))

        list_label = tk.Label(self, text="Currently blocked applications:", anchor="w")
        list_label.pack(fill="x", padx=12, pady=(12, 2))

        list_frame = tk.Frame(self)
        list_frame.pack(fill="both", expand=True, padx=12, pady=(0, 6))

        self.listbox = tk.Listbox(list_frame)
        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=scrollbar.set)
        self.listbox.bind("<<ListboxSelect>>", self._on_select)

        bottom_frame = tk.Frame(self)
        bottom_frame.pack(fill="x", padx=12, pady=(0, 12))

        refresh_btn = tk.Button(bottom_frame, text="Refresh List", command=self._refresh_blocked_list)
        refresh_btn.pack(side="left")

        unblock_from_list_btn = tk.Button(
            bottom_frame, text="Unblock Highlighted",
            command=self._unblock_highlighted,
        )
        unblock_from_list_btn.pack(side="left", padx=(8, 0))

        self.status_var = tk.StringVar(value="Ready.")
        status_label = tk.Label(self, textvariable=self.status_var, anchor="w", fg="#555")
        status_label.pack(fill="x", padx=12, pady=(0, 8))

    def _browse(self):
        filetypes = [("Executables", "*.exe"), ("All files", "*.*")]
        path = filedialog.askopenfilename(title="Select application", filetypes=filetypes)
        if path:
            self.path_var.set(path)

    def _block_selected(self):
        path = self.path_var.get().strip()
        if not path:
            messagebox.showinfo("No app selected", "Choose an application first.")
            return
        if not os.path.isfile(path):
            messagebox.showerror("Invalid path", f"File not found:\n{path}")
            return
        ok, output = block_app(path)
        if ok:
            self.status_var.set(f"Blocked: {os.path.basename(path)}")
            self._refresh_blocked_list()
        else:
            self.status_var.set("Failed to block app.")
            messagebox.showerror("Failed to block app", output or "Unknown error.")

    def _unblock_selected(self):
        path = self.path_var.get().strip()
        if not path:
            messagebox.showinfo("No app selected", "Choose an application first.")
            return
        ok, output = unblock_app(path)
        if ok:
            self.status_var.set(f"Unblocked: {os.path.basename(path)}")
        else:
            self.status_var.set("No matching block rule found.")
        self._refresh_blocked_list()

    def _unblock_highlighted(self):
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showinfo("Nothing selected", "Select an app in the list first.")
            return
        display_name = self.listbox.get(selection[0])
        full_path = self.blocked_apps.get(display_name, display_name)
        ok, output = unblock_app(full_path)
        if ok:
            self.status_var.set(f"Unblocked: {display_name}")
        else:
            self.status_var.set("Failed to remove rule.")
            messagebox.showerror("Failed to unblock app", output or "Unknown error.")
        self._refresh_blocked_list()

    def _on_select(self, _event):
        selection = self.listbox.curselection()
        if selection:
            display_name = self.listbox.get(selection[0])
            self.path_var.set(self.blocked_apps.get(display_name, display_name))

    def _refresh_blocked_list(self):
        self.listbox.delete(0, tk.END)
        self.blocked_apps.clear()
        names = list_blocked_rule_names()
        for name in names:
            self.blocked_apps[name] = name
            self.listbox.insert(tk.END, name)
        self.status_var.set(f"{len(names)} app(s) currently blocked.")


def main():
    if os.name != "nt":
        print("This tool manages Windows Firewall rules and only runs on Windows.")
        sys.exit(1)
    app = AppBlockerGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
