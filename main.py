"""
Kanakkupulla Application Entry Point
"""
import sys
import logging
from PySide6.QtWidgets import QApplication
from config.settings import LOGS_DIR, APP_NAME
from database.seed import seed_database
from ui.login_dialog import LoginDialog
from ui.main_window import MainWindow

# Setup logging
logging.basicConfig(
    filename=LOGS_DIR / "app.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("Kanakkupulla")

def main():
    logger.info("Starting %s application", APP_NAME)
    
    # 1. Initialize and seed DB if needed
    try:
        seed_database()
        logger.info("Database initialized and verified.")
    except Exception as e:
        logger.error("Failed to initialize database: %s", str(e), exc_info=True)

    # 2. Launch Qt Application
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)

    # 3. Present Login Dialog
    login_dialog = LoginDialog()
    authenticated_user = None

    def on_login_success(user):
        nonlocal authenticated_user
        authenticated_user = user

    login_dialog.login_success.connect(on_login_success)

    if login_dialog.exec():
        if authenticated_user:
            logger.info("User %s authenticated successfully", authenticated_user.username)
            main_window = MainWindow(user=authenticated_user)
            main_window.show()
            sys.exit(app.exec())
        else:
            sys.exit(0)
    else:
        logger.info("Login canceled or closed by user.")
        sys.exit(0)

if __name__ == "__main__":
    main()
