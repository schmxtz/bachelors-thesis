import logging

from crypto.Signer import Signer

from PyQt5.QtWidgets import *
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QSize, Qt
import qtawesome as qta


class PDFSignerWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.main_layout = QVBoxLayout()
        self.main_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.labels = []

        self.setup_buttons('Select signing certificate', self.signing_cert_dialog, qta.icon('mdi6.certificate'))
        self.setup_buttons('Select PDF files to be signed', self.pdf_files_dialog, qta.icon('fa.file-pdf-o'))
        self.pw_box = QLineEdit()
        self.pw_box.setEchoMode(QLineEdit.Password)
        self.pw_box.setPlaceholderText('Certificate passphrase')
        self.pw_box.setFixedSize(250, 40)
        self.main_layout.addWidget(self.pw_box)
        self.in_place = QCheckBox('Sign in place (replaces original PDF)')
        self.in_place.setChecked(True)
        self.main_layout.addWidget(self.in_place)
        self.list_widget = QListWidget()
        self.list_widget.setFixedSize(500, 200)
        self.main_layout.addWidget(self.list_widget)

        self.sign_button = None
        self.setup_sign_button()
        self.pdf_file_names = None

        self.setLayout(self.main_layout)

    def setup_buttons(self, btn_text, btn_action, btn_icon):
        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignLeft)
        self.sign_button = QPushButton(btn_icon, btn_text)
        self.sign_button.clicked.connect(btn_action)
        self.sign_button.setFont(QFont('MS Shell Dlg', 12))
        self.sign_button.setFixedSize(250, 40)
        self.sign_button.setIconSize(QSize(35, 35))
        label = QLabel()
        label.setMaximumHeight(40)
        layout.addWidget(self.sign_button)
        layout.addWidget(label)
        self.main_layout.addLayout(layout)
        self.labels.append(label)

    def setup_sign_button(self):
        button = QPushButton(qta.icon('msc.file-pdf'), 'Sign PDFs')
        button.clicked.connect(self.sign_pdfs)
        button.setFont(QFont('MS Shell Dlg', 12))
        button.setFixedSize(250, 40)
        button.setIconSize(QSize(35, 35))
        self.main_layout.addWidget(button)

    def signing_cert_dialog(self):
        file_name = QFileDialog.getOpenFileName(parent=self,
                                                caption='Select signing certificate',
                                                directory='',
                                                filter='PKCS12 keystore (*.p12 *.pfx)',
                                                initialFilter='PKCS12 keystore (*.p12 *.pfx)')
        if file_name[0]:
            self.labels[0].setText(file_name[0])

    def pdf_files_dialog(self):
        file_names = QFileDialog.getOpenFileNames(parent=self,
                                                  caption='Select PDF files to be signed',
                                                  directory='',
                                                  filter='PDF Files (*.pdf)',
                                                  initialFilter='PDF Files (*.pdf)')
        for file_name in file_names[0]:
            self.list_widget.addItem(file_name)
        self.pdf_file_names = file_names[0]

    def sign_pdfs(self):
        logging.info('Signing PDFs')

        try:
            signer = Signer(pdf_file_names=self.pdf_file_names,
                            passphrase=self.pw_box.text(),
                            pkcs12_file_name=self.labels[0].text(),
                            in_place=self.in_place.isChecked())
        except ValueError as e:
            logging.warning(e)




