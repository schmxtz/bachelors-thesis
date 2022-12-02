import sys, logging
from gui.PDFGeneratorWindow import PDFGeneratorWindow
from gui.PDFSignerWindow import PDFSignerWindow
from gui.Logger import Handler

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QPushButton, QHBoxLayout, QApplication, QPlainTextEdit
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QFont
import qtawesome as qta


WINDOW_SIZE = (1200, 1000)
VERSION = 'v0.1'
NAME = 'GenSig'


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('{0} {1}'.format(NAME, VERSION))
        self.setGeometry(0, 0, WINDOW_SIZE[0], WINDOW_SIZE[1])

        main_layout = QVBoxLayout()

        handler = Handler(self)
        log_text_box = QPlainTextEdit(self)
        log_text_box.setFixedSize(1180, 300)
        logging.getLogger().addHandler(handler)
        logging.getLogger().setLevel(logging.INFO)
        handler.new_record.connect(log_text_box.appendPlainText)

        self.stacked_widget = QStackedWidget()
        self.stacked_widget.insertWidget(0, PDFGeneratorWindow())
        self.stacked_widget.insertWidget(1, PDFSignerWindow())
        self.stacked_widget.insertWidget(2, QWidget())
        self.stacked_widget.setCurrentIndex(2)

        generator_icon = qta.icon('msc.file-pdf')
        button_generator = QPushButton(generator_icon, 'PDF Generation')
        button_generator.setFont(QFont('MS Shell Dlg', 16))
        button_generator.setFixedSize(575, 70)
        button_generator.setIconSize(QSize(60, 50))
        button_generator.clicked.connect(self.show_generator_widget)

        sign_icon = qta.icon('msc.file', 'msc.edit', options=[{}, {'scale_factor': 0.6, 'offset': (0.0, 0.1)}])
        button_sign = QPushButton(sign_icon, 'PDF Signing')
        button_sign.setFont(QFont('MS Shell Dlg', 16))
        button_sign.setFixedSize(575, 70)
        button_sign.setIconSize(QSize(60, 50))
        button_sign.clicked.connect(self.show_sign_widget)

        button_layout = QHBoxLayout()
        button_layout.addWidget(button_generator)
        button_layout.addWidget(button_sign)

        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.stacked_widget)
        main_layout.addWidget(log_text_box)

        self.setLayout(main_layout)

    def show_generator_widget(self):
        self.stacked_widget.setCurrentIndex(0)

    def show_sign_widget(self):
        self.stacked_widget.setCurrentIndex(1)


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    ex = MainWindow()
    ex.show()
    sys.exit(app.exec())
