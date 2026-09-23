"""Drive the ide in a real pty and read the screen back.

A minimal emulator for exactly what the tty module sends: cursor moves
(CSI r;c H), clear (CSI 2J), SGR colours (fg recorded per cell), private
modes (ignored), cursor show/hide. Usage: import and call Session.
"""
import os, pty, select, signal, struct, fcntl, termios, time, re, sys

class Screen:
    def __init__(self, cols, rows):
        self.resize(cols, rows)
        self.cursor = (0, 0)
        self.visible = False
        self.fg = None
        self.alt = False
        self.raw = b""

    def resize(self, cols, rows):
        self.cols, self.rows = cols, rows
        self.chars = [[" "] * cols for _ in range(rows)]
        self.fgs = [[None] * cols for _ in range(rows)]

    def feed(self, data):
        self.raw += data
        data = getattr(self, "pending", b"") + data
        cut = data.rfind(b"\x1b")
        if cut >= 0 and not re.search(rb"[A-Za-z~]", data[cut + 2:]) :
            data, self.pending = data[:cut], data[cut:]
        else:
            self.pending = b""
        while data and (data[-1] & 0xC0) == 0x80 or (data and data[-1] >= 0xC0):
            k = len(data) - 1
            while k > 0 and (data[k] & 0xC0) == 0x80: k -= 1
            need = 2 if data[k] >= 0xC0 else 1
            need = 3 if data[k] >= 0xE0 else need
            need = 4 if data[k] >= 0xF0 else need
            if len(data) - k >= need: break
            data, self.pending = data[:k], data[k:] + self.pending
        text = data.decode("utf-8", "replace")
        i = 0
        r, c = self.cursor
        while i < len(text):
            ch = text[i]
            if ch == "\x1b":
                m = re.match(r"\x1b\[([<>?=]?)([0-9;:]*)( ?)([A-Za-z~])", text[i:])
                if not m:
                    i += 1
                    continue
                priv, params, sp, fin = m.groups()
                i += m.end()
                if priv == "" and sp == "":
                    if fin == "H":
                        p = (params or "1;1").split(";")
                        r, c = int(p[0]) - 1, int(p[1]) - 1 if len(p) > 1 else 0
                    elif fin == "J" and params == "2":
                        self.resize(self.cols, self.rows)
                    elif fin == "m":
                        ps = params.split(";")
                        if "38" in ps:
                            k = ps.index("38")
                            self.fg = tuple(int(x) for x in ps[k + 2:k + 5])
                if priv == "?" and params == "25":
                    self.visible = fin == "h"
                if priv == "?" and params == "1049":
                    self.alt = fin == "h"
                continue
            if ch in "\r\n":
                i += 1
                continue
            if 0 <= r < self.rows and 0 <= c < self.cols:
                self.chars[r][c] = ch
                self.fgs[r][c] = self.fg
            c += 1
            i += 1
        self.cursor = (r, c)

    def row(self, r):
        return "".join(self.chars[r])

    def text(self):
        return "\n".join(self.row(r) for r in range(self.rows))


class Session:
    def __init__(self, argv, cwd, env, cols=120, rows=40):
        self.screen = Screen(cols, rows)
        pid, fd = pty.fork()
        if pid == 0:
            os.chdir(cwd)
            os.execvpe(argv[0], argv, {**os.environ, **env})
        self.pid, self.fd = pid, fd
        self.set_size(cols, rows)
        self.exit = None

    def set_size(self, cols, rows):
        fcntl.ioctl(self.fd, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))
        self.screen.cols, self.screen.rows = cols, rows

    def pump(self, seconds=0.5):
        end = time.time() + seconds
        while time.time() < end:
            ready, _, _ = select.select([self.fd], [], [], 0.05)
            if ready:
                try:
                    data = os.read(self.fd, 65536)
                except OSError:
                    data = b""
                if data:
                    self.screen.feed(data)
                    end = max(end, time.time() + 0.15)
                else:
                    time.sleep(0.05)
            done, status = os.waitpid(self.pid, os.WNOHANG)
            if done:
                self.exit = os.waitstatus_to_exitcode(status)
                try:
                    while True:
                        ready, _, _ = select.select([self.fd], [], [], 0.1)
                        if not ready:
                            break
                        data = os.read(self.fd, 65536)
                        if not data:
                            break
                        self.screen.feed(data)
                except OSError:
                    pass
                break

    def wait_for(self, needle, seconds=20):
        end = time.time() + seconds
        while time.time() < end:
            self.pump(0.2)
            if needle in self.screen.text():
                return True
            if self.exit is not None:
                return False
        return False

    def keys(self, data, settle=0.6):
        os.write(self.fd, data)
        self.pump(settle)

    def resize(self, cols, rows, settle=1.0):
        self.set_size(cols, rows)
        self.screen.resize(cols, rows)
        self.pump(settle)
