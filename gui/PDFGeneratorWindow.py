import logging

from pdf.PDFGenerator import PDFGenerator

from PyQt5.QtWidgets import *
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QSize, Qt
import qtawesome as qta


class PDFGeneratorWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.main_layout = QVBoxLayout()
        self.main_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.labels = []

        self.setup_buttons('Select template file', self.template_file_dialog, qta.icon('mdi6.microsoft-word'))
        self.setup_buttons('Select Excel sheet file', self.excel_file_dialog, qta.icon('mdi.microsoft-excel'))
        self.setup_buttons('Select output folder', self.output_path_dialog, qta.icon('fa.folder-open'))

        self.is_delete_docx = QCheckBox('Delete source .docx after?')
        self.is_delete_docx.setChecked(True)
        self.main_layout.addWidget(self.is_delete_docx)

        self.generate_button = None
        self.setup_generate_button()

        self.setLayout(self.main_layout)

    def setup_buttons(self, btn_text, btn_action, btn_icon):
        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignLeft)
        self.generate_button = QPushButton(btn_icon, btn_text)
        self.generate_button.clicked.connect(btn_action)
        self.generate_button.setFont(QFont('MS Shell Dlg', 12))
        self.generate_button.setFixedSize(250, 40)
        self.generate_button.setIconSize(QSize(35, 35))
        label = QLabel()
        label.setMaximumHeight(40)
        layout.addWidget(self.generate_button)
        layout.addWidget(label)
        self.main_layout.addLayout(layout)
        self.labels.append(label)

    def setup_generate_button(self):
        button = QPushButton(qta.icon('msc.file-pdf'), 'Generate PDFs')
        button.clicked.connect(self.generate_pdfs)
        button.setFont(QFont('MS Shell Dlg', 12))
        button.setFixedSize(250, 40)
        button.setIconSize(QSize(35, 35))
        self.main_layout.addWidget(button)

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

    def generate_pdfs(self):
        logging.info('Generating PDFs')

        template_file_name = self.labels[0].text()
        excel_file_name = self.labels[1].text()
        output_path = self.labels[2].text()
        delete_source_docx = self.is_delete_docx.isChecked()

        try:
            generator = PDFGenerator(template_file_name=template_file_name, excel_file_name=excel_file_name,
                                     output_path=output_path, delete_source_docx=delete_source_docx)
            generator.parse_excel_file()
            generator.replace_parameters()
            generator.convert_docx_to_pdf_thread()
        except ValueError as e:
            logging.warning(e)