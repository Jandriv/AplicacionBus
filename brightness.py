"""Control de brillo para dispositivos Linux."""
import re
import shutil
import subprocess
from pathlib import Path


class BrightnessController:
    """Cambia el brillo mediante backlight del sistema o xrandr."""

    def __init__(self):
        self.backlight_path = self._find_backlight()
        self.output = self._find_xrandr_output()

    @property
    def available(self):
        return self.backlight_path is not None or self.output is not None

    @property
    def description(self):
        if self.backlight_path:
            return f"backlight: {self.backlight_path.name}"
        if self.output:
            return f"xrandr: {self.output}"
        return "no disponible"

    def _find_backlight(self):
        backlight_dir = Path("/sys/class/backlight")
        try:
            devices = [path for path in backlight_dir.iterdir() if (path / "brightness").exists()]
            return devices[0] if devices else None
        except OSError:
            return None

    def _find_xrandr_output(self):
        if shutil.which("xrandr") is None:
            return None
        try:
            result = subprocess.run(
                ["xrandr", "--query"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=3,
                check=False,
            )
            connected_outputs = []
            for line in result.stdout.splitlines():
                match = re.match(r"^(\S+) connected(?: primary)?\s", line)
                if match:
                    output = match.group(1)
                    if " connected primary " in line:
                        return output
                    connected_outputs.append(output)
            if connected_outputs:
                return connected_outputs[0]
        except (OSError, subprocess.TimeoutExpired):
            pass
        return None

    def get(self, fallback=100):
        if self.backlight_path:
            try:
                current = int((self.backlight_path / "brightness").read_text().strip())
                maximum = int((self.backlight_path / "max_brightness").read_text().strip())
                return max(10, min(100, round(current * 100 / maximum))) if maximum else fallback
            except (OSError, ValueError, ZeroDivisionError):
                return fallback
        return fallback

    def set(self, value):
        value = max(10, min(100, int(value)))
        if self.backlight_path:
            try:
                maximum = int((self.backlight_path / "max_brightness").read_text().strip())
                (self.backlight_path / "brightness").write_text(str(round(maximum * value / 100)))
                return True, "Brillo aplicado"
            except (OSError, ValueError):
                pass

        if self.output:
            try:
                result = subprocess.run(
                    ["xrandr", "--output", self.output, "--brightness", f"{value / 100:.2f}"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=3,
                    check=False,
                )
                if result.returncode == 0:
                    return True, "Brillo aplicado"
                return False, result.stderr.strip() or "xrandr rechazó el brillo"
            except (OSError, subprocess.TimeoutExpired) as error:
                return False, str(error)

        return False, "Este dispositivo no permite controlar el brillo desde la aplicación"
