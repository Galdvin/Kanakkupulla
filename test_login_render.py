import sys, os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont

app = QApplication.instance() or QApplication(sys.argv)
app.setFont(QFont("Segoe UI", 9))

from assets.styles.theme import DARK_THEME
app.setStyleSheet(DARK_THEME)

from ui.login_dialog import LoginDialog

dlg = LoginDialog()
dlg.show()
app.processEvents()

pix = dlg.grab()
pix.save("scratch_login_preview.png")
print("Saved scratch_login_preview.png successfully")
