"""
Remote access to lys Python Interface.

When lys is launched with --remote option, lys accepts commands from other processes (such as Claude Code via MCP) through a local socket.
Each request and response is a JSON object in one line.

The socket name is "lys-remote-<user>-<label>" (in temporary directory on Linux/Mac, named pipe on Windows).
The label is given by --remote LABEL. If omitted, the process id is used, so that several lys can accept commands at the same time.

To accept commands from other computers, launch lys with --port option (e.g. python -m lys --remote expA --port 8765).
Then lys also accepts TCP connections on all network interfaces (or the address given by --host).
If --token is given, TCP clients should add "token" to every request. Note that the TCP connection is not encrypted.

Request::

    {"id": 1, "op": "exec", "code": "a = 1\\na + 1"}     # run code; the value of the last expression is returned
    {"id": 2, "op": "image", "target": "frontCanvas()", "dpi": 100}   # get png image of a canvas/figure/widget
    {"id": 3, "op": "list"}                                  # list variables in shell
    {"id": 4, "op": "info"}                                  # label, pid, home directory, port, protocol version
    {"id": 5, "op": "exec", "code": "1", "token": "secret"}  # TCP connection with --token

Response::

    {"id": 1, "ok": true, "result": "2", "stdout": "", "stderr": ""}
    {"id": 2, "ok": true, "image": "<base64 png>", "stdout": "", "stderr": ""}
    {"id": 3, "ok": false, "error": "Traceback ...", "stdout": "", "stderr": ""}

The client is provided by lys_mcp package.
When the protocol is changed, PROTOCOL should be incremented.
"""

import os
import io
import sys
import ast
import json
import types
import base64
import getpass
import tempfile
import traceback

from lys import glb
from qtpy import QtNetwork
from lys.Qt import QtCore

PROTOCOL = 1
_MAX_RESULT = 20000


def serverName(label):
    """
    Return the name of the local socket for *label*. The same rule is used in lys_mcp.

    Args:
        label(str): The label of the server.
    """
    name = "lys-remote-" + getpass.getuser() + "-" + label
    if sys.platform == "win32":
        return name
    return os.path.join(tempfile.gettempdir(), name)


