"""
agentsitter.py
--------------
Drop this file into your project folder.
Add three lines to your agent. That's it.

Usage:
    import agentsitter

    sitter = agentsitter.watch(alert="you@email.com")

    # Then after every API call, track the cost:
    sitter.track(cost=0.04)

Agentsitter sends your last 10 costs to the TrustLog API
every 60 seconds and prints an alert if your agent goes RED.
"""

import time
import threading
import requests

TRUSTLOG_API = "https://trustlog-api.onrender.com/analyze"


class Agentsitter:
    def __init__(self, alert: str = None, check_every: int = 60, verbose: bool = True):
        self.alert_email = alert
        self.check_every = check_every
        self.verbose = verbose
        self._costs = []
        self._lock = threading.Lock()
        self._last_status = None

        if self.verbose:
            print("🟢 Agentsitter is watching your agent.")
            if alert:
                print(f"   Alerts → {alert}")
            print(f"   Checking every {check_every}s\n")

        self._start()

    def track(self, cost: float):
        """Call this after every API call with the cost in £/$ of that call."""
        with self._lock:
            self._costs.append(round(float(cost), 6))
            if len(self._costs) > 50:
                self._costs = self._costs[-50:]

    def _check(self):
        with self._lock:
            recent = self._costs[-10:] if len(self._costs) >= 3 else []

        if not recent:
            return

        try:
            response = requests.post(
                TRUSTLOG_API,
                json={"calls": recent},
                timeout=8
            )
            data = response.json()
            status = data.get("status", "UNKNOWN")
            message = data.get("message", "")
            total = sum(recent)

            status_icon = {"GREEN": "🟢", "AMBER": "🟡", "RED": "🔴"}.get(status, "⚪")

            if self.verbose:
                print(f"{status_icon} Agentsitter | Status: {status} | Last 10 calls: £{total:.4f} | {message}")

            if status == "RED":
                self._fire_alert(status, message, total)

            self._last_status = status

        except requests.exceptions.RequestException as e:
            if self.verbose:
                print(f"⚠️  Agentsitter | Could not reach API: {e}")

    def _fire_alert(self, status: str, message: str, total: float):
        """Fires when status hits RED. Extend this to add Slack, webhooks, SMS."""
        print("\n" + "=" * 55)
        print("🔴  AGENTSITTER ALERT — YOUR AGENT NEEDS ATTENTION")
        print("=" * 55)
        print(f"   Status  : {status}")
        print(f"   Message : {message}")
        print(f"   Cost    : £{total:.4f} in last 10 calls")
        if self.alert_email:
            print(f"   Alert   : {self.alert_email} (email coming soon)")
        print("=" * 55 + "\n")

    def _start(self):
        def loop():
            while True:
                time.sleep(self.check_every)
                self._check()

        thread = threading.Thread(target=loop, daemon=True)
        thread.start()

    def status(self):
        """Returns the last known status. Call anytime."""
        return self._last_status


def watch(alert: str = None, check_every: int = 60, verbose: bool = True) -> Agentsitter:
    """
    Start watching your agent.

    Args:
        alert       : your email for RED alerts (optional for now)
        check_every : how often to check in seconds (default 60)
        verbose     : print status updates to console (default True)

    Returns:
        Agentsitter instance with a .track(cost) method
    """
    return Agentsitter(alert=alert, check_every=check_every, verbose=verbose)
