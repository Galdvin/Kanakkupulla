"""
Theme & Palette Manager:
Implements CameronBrooks11/pyside6-gui-template theme architecture using Qt's Fusion engine and QPalette.
"""
from PySide6.QtCore import QSettings
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QPushButton

SYSTEM = "System"
LIGHT = "Light"
DARK = "Dark"
THEMES = (SYSTEM, LIGHT, DARK)

_ACCENT_TEAL = QColor(20, 184, 166) # #14b8a6 Vibrant Fintech Teal
_ACCENT_DARK = QColor(13, 148, 136) # #0d9488 Deep Teal

def _palette(
    window: QColor, base: QColor, alternate: QColor, button: QColor, text: QColor, disabled: QColor, accent: QColor
) -> QPalette:
    palette = QPalette(button, window)
    role = QPalette.ColorRole
    colours = {
        role.WindowText: text,
        role.Text: text,
        role.ButtonText: text,
        role.ToolTipText: text,
        role.Base: base,
        role.ToolTipBase: base,
        role.AlternateBase: alternate,
        role.PlaceholderText: disabled,
        role.Highlight: accent,
        role.HighlightedText: QColor("white"),
        role.Link: accent,
    }
    for colour_role, colour in colours.items():
        palette.setColor(colour_role, colour)
    for colour_role in (role.WindowText, role.Text, role.ButtonText):
        palette.setColor(QPalette.ColorGroup.Disabled, colour_role, disabled)
    return palette

def dark_palette() -> QPalette:
    return _palette(
        window=QColor(10, 15, 29),       # #0a0f1d Deep Navy
        base=QColor(13, 19, 34),         # #0d1322 Dark Surface
        alternate=QColor(30, 41, 59),    # #1e293b Card / Hover surface
        button=QColor(30, 41, 59),       # #1e293b
        text=QColor(241, 245, 249),      # #f1f5f9 Crisp White
        disabled=QColor(100, 116, 139),  # #64748b Muted Slate
        accent=_ACCENT_TEAL,
    )

def light_palette() -> QPalette:
    return _palette(
        window=QColor(248, 250, 252),    # #f8fafc Clean Light Slate
        base=QColor(255, 255, 255),      # #ffffff Pure White
        alternate=QColor(241, 245, 249), # #f1f5f9
        button=QColor(241, 245, 249),
        text=QColor(15, 23, 42),         # #0f172a Deep Slate Text
        disabled=QColor(148, 163, 184),
        accent=QColor(2, 132, 199),      # #0284c7 Sky Blue
    )

def apply_app_theme(name: str = DARK) -> None:
    """Applies theme palette and Fusion style to the whole application."""
    app = QApplication.instance()
    if not app:
        return
    app.setStyle("Fusion")
    if name == LIGHT:
        app.setPalette(light_palette())
    else:
        app.setPalette(dark_palette())

def get_saved_theme() -> str:
    name = QSettings().value("theme", DARK)
    return name if name in THEMES else DARK

def save_app_theme(name: str) -> None:
    QSettings().setValue("theme", name)
