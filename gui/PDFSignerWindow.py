from PyQt5.QtWidgets import *


class PDFSignerWindow(QWidget):
    def __init__(self):
        super().__init__()
        main_layout = QVBoxLayout()

        main_layout.addWidget(QLabel("Test Signer"))

        self.setLayout(main_layout)
