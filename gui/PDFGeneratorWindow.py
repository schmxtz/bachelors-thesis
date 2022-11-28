from PyQt5.QtWidgets import *
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QSize
import qtawesome as qta


class PDFGeneratorWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.main_layout = QVBoxLayout()
        self.labels = []

        self.setup_buttons('Select template file', self.template_file_dialog, qta.icon('mdi6.microsoft-word'))
        self.setup_buttons('Select Excel sheet file', self.excel_file_dialog, qta.icon('mdi.microsoft-excel'))
        self.setup_buttons('Select output folder', self.output_path_dialog, qta.icon('fa.folder-open'))

        self.setLayout(self.main_layout)

    def setup_buttons(self, btn_text, btn_action, btn_icon):
        layout = QHBoxLayout()
        button = QPushButton(btn_icon, btn_text)
        button.clicked.connect(btn_action)
        button.setFont(QFont('MS Shell Dlg', 12))
        button.setFixedSize(250, 40)
        button.setIconSize(QSize(35, 35))
        label = QLabel()
        label.setFixedSize(250, 40)
        layout.addWidget(button)
        layout.addWidget(label)
        self.main_layout.addLayout(layout)
        self.labels.append(label)

    def template_file_dialog(self):
        file_name = QFileDialog.getOpenFileName(parent=self,
                                                caption='Select template file',
                                                directory='',
                                                filter='All Files (*);;DOCX Files (*.docx)',
                                                initialFilter='DOCX Files (*.docx)')
        if file_name[0]:
            self.labels[0].setText(file_name[0])

    def excel_file_dialog(self):
        file_name = QFileDialog.getOpenFileName(parent=self,
                                                caption='Select excel sheet file',
                                                directory='',
                                                filter='All Files (*);;Excel Files (*.xlsx)',
                                                initialFilter='Excel Files (*.xlsx)')
        if file_name[0]:
            self.labels[1].setText(file_name[0])

    def output_path_dialog(self):
        folder_name = QFileDialog.getExistingDirectory(self, 'Select output folder')
        if folder_name:
            self.labels[2].setText(folder_name)
