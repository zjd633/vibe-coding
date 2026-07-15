from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QGuiApplication, QPalette
from PySide6.QtWidgets import QApplication


def configure_application(app: QApplication) -> None:
    app.setFont(QFont("Segoe UI", 10))
    app.setStyle("Fusion")
    _apply_palette(app)
    app.setStyleSheet(
        """
        QLineEdit, QComboBox { min-height: 32px; padding: 2px 8px; }
        QPushButton { min-height: 32px; padding: 2px 14px; }
        QCheckBox { min-height: 28px; }
        QScrollArea { background: transparent; }
        """
    )
    if not app.property("replykeyThemeConnected"):
        QGuiApplication.styleHints().colorSchemeChanged.connect(
            lambda _scheme: _apply_palette(app)
        )
        app.setProperty("replykeyThemeConnected", True)


def _apply_palette(app: QApplication) -> None:
    dark = QGuiApplication.styleHints().colorScheme() == Qt.ColorScheme.Dark
    palette = QPalette()
    if dark:
        colors = {
            QPalette.ColorRole.Window: "#202124",
            QPalette.ColorRole.WindowText: "#f2f3f5",
            QPalette.ColorRole.Base: "#17181a",
            QPalette.ColorRole.AlternateBase: "#26282c",
            QPalette.ColorRole.ToolTipBase: "#2b2d31",
            QPalette.ColorRole.ToolTipText: "#f2f3f5",
            QPalette.ColorRole.Text: "#f2f3f5",
            QPalette.ColorRole.Button: "#2b2d31",
            QPalette.ColorRole.ButtonText: "#f2f3f5",
            QPalette.ColorRole.Highlight: "#5b8def",
            QPalette.ColorRole.HighlightedText: "#ffffff",
            QPalette.ColorRole.PlaceholderText: "#a9adb5",
        }
    else:
        colors = {
            QPalette.ColorRole.Window: "#f6f7f9",
            QPalette.ColorRole.WindowText: "#1e2329",
            QPalette.ColorRole.Base: "#ffffff",
            QPalette.ColorRole.AlternateBase: "#eef1f5",
            QPalette.ColorRole.ToolTipBase: "#ffffff",
            QPalette.ColorRole.ToolTipText: "#1e2329",
            QPalette.ColorRole.Text: "#1e2329",
            QPalette.ColorRole.Button: "#ffffff",
            QPalette.ColorRole.ButtonText: "#1e2329",
            QPalette.ColorRole.Highlight: "#2b6de5",
            QPalette.ColorRole.HighlightedText: "#ffffff",
            QPalette.ColorRole.PlaceholderText: "#68707d",
        }
    for role, color in colors.items():
        palette.setColor(role, QColor(color))
    palette.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.Text,
        QColor("#737983" if dark else "#8a919d"),
    )
    palette.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.ButtonText,
        QColor("#737983" if dark else "#8a919d"),
    )
    app.setPalette(palette)

