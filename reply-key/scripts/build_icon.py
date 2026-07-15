from __future__ import annotations

import os
from pathlib import Path
import struct
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QByteArray, QBuffer, QIODevice, QRectF
from PySide6.QtGui import QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer


def render_png(renderer: QSvgRenderer, size: int) -> bytes:
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(0)
    painter = QPainter(image)
    renderer.render(painter, QRectF(0, 0, size, size))
    painter.end()
    payload = QByteArray()
    buffer = QBuffer(payload)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    if not image.save(buffer, "PNG"):
        raise RuntimeError(f"Unable to render {size}px icon")
    buffer.close()
    return bytes(payload)


def build_icon(source: Path, destination: Path) -> None:
    app = QGuiApplication.instance() or QGuiApplication([])
    renderer = QSvgRenderer(str(source))
    if not renderer.isValid():
        raise RuntimeError(f"Invalid SVG: {source}")
    images = [(size, render_png(renderer, size)) for size in (16, 24, 32, 48, 64, 128, 256)]
    header_size = 6 + 16 * len(images)
    entries = []
    payloads = []
    offset = header_size
    for size, payload in images:
        dimension = 0 if size == 256 else size
        entries.append(
            struct.pack(
                "<BBBBHHII",
                dimension,
                dimension,
                0,
                0,
                1,
                32,
                len(payload),
                offset,
            )
        )
        payloads.append(payload)
        offset += len(payload)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(
        struct.pack("<HHH", 0, 1, len(images)) + b"".join(entries) + b"".join(payloads)
    )
    app.processEvents()


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[1]
    target = project_root / "assets" / "replykey.ico"
    build_icon(project_root / "assets" / "replykey.svg", target)
    print(target)

