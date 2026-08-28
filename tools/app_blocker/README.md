# App Internet Blocker (Norton 360 compatible)

A Tkinter GUI to block or unblock specific applications' internet access on
Windows machines running Norton 360.

## Important: how this works with Norton 360

Norton 360's Smart Firewall does not provide a public API or command-line
interface for adding per-application rules, so nothing can script Norton's
own rule store directly. In practice Norton runs alongside the Windows
Filtering Platform rather than replacing it, so a block rule created in
Windows Firewall (`netsh advfirewall`) still stops the target process from
reaching the network even with Norton active. This tool manages those
Windows Firewall rules (tagged with an `AppBlocker_` prefix) instead.

If Norton is configured to take over network filtering entirely and a
blocked app still gets through, also mark that program as **Restricted** in
Norton's own **Settings → Firewall → Program Control** list — this script
cannot reach into Norton's private configuration, only the OS firewall.

## Requirements

- Windows 10/11
- Python 3.8+
- Run as **Administrator** (firewall rule changes require elevated rights)

## Usage

```
python app_blocker_gui.py
```

1. Click **Browse...** and select the `.exe` you want to block.
2. Click **Block Selected App** to create inbound + outbound block rules.
3. The "Currently blocked applications" list shows every app blocked by
   this tool. Select one and click **Unblock Highlighted** (or re-select
   the exe path and click **Unblock Selected App**) to restore its access.
4. **Refresh List** re-reads the current rules from Windows Firewall.

## Notes

- Rules are named `AppBlocker_<exe name>_in` / `AppBlocker_<exe name>_out`
  so they're easy to identify and won't collide with unrelated rules.
- Removing this tool does not remove already-created rules; use
  **Unblock** on each app first, or run:
  `netsh advfirewall firewall delete rule name=all` and re-add any other
  rules you still need (not recommended — it clears everything).
