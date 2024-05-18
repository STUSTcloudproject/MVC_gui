import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPlainTextEdit, QVBoxLayout, QWidget


class TerminalWidget(QWidget):
    def __init__(self, welcome_message="Welcome", font_size=12, background_color="#000000", parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout()
        self.console = QPlainTextEdit()
        self.console.setReadOnly(True)
        self.console.setStyleSheet(f"""
            background-color: {background_color};
            color: #FFFFFF;
            font-family: 'Consolas', 'Courier New', 'Lucida Console', monospace;
            font-size: {font_size}px;
            border: none;
        """)

        self.welcome_message = welcome_message

        self.layout.addWidget(self.console)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(self.layout)
        self.setStyleSheet(f"background-color: {background_color};")

        # Initial welcome message
        self.post_message("System", self.welcome_message)

    def post_message(self, sender, message):
        formatted_message = f"[{sender}] {message}"
        self.console.appendPlainText(formatted_message)


class MainWindow(QMainWindow):
    def __init__(self, font_size=12, background_color="#000000"):
        super().__init__()

        self.setWindowTitle("PyQt5 Terminal Simulation")
        self.setGeometry(100, 100, 600, 400)

        self.terminal_widget = TerminalWidget(font_size=font_size, background_color=background_color)
        self.setCentralWidget(self.terminal_widget)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow(font_size=14, background_color="#1e1e1e")
    main_window.show()

    # Example usage
    main_window.terminal_widget.post_message("System", "This is a test message.")
    main_window.terminal_widget.post_message("User", "Hello, this is a user message.")

    sys.exit(app.exec_())
