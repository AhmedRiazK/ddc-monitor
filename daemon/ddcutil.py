import subprocess
import re


class DDCUtilError(Exception):
    pass


class DDCUtil:

    def _run(self, args):
        try:
            result = subprocess.run(
                ["ddcutil"] + args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )
        except subprocess.TimeoutExpired:
            raise DDCUtilError("ddcutil command timed out")

        if result.returncode != 0:
            raise DDCUtilError(
                result.stderr.strip() or
                result.stdout.strip() or
                "ddcutil failed"
            )

        return result.stdout

    def detect(self):
        output = self._run(["detect"])

        displays = []
        current = None

        for line in output.splitlines():

            m = re.search(r"Display\s+(\d+)", line)

            if m:
                if current:
                    displays.append(current)

                current = {
                    "id": int(m.group(1)),
                    "model": "Unknown",
                    "manufacturer": "Unknown"
                }

            if current is None:
                continue

            m = re.search(r"Mfg id:\s*(.*)", line)

            if m:
                current["manufacturer"] = m.group(1).strip()

            m = re.search(r"Model:\s*(.*)", line)

            if m:
                current["model"] = m.group(1).strip()

        if current:
            displays.append(current)

        return displays

    def get_vcp(self, display, code):

        output = self._run([
            "--display",
            str(display),
            "getvcp",
            code
        ])

        match = re.search(
            r"current value\s*=\s*(\d+).*max value\s*=\s*(\d+)",
            output,
            re.IGNORECASE
        )

        if not match:
            raise DDCUtilError(
                f"Unable to parse VCP {code}: {output}"
            )

        return {
            "current": int(match.group(1)),
            "max": int(match.group(2))
        }

    def set_vcp(self, display, code, value):

        self._run([
            "--display",
            str(display),
            "setvcp",
            code,
            str(value)
        ])

    def capabilities(self, display):

        return self._run([
            "--display",
            str(display),
            "capabilities"
        ])
