from utils.Files import parse_excel_file
import time, pikepdf, itertools
from pikepdf import Pdf

DEKAN_NAME = 'Prof. Dr. rer. nat. Heinz Schmitz'
LEITER_NAME = 'Prof. Dr. sc. nat. Konstantin Knorr'
CMAP_PARSE_ERROR = 'Placeholder strings inside the template PDF cannot be replaced.'

FONT_NAME = '/CIDFont+F1'

BT_OP = pikepdf.Operator('BT')
ET_OP = pikepdf.Operator('ET')
TJ_OP = pikepdf.Operator('TJ')
BEGINBFCHAR_OP = pikepdf.Operator('beginbfchar')


class PDFGenerator:
    def __init__(self, template_file_name: str, excel_file_name: str, output_path: str):
        self.parameters, self.header = parse_excel_file(excel_file_name)
        self.document = Pdf.open(filename_or_stream=template_file_name, allow_overwriting_input=False)
        self.mapping = GlypthToUnicodeMapping()

        """
        PDF renders strings by printing them character by character. In a PDF these are called glyphs and there exists 
        in most cases a /ToUnicode entry. This entry should map all glyphs in the template_file to corresponding unicode
        characters. So in order to find and replace whole strings we to parse the mapping. 
        """
        self.parse_glyph_unicode_mapping()
        self.positions = self.parse_placeholder_positions()
        print(self.positions)

        # Now that we have the glyph to unicode mapping we can start looking for the placeholder strings

        # for parameter in self.parameters[0:1]:
        #     self.output_filename = self.build_file_name(parameter=parameter)
        #     content = self.document.pages[0].obj.Contents[0]
        #     content_parsed = pikepdf.parse_content_stream(content)
        #
        #     operands = content_parsed[43].operands
        #     operand = operands.pop(0)
        #     for i in range(len(operand)):
        #         if isinstance(operand[i], pikepdf.String):
        #             print(operand[i].unparse())
        #             operand[i] = pikepdf.String(b'\0t')
        #             print(operand[i].unparse())
        #     operands.insert(0, operand)
        #     print(operands)
        #     for operand in content_parsed[43].operands:
        #         for t in operand:
        #             if isinstance(t, pikepdf.String):
        #                 t = pikepdf.String(b'<0074>')
        #         print(operand.unparse())
        #     content = document.pages[0].obj.Contents[0] = document.make_stream(pikepdf.unparse_content_stream(content_parsed))
        #     document.save('etsesfsef.pdf')
        #     print(content_parsed[43].operands)
        #     for operands, operator in pikepdf.parse_content_stream(document.pages[0]):
        #         # for operand in operands:
        #         #     if isinstance(operand, pikepdf.Array):
        #         #         print(operand)
        #         print(operands)

    def parse_glyph_unicode_mapping(self):
        # Each pages' resources reference the same fonts, thus we can just take the first
        font_list = self.document.pages[0]['/Resources']['/Font']

        target_font = None
        # Loop through available fonts and find arial font (/CIDFont+F1)
        for font in font_list:
            if font_list[font]['/BaseFont'] == FONT_NAME:
                target_font = font_list[font]
                break

        if target_font is None or target_font.get('/ToUnicode') is None:
            raise ValueError('Font used in template not available.')

        # /ToUnicode entry is a stream object, so we need to parse it
        resource_parsed = pikepdf.parse_content_stream(target_font['/ToUnicode'])

        # Mapping is surrounded by <length> beginbfchar <glyph> <unicode> ... endbfchar
        mapping_indices = []
        mapping_obj = None
        for i in range(len(resource_parsed)):
            if resource_parsed[i].operator == BEGINBFCHAR_OP:
                mapping_indices.append(i + 1)

        # Mapping dict lengths are limited to 100, so there might be more, so we collect them all in one list
        mapping_obj = list(itertools.chain.from_iterable(
            [resource_parsed[indices].operands for indices in mapping_indices]
        ))

        # Contains list of <glyph> <unicode> pairs
        if len(mapping_obj) % 2 != 0:
            raise ValueError('/ToUnicode entry is not parseable')

        # Iterate over mapping object pairwise
        for glyph, unicode in zip(mapping_obj[0::2], mapping_obj[1::2]):
            self.mapping.add_entry(glyph.unparse(), unicode.unparse())

    def parse_placeholder_positions(self):
        content = self.document.pages[0].obj.Contents[0]
        content_parsed = pikepdf.parse_content_stream(content)

        """
        Text is inside BT (begin text) and ET (end text) operator.
        The actual text follows are the Tj operator, so in order to later replace/delete unnecessary placeholders
        we need to save the indices of BT, ET and TJ operators and their corresponding placeholder name
        """
        text_op_ctr = 0
        positions = []
        text_obj = {'TJ': [], 'name': []}
        for i in range(len(content_parsed)):
            if content_parsed[i].operator == BT_OP:
                text_obj['BT'] = i
            if content_parsed[i].operator == ET_OP:
                text_obj['ET'] = i
                if text_obj['name']:
                    positions.append(text_obj.copy())
                text_obj = {'TJ': [], 'name': []}
            if content_parsed[i].operator == TJ_OP:
                text_obj['TJ'].append(i)
                if len(content_parsed[i].operands) < 1:
                    continue

                # Parse the characters to an actual string and check if it is a placeholder
                text = self.tj_to_string(content_parsed[i].operands[0])

                """
                Check if one of the placeholder names appears as a substring inside the parsed text.
                Check this way around because the parsed text might contain more characters than the actual
                placeholders. check if "placeholder_a" in "<<placeholder_a>> <<placeholder_b>>"
                """
                for name in self.header:
                    if name in text:
                        text_obj['name'].append(name)

        return positions

        # for t in content_parsed[538].operands[0]:
        #     if isinstance(t, pikepdf.String):
        #         print('Glyph:', t.unparse())
        #         uc = self.mapping.get_mapping(t.unparse(), True)
        #         if uc is not None:
        #             print('Unicode:', (b'\u' + uc[1:-1]).decode('unicode_escape'))
        # print(pikepdf.unparse_content_stream(content_parsed).decode("utf-8"))
        print(self.header)
        return {}

    def tj_to_string(self, char_list):
        chars = []
        for char in char_list:
            if isinstance(char, pikepdf.String):
                unicode_bytes = self.mapping.get_mapping(char.unparse(), True)
                if unicode_bytes is not None:
                    chars.append(
                        self.unicode_bytes_to_string(unicode_bytes)
                    )
        return ''.join(chars)

    @staticmethod
    def build_file_name(parameter):
        return '{last_name}_{first_name}_{module}_{time}.pdf'.format(
            last_name=parameter['Nachname'],
            first_name=parameter['Vorname'],
            module=parameter['Modul'],
            time=time.time_ns())

    @staticmethod
    def unicode_bytes_to_string(unicode_bytes):
        # Converting unicode-bytes to a string needs a unicode specification (\u)
        # Also the raw unicode bytes are surrounded by < and > so we cut them off with slicing
        return (b'\u' + unicode_bytes[1:-1]).decode('unicode_escape')


class GlypthToUnicodeMapping:
    def __init__(self):
        self.to_unicode_mapping = {}
        self.to_glyph_mapping = {}

    def add_entry(self, glyph: bytes, unicode: bytes):
        self.to_unicode_mapping[glyph] = unicode
        self.to_glyph_mapping[unicode] = glyph

    def get_mapping(self, entry: bytes, is_glyph: bool):
        if is_glyph:
            if entry in self.to_unicode_mapping:
                return self.to_unicode_mapping[entry]
        if entry in self.to_glyph_mapping:
            return self.to_glyph_mapping[entry]
        return None


pdf = PDFGenerator('zertifikat.pdf', 'Empfaenger.xlsx', '.')

parse_excel_file(file_name='Empfaenger.xlsx')
