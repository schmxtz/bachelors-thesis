from utils.Files import parse_excel_file
import time, pikepdf
from pikepdf import Pdf


class PDFGenerator:
    def __init__(self, template_file_name: str, excel_file_name: str, output_path: str):
        parameters = parse_excel_file(excel_file_name)

        for parameter in parameters[0:1]:
            output_filename = self.build_file_name(parameter=parameter)
            document = Pdf.open(filename_or_stream=template_file_name, allow_overwriting_input=False)
            unicode_map = document.pages[0].resources['/Font']['/F1']['/ToUnicode']
            unicode_map_parsed = pikepdf.parse_content_stream(unicode_map)[11].operands
            content = document.pages[0].obj.Contents[0]
            content_parsed = pikepdf.parse_content_stream(content)
            operands = content_parsed[43].operands
            operand = operands.pop(0)
            for i in range(len(operand)):
                if isinstance(operand[i], pikepdf.String):
                    print(operand[i].unparse())
                    operand[i] = pikepdf.String(b'\0t')
                    print(operand[i].unparse())
            operands.insert(0, operand)
            print(operands)
            # for operand in content_parsed[43].operands:
            #     for t in operand:
            #         if isinstance(t, pikepdf.String):
            #             t = pikepdf.String(b'<0074>')
            #     print(operand.unparse())
            content = document.pages[0].obj.Contents[0] = document.make_stream(pikepdf.unparse_content_stream(content_parsed))
            document.save('etsesfsef.pdf')
            # print(content_parsed[43].operands)
            # for operands, operator in pikepdf.parse_content_stream(document.pages[0]):
            #     # for operand in operands:
            #     #     if isinstance(operand, pikepdf.Array):
            #     #         print(operand)
            #     print(operands)




    @staticmethod
    def build_file_name(parameter):
        return '{last_name}_{first_name}_{module}_{time}.pdf'.format(
            last_name=parameter['Nachname'],
            first_name=parameter['Vorname'],
            module=parameter['Modul'],
            time=time.time_ns())


pdf = PDFGenerator('zertifikat.pdf', 'Empfaenger.xlsx', '.')

parse_excel_file(file_name='Empfaenger.xlsx')
