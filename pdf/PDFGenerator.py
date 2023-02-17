import logging
import os
import subprocess
import time
from threading import Thread

from docx import Document

from utils.Files import parse_excel_file, PLACEHOLDER_CLOSING, PLACEHOLDER_OPENING

DOCX_EXT = '.docx'
EXCEL_EXT = '.xlsx'


class PDFGenerator:
    def __init__(self, template_file_name: str, excel_file_name: str, output_path: str,
                 delete_source_docx: bool = True):
        """
        Initializes attributes and checks their validity

        :param template_file_name: Path to the template file
        :param excel_file_name: Path to the excel file
        :param output_path: Path to the folder to place the output files into
        :param delete_source_docx: Boolean indicating whether to delete the source .docx files afterwards
        """
        if not template_file_name.endswith(DOCX_EXT):
            raise ValueError('Template file must be {} format.'.format(DOCX_EXT))
        self.template_file_name = template_file_name

        if not excel_file_name.endswith(EXCEL_EXT):
            raise ValueError('Excel sheet file must be {} format.'.format(EXCEL_EXT))
        self.excel_file_name = excel_file_name

        if not os.path.isdir(output_path):
            raise ValueError('Output path must be a directory.')
        self.output_path = output_path

        self.delete_source_docx = delete_source_docx
        self.parameters = None
        self.header = None

    def parse_excel_file(self):
        """
        Parses the excel file.

        :return:
        """
        logging.info('Parsing excel file: {0}'.format(self.excel_file_name))
        self.parameters, self.header = parse_excel_file(self.excel_file_name)
        logging.info('Finished parsing excel file: {0}'.format(self.excel_file_name))

    def replace_parameters(self):
        """
        Iterates through the word document and replaces the placeholders with the given values in parameters.

        :return:
        """
        logging.info('Creating word files... (0/{0})'.format(len(self.parameters)))
        if self.parameters is None or self.header is None:
            return
        ctr = 1
        len_params = len(self.parameters)
        for parameter in self.parameters:
            logging.info('Creating word files... ({0}/{1})'.format(ctr, len_params))
            template = Document(self.template_file_name)
            file_name = self.build_file_name(parameter)
            for paragraph in template.paragraphs:
                self.replace_text_in_paragraph(paragraph, parameter)

            for table in template.tables:
                for col in table.columns:
                    for cell in col.cells:
                        for paragraph in cell.paragraphs:
                            self.replace_text_in_paragraph(paragraph, parameter)
            template.save(self.output_path + '/' + file_name)
            ctr += 1
        logging.info('Finished creating word files')

    def convert_docx_to_pdf(self):
        """
        Function that calls the Visual-Basic-script that converts the Word files to pdf files.

        :return:
        """
        current_wcd = os.getcwd()
        current_wcd = current_wcd.replace('\\', '/')
        command = 'wscript {0}/pdf/DocxToPdf.vbs {1} {2}'.format(current_wcd,
                                                                 self.output_path,
                                                                 int(self.delete_source_docx))
        subprocess.call(command)
        logging.info('Finished converting PDFs')

    def convert_docx_to_pdf_thread(self):
        """
        Function that calls our word-to-pdf conversion function in a thread so that it doesn't block the UI.

        :return:
        """

        Thread(target=self.convert_docx_to_pdf).start()

    @staticmethod
    def replace_text_in_paragraph(paragraph, parameter):
        """
        This is the actual function that replaces the placeholders, deletes them or sets their text to an empty string.
        Depending on the layout of the template file, the logic in this function might have to be altered. As of now the
        text of the original placeholders is set to an empty string. If a name in the numbered lists (Inhalt_01,
        Inhalt_02, ...) is very long and causes a linebreak, it is possible that this shifts the following lines
        underneath which leads to the creation of a second page, which is not desirable. To counter this, there is a
        function called delete_paragraph, but we don't use it as of now.

        :param paragraph: The paragraph that is to be checked for placeholders.
        :param parameter: Parameters containing a dictionary of key-value with placeholder-name: placeholder-value
        :return:
        """
        line = paragraph.runs
        for word in line:
            if PLACEHOLDER_OPENING in word.text and PLACEHOLDER_CLOSING in word.text:
                if word.text in parameter:
                    value = parameter.get(word.text)
                    if value is None:
                        value = ''
                    word.text = word.text.replace(word.text, value)
                else:
                    word.text = word.text.replace(word.text, '')

    @staticmethod
    def delete_paragraph(paragraph):
        """
        Deletes the given paragraph

        :param paragraph: Paragraph which is to be deleted
        :return:
        """
        p = paragraph._element
        p.getparent().remove(p)
        paragraph._p = paragraph._element = None

    @staticmethod
    def build_file_name(parameter):
        """
        Builds file name with given parameter list.
        :param parameter: Parameters containing a dictionary of key-value with placeholder-name: placeholder-value
        :return: Returns a file name including last name, first name, module name and a timestamp.
        """

        return '{last_name}_{first_name}_{module}_{time}.docx'.format(
            last_name=parameter[PLACEHOLDER_OPENING + 'Nachname' + PLACEHOLDER_CLOSING],
            first_name=parameter[PLACEHOLDER_OPENING + 'Vorname' + PLACEHOLDER_CLOSING],
            module=parameter[PLACEHOLDER_OPENING + 'Modul' + PLACEHOLDER_CLOSING],
            time=time.time_ns())
