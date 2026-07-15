from __future__ import annotations

from PySide6.QtCore import QObject, Signal
from PySide6.QtNetwork import QLocalServer, QLocalSocket


class SingleInstanceGuard(QObject):
    activation_requested = Signal()

    def __init__(self, server_name: str = "ReplyKey-Desktop-SingleInstance") -> None:
        super().__init__()
        self.server_name = server_name
        self._server: QLocalServer | None = None
        self.is_primary = False

    def acquire(self) -> bool:
        if self.is_primary:
            return True
        probe = QLocalSocket()
        probe.connectToServer(self.server_name)
        if probe.waitForConnected(250):
            probe.abort()
            return False
        probe.abort()

        QLocalServer.removeServer(self.server_name)
        server = QLocalServer(self)
        server.newConnection.connect(self._accept_connections)
        if not server.listen(self.server_name):
            return False
        self._server = server
        self.is_primary = True
        return True

    def _accept_connections(self) -> None:
        if self._server is None:
            return
        while self._server.hasPendingConnections():
            socket = self._server.nextPendingConnection()
            if socket is None:
                continue
            self.activation_requested.emit()
            socket.setParent(self)
            socket.abort()

    def close(self) -> None:
        if self._server is not None:
            self._server.close()
        if self.is_primary:
            QLocalServer.removeServer(self.server_name)
        self.is_primary = False
