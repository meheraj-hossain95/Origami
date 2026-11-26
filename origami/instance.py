"""One Origami per user and data folder: a second launch brings the running window forward instead.

Two copies would both run the reminder service, so every reminder would arrive twice.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from pathlib import Path

from PySide6.QtNetwork import QLocalServer, QLocalSocket

WAIT_MS = 500
SHOW = b"show"


def server_name(data_dir: Path) -> str:
    digest = hashlib.sha256(str(data_dir).lower().encode()).hexdigest()[:16]
    return f"origami-{digest}"


def notify_running(name: str) -> bool:
    """Ask a running instance to show itself. True if one answered."""
    socket = QLocalSocket()
    socket.connectToServer(name)
    if not socket.waitForConnected(WAIT_MS):
        return False
    socket.write(SHOW)
    socket.waitForBytesWritten(WAIT_MS)
    socket.disconnectFromServer()
    return True


def listen(name: str, on_show: Callable[[], None]) -> QLocalServer:
    server = QLocalServer()
    server.setSocketOptions(QLocalServer.SocketOption.UserAccessOption)  # only this user may connect
    if not server.listen(name):
        QLocalServer.removeServer(name)  # a crashed instance can leave its socket behind (Unix)
        server.listen(name)

    def accept() -> None:
        while (socket := server.nextPendingConnection()) is not None:

            def read(s: QLocalSocket = socket) -> None:
                if bytes(s.readAll().data()).startswith(SHOW):
                    on_show()
                s.disconnectFromServer()

            socket.readyRead.connect(read)
            socket.disconnected.connect(socket.deleteLater)

    server.newConnection.connect(accept)
    return server
