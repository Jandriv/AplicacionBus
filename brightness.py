"""Control de brillo para dispositivos Linux."""
import re
import shutil
import subprocess
from pathlib import Path


class BrightnessController:
    """Cambia el brillo usando el backend disponible en el sistema."""

    def __init__(self):
        self.backlight_path = self._find_backlight()
        self.brightnessctl = shutil.which("brightnessctl")
        self.xbacklight = shutil.which("xbacklight")
        self.output = self._find_xrandr_output()

    @property
    def available(self):
        return any((self.backlight_path, self.brightnessctl, self.xbacklight, self.output))

    @property
    def description(self):
        if self.backlight_path:
            return f"backlight: {self.backlight_path.name}"
        if self.brightnessctl:
            return "brightnessctl"
        if self.xbacklight:
            return "xbacklight"
        if self.output:
            return f"xrandr: {self.output}"
        return "no disponible"

    def _find_backlight(self):
        backlight_dir = Path("/sys/class/backlight")
        try:
            devices = [path for path in backlight_dir.iterdir() if (path / "brightness").exists()]
            preferred = (
                "intel_backlight", "amdgpu_bl", "nvidia_wmi_ec_backlight",
                "nvidia_wmi_backlight", "acpi_video"
            )
            devices.sort(key=lambda path: next(
                (index for index, name in enumerate(preferred) if path.name.startswith(name)),
                len(preferred)
            ))
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
        if self.brightnessctl:
            result = self._run_command([self.brightnessctl, "get"])
            maximum = self._run_command([self.brightnessctl, "max"])
            try:
                current = int(result[0].strip())
                maximum_value = int(maximum[0].strip())
                return max(10, min(100, round(current * 100 / maximum_value)))
            except (ValueError, ZeroDivisionError):
                pass

        if self.backlight_path:
            try:
                current = int((self.backlight_path / "brightness").read_text().strip())
                maximum = int((self.backlight_path / "max_brightness").read_text().strip())
                return max(10, min(100, round(current * 100 / maximum))) if maximum else fallback
            except (OSError, ValueError, ZeroDivisionError):
                return fallback
        return fallback

    def _run_command(self, command):
        try:
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=3,
                check=False,
            )
            return result.stdout, result.stderr, result.returncode
        except (OSError, subprocess.TimeoutExpired) as error:
            return "", str(error), 1

    def _run_set_command(self, command):
        stdout, stderr, returncode = self._run_command(command)
        if returncode == 0:
            return True, "Brillo aplicado"
        return False, stderr.strip() or "El controlador rechazó el brillo"

    def set(self, value):
        value = max(10, min(100, int(value)))
        if self.brightnessctl:
            success, message = self._run_set_command(
                [self.brightnessctl, "set", f"{value}%"]
            )
            if success:
                current = self.get(fallback=0)
                if abs(current - value) <= 2:
                    return True, "Brillo aplicado"
                return False, "brightnessctl no pudo verificar el brillo aplicado"

        if self.backlight_path:
            try:
                maximum = int((self.backlight_path / "max_brightness").read_text().strip())
                target = round(maximum * value / 100)
                (self.backlight_path / "brightness").write_text(str(target))
                current = int((self.backlight_path / "brightness").read_text().strip())
                if abs(current - target) <= 1:
                    return True, "Brillo aplicado"
                return False, "El backlight no confirmó el brillo aplicado"
            except (OSError, ValueError):
                pass

        if self.xbacklight:
            success, message = self._run_set_command(
                [self.xbacklight, "-set", str(value)]
            )
            if success:
                return success, message

        if self.output:
            success, message = self._run_set_command([
                "xrandr", "--output", self.output,
                "--brightness", f"{value / 100:.2f}"
            ])
            if success:
                return success, message
            if "gamma size is 0" in message.lower():
                return False, "La pantalla no admite brillo mediante xrandr"
            return False, message

        return False, "Este dispositivo no permite controlar el brillo desde la aplicación"