class RemoteServer(QtCore.QObject):
    """
    Local socket (and optionally TCP) server that executes commands in :class:`lys.glb.shell.ExtendShell`.

    All commands are executed in the main thread through Qt event loop.

    Args:
        label(str): The label of the server. If None, the process id is used.
        port(int): The TCP port. If None, TCP connection is disabled.
        host(str): The address on which TCP server listens. Default is all network interfaces.
        token(str): If given, TCP clients should send it in every request.
    """

    def __init__(self, label=None, port=None, host="0.0.0.0", token=None, parent=None):
        super().__init__(parent)
        self._label = label or str(os.getpid())
        self._name = serverName(self._label)
        self._port = port
        self._host = host
        self._token = token
        self._buffers = {}
        self._tcpSockets = set()
        self._server = QtNetwork.QLocalServer(self)
        self._server.setSocketOptions(QtNetwork.QLocalServer.UserAccessOption)
        self._server.newConnection.connect(lambda: self._newConnection(self._server))
        self._tcp = None
        if port is not None:
            self._tcp = QtNetwork.QTcpServer(self)
            self._tcp.newConnection.connect(lambda: self._newConnection(self._tcp, tcp=True))

    def listen(self):
        res = self._listenLocal()
        if self._tcp is not None:
            res = self._listenTcp() or res
        return res

    def _listenLocal(self):
        if self._isRunning():
            print("lys remote: another lys is already listening with label", self._label, file=sys.stderr)
            return False
        QtNetwork.QLocalServer.removeServer(self._name)
        if not self._server.listen(self._name):
            print("lys remote: failed to listen on", self._name, ":", self._server.errorString(), file=sys.stderr)
            return False
        print("lys remote: listening with label", self._label, "(" + self._server.fullServerName() + ")")
        return True

    def _listenTcp(self):
        if not self._tcp.listen(QtNetwork.QHostAddress(self._host), self._port):
            print("lys remote: failed to listen on port", self._port, ":", self._tcp.errorString(), file=sys.stderr)
            return False
        if self._host in ("0.0.0.0", "::"):
            addresses = _localAddresses()
        else:
            addresses = [self._host]
        print("lys remote: listening on TCP port", self._port, "(" + ", ".join(a + ":" + str(self._port) for a in addresses) + ")")
        if self._token is None:
            print("lys remote: no token is set. Anyone in the network can execute commands in this lys.")
        return True

    def _isRunning(self):
        sock = QtNetwork.QLocalSocket()
        sock.connectToServer(self._name)
        res = sock.waitForConnected(500)
        sock.abort()
        return res

    def _newConnection(self, server, tcp=False):
        while server.hasPendingConnections():
            sock = server.nextPendingConnection()
            self._buffers[sock] = b""
            if tcp:
                self._tcpSockets.add(sock)
                print("lys remote: connected from", sock.peerAddress().toString())
            sock.readyRead.connect(lambda s=sock: self._read(s))
            sock.disconnected.connect(lambda s=sock: self._disconnected(s))

    def _disconnected(self, sock):
        self._buffers.pop(sock, None)
        self._tcpSockets.discard(sock)
        sock.deleteLater()

    def _read(self, sock):
        if sock not in self._buffers:
            return
        self._buffers[sock] += bytes(sock.readAll())
        while sock in self._buffers and b"\n" in self._buffers[sock]:
            line, self._buffers[sock] = self._buffers[sock].split(b"\n", 1)
            if line.strip():
                res = self._handle(line, tcp=sock in self._tcpSockets)
                sock.write(json.dumps(res).encode("utf-8") + b"\n")
                sock.flush()

    def _handle(self, line, tcp=False):
        try:
            req = json.loads(line.decode("utf-8"))
        except Exception:
            return {"ok": False, "error": "Invalid request: " + traceback.format_exc()}
        if tcp and self._token is not None and req.get("token") != self._token:
            return {"id": req.get("id"), "ok": False, "error": "Invalid token."}
        op = req.get("op", "exec")
        func = {"exec": self._exec, "image": self._image, "list": self._list, "info": self._info}.get(op)
        if func is None:
            return {"id": req.get("id"), "ok": False, "error": "Unknown op: " + str(op)}
        if op == "exec":
            print("[remote] >", req.get("code", "").replace("\n", "\n[remote]   "))
        with _Capture() as cap:
            try:
                res = func(req)
                res["ok"] = True
            except Exception:
                res = {"ok": False, "error": _formatException()}
        res["id"] = req.get("id")
        res["stdout"] = cap.stdout()
        res["stderr"] = cap.stderr()
        if res.get("result") is not None and op == "exec":
            print(res["result"])  # show result in lys log only
        return res

    def _exec(self, req):
        code = req.get("code", "")
        shell = glb.shell()
        body, last = _splitLastExpression(code)
        if body is not None:
            shell.exec(body, save=last is None)
        result = None
        if last is not None:
            result = shell.eval(last, save=body is None)
        return {"result": _repr(result)}

    def _image(self, req):
        target = req.get("target") or "frontCanvas()"
        obj = glb.shell().eval(target)
        if obj is None:
            raise ValueError(target + " is None. No canvas is found.")
        return {"image": base64.b64encode(_toPng(obj, dpi=req.get("dpi", 100))).decode("ascii")}

    def _info(self, req):
        from lys import home
        return {"label": self._label, "pid": os.getpid(), "home": os.path.abspath(home()), "port": self._port, "protocol": PROTOCOL}

    def _list(self, req):
        import lys
        res = {}
        for key, value in glb.shell().dict.items():
            if key.startswith("_") or getattr(lys, key, None) is value:  # private or imported by 'from lys import *'
                continue
            if isinstance(value, (type, types.ModuleType, types.FunctionType, types.BuiltinFunctionType)):
                continue
            res[key] = _summary(value)
        return {"result": json.dumps(res, ensure_ascii=False, indent=1)}


class _Capture:
    """Copy stdout/stderr to buffers while keeping the output to lys log."""

    class _Tee:
        def __init__(self, out):
            self.out = out
            self.buf = io.StringIO()

        def write(self, message):
            self.buf.write(message)
            if self.out is not None:
                self.out.write(message)

        def flush(self):
            if self.out is not None:
                self.out.flush()

    def __enter__(self):
        self._orig = sys.stdout, sys.stderr
        sys.stdout = self._out = self._Tee(sys.stdout)
        sys.stderr = self._err = self._Tee(sys.stderr)
        return self

    def __exit__(self, *args):
        sys.stdout, sys.stderr = self._orig

    def stdout(self):
        return self._out.buf.getvalue()

    def stderr(self):
        return self._err.buf.getvalue()


def _formatException():
    """Format exception without the frames of remote server and shell."""
    exc_type, exc, tb = sys.exc_info()
    if issubclass(exc_type, SyntaxError):
        return "".join(traceback.format_exception_only(exc_type, exc))
    skip = (os.path.abspath(__file__), os.path.abspath(sys.modules[type(glb.shell()).__module__].__file__))
    while tb is not None and os.path.abspath(tb.tb_frame.f_code.co_filename) in skip:
        tb = tb.tb_next
    return "".join(traceback.format_exception(exc_type, exc, tb))


def _localAddresses():
    """Return IPv4 addresses of this computer except for loopback."""
    res = []
    for a in QtNetwork.QNetworkInterface.allAddresses():
        if a.protocol() == QtNetwork.QAbstractSocket.IPv4Protocol and not a.isLoopback():
            res.append(a.toString())
    return res or ["0.0.0.0"]


def _splitLastExpression(code):
    """
    Split code into the body and the last expression, similar to Jupyter.

    Return:
        tuple: (body, last). Either of them may be None.
    """
    tree = ast.parse(code)
    if len(tree.body) == 0:
        return None, None
    if not isinstance(tree.body[-1], ast.Expr):
        return code, None
    lines = code.splitlines(keepends=True)
    last = tree.body[-1]
    if len(tree.body) == 1:
        return None, ast.get_source_segment(code, last)
    body = "".join(lines[:last.lineno - 1]) + lines[last.lineno - 1][:last.col_offset]
    return body, ast.get_source_segment(code, last)


def _repr(obj):
    if obj is None:
        return None
    try:
        txt = repr(obj)
    except Exception:
        txt = "<repr failed: " + type(obj).__name__ + ">"
    if len(txt) > _MAX_RESULT:
        txt = txt[:_MAX_RESULT] + "\n... (truncated, " + str(len(txt)) + " characters)"
    return txt


def _summary(obj):
    name = type(obj).__name__
    for attr in ["shape", "dtype"]:
        if hasattr(obj, attr):
            try:
                name += " " + attr + "=" + str(getattr(obj, attr))
            except Exception:
                pass
    return name


def _toPng(obj, dpi=100):
    """Convert canvas, matplotlib figure, or QWidget to png."""
    from matplotlib.figure import Figure
    if hasattr(obj, "getFigure"):
        obj = obj.getFigure()
    elif hasattr(obj, "canvas") and hasattr(obj.canvas, "getFigure"):  # Graph window
        obj = obj.canvas.getFigure()
    if isinstance(obj, Figure):
        buf = io.BytesIO()
        obj.savefig(buf, format="png", dpi=dpi, facecolor="white")
        return buf.getvalue()
    if hasattr(obj, "canvas") and hasattr(obj.canvas, "grab"):  # Graph3D, pyqtgraph Graph
        obj = obj.canvas
    if hasattr(obj, "grab"):
        ba = QtCore.QByteArray()
        buf = QtCore.QBuffer(ba)
        buf.open(QtCore.QIODevice.WriteOnly)
        obj.grab().save(buf, "PNG")
        buf.close()
        return bytes(ba)
    raise TypeError("Cannot convert " + type(obj).__name__ + " to image.")


_server = None


def start(label=None, port=None, host="0.0.0.0", token=None):
    """
    Start remote server.

    Args:
        label(str): The label of the server, which is used by clients to select lys. If None, the process id is used.
        port(int): The TCP port to accept connections from other computers. If None, only local connections are accepted.
        host(str): The address on which TCP server listens. Default is all network interfaces.
        token(str): If given, TCP clients should send it in every request.
    """
    global _server
    if _server is None:
        _server = RemoteServer(label, port=port, host=host, token=token)
        if not _server.listen():
            _server = None
    return _server
