from utils.Files import parse_excel_file
import time, pikepdf, itertools
from pikepdf import Pdf, AccessMode

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
        self.template_file_name = template_file_name
        self.parameters, self.header = parse_excel_file(excel_file_name)
        document = Pdf.open(filename_or_stream=template_file_name)
        self.mapping = GlypthToUnicodeMapping()

        """
        PDF renders strings by printing them character by character. In a PDF these are called glyphs and there exists 
        in most cases a /ToUnicode entry. This entry should map all glyphs in the template_file to corresponding unicode
        characters. So in order to find and replace whole strings we to parse the mapping. 
        """
        self.parse_glyph_unicode_mapping(document)

        # Now that we have the glyph to unicode mapping we can start looking for the placeholder strings
        self.positions = self.parse_placeholder_positions(document)
        document.close()

    def make_pdfs(self):
        # Now that we have the positions of the placeholder strings we can replace them with the actual strings for
        # every row of the excel sheet and save each of them in a separate file
        for parameter in self.parameters[0:1]:
            output_filename = self.build_file_name(parameter=parameter)

            # For every new file, the template has to be reopened as we tamper with its content stream
            document = Pdf.open(filename_or_stream=self.template_file_name, allow_overwriting_input=False)
            content = document.pages[0].obj.Contents[0]
            content_parsed = pikepdf.parse_content_stream(content)

            """            
            Now we need to iterate over the placeholder positions array and check whether the placeholder is to
            replaced by an actual value from the parameter map, if not that placeholder is to be deleted. We also need
            loop over it in reversed order because we're deleting elements and that would shift the indices of 
            subsequent elements if we were to start at the beginning.
            """
            for position in reversed(self.positions):
                # If there is no value for the given placeholder, delete its entry
                if not [key for key in position['name'] if key in parameter]:
                    self.delete_entries(content_parsed, position['BT'], position['ET'])
                else:
                    for start, ctr, index in position['TJ']:
                        self.replace_tj_entry(document, parameter, content_parsed, index, position['name'][start:ctr])

            # Replace the old content stream with the changed one
            document.pages[0].obj.Contents[0] = document.make_stream(
                pikepdf.unparse_content_stream(content_parsed)
            )

            # Delete the last, as its sole purpose is the placeholder for potential characters
            del (document.pages[-1])
            document.save(output_filename)
            document.close()

    def parse_glyph_unicode_mapping(self, document):
        # Each pages' resources reference the same fonts, thus we can just take the first
        font_list = document.pages[0]['/Resources']['/Font']

        # Put the main font at the end of the list, so that unicode->glyph mappings can be overwritten
        # We do this because different font glyphs can map to the same unicode char
        font_names_list = list(font_list)
        for i in range(len(font_names_list)):
            if font_list[font_names_list[i]]['/BaseFont'] == FONT_NAME:
                break
        font_names_list[-1], font_names_list[i] = font_names_list[i], font_names_list[-1]

        # Loop through available fonts and add their mappings,
        for font in font_names_list:
            target_font = font_list[font]

            if target_font is None or target_font.get('/ToUnicode') is None:
                continue

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

    def parse_placeholder_positions(self, document):
        content = document.pages[0].obj.Contents[0]
        content_parsed = pikepdf.parse_content_stream(content)

        """
        Text is inside BT (begin text) and ET (end text) operator.
        The actual text follows are the Tj operator, so in order to later replace/delete unnecessary placeholders
        we need to save the indices of BT, ET and TJ operators and their corresponding placeholder name
        """

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
                """                
                Save start, counter and index of found placeholder strings inside BT-ET-block, because:
                1. There can be more than one TJ blocks inside BT-ET-block
                2. There can be more than one placeholder string inside one TJ block
                So by saving the ctr and index of TJ-block we can later map which strings belonged to which TJ-block
                """
                start = len(text_obj['name'])

                # Parse the characters to an actual string and check if it is a placeholder
                text = self.tj_to_string(content_parsed[i].operands[0])
                """
                Check if one of the placeholder names appears as a substring inside the parsed text.
                Check this way around because the parsed text might contain more characters than the actual
                placeholders. check if "placeholder_a" in "<<placeholder_a>> <<placeholder_b>>"
                """
                for name in self.header:
                    # Check for placeholder marking so that we don't replace text by accident
                    if '«' in text and name in text:
                        text_obj['name'].append(name)
                ctr = len(text_obj['name'])
                text_obj['TJ'].append((start, ctr, i))

        return positions

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

    def replace_tj_entry(self, document, parameter, content, index, names):
        # As our placeholders are surrounded by « and » we need to replace every char enclosed by the actual char
        new_text = pikepdf.Array()
        operands = list(content[index].operands[0])
        operands_len = len(operands)
        operand_ctr = 0

        opening_arrow_glyph = self.mapping.get_mapping(b'<00ab>', False)
        closing_arrow_glyph = self.mapping.get_mapping(b'<00bb>', False)

        for name in names:
            parameter_value = parameter[name]
            # Append all text in front of the placeholder, if « is found we assign its index to operand_ctr
            for i in range(operand_ctr, operands_len):
                if isinstance(operands[i], pikepdf.String):
                    if operands[i].unparse() == opening_arrow_glyph:
                        operand_ctr = i
                        break
                new_text.append(operands[i])

            # Next we need to give the offset of the « char to the first letter of the actual text
            new_text.append(pikepdf.Object.parse(self.char_to_glyph_bytes(parameter_value[0])))
            if operand_ctr + 1 < operands_len and not isinstance(operands[operand_ctr + 1], pikepdf.String):
                operand_ctr += 1
                new_text.append(operands[operand_ctr])

            # Now we append the remaining chars
            for i in range(1, len(parameter_value)):
                print(parameter_value[i])
                new_text.append(pikepdf.Object.parse(self.char_to_glyph_bytes(parameter_value[i])))

            # Move the operand_ctr one index after the closing arrow
            for i in range(operand_ctr, operands_len):
                if isinstance(operands[i], pikepdf.String):
                    if operands[i].unparse() == closing_arrow_glyph:
                        operand_ctr = i + 1
                        break

        # Append the remaining text
        for i in range(operand_ctr, operands_len):
            new_text.append(operands[i])

        new_content = new_text.unparse() + b' ' + content[index].operator.unparse()
        new_content_instruction = pikepdf.parse_content_stream(document.make_stream(new_content))[0]
        content[index] = new_content_instruction

    def char_to_glyph_bytes(self, char):
        encoded_char = char.encode('unicode_escape')
        encoded_unicode_bytes = bytes(''.join(['<', encoded_char.hex().zfill(4), '>']), 'utf-8')
        return self.mapping.get_mapping(encoded_unicode_bytes, False)

    @staticmethod
    def build_file_name(parameter):
        return '{last_name}_{first_name}_{module}_{time}.pdf'.format(
            last_name=parameter['Nachname'],
            first_name=parameter['Vorname'],
            module=parameter['Modul'],
            time=time.time_ns())

    @staticmethod
    def delete_entries(object_list, start, end):
        """
        Deletes entries in the _ObjectList with start and end being inclusive

        :param object_list: Object to delete entries from
        :param start: First index of the elements to delete
        :param end: Last index of the elements to delete
        :return: Returns whether deletion was successful
        """
        try:
            for i in range(start, end + 1):
                object_list.pop(start)
            return True
        except IndexError as index_err:
            return False

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
        self.to_glyph_mapping[unicode] = glyph
        self.to_unicode_mapping[glyph] = unicode

    def get_mapping(self, entry: bytes, is_glyph: bool):
        if is_glyph:
            return self.to_unicode_mapping.get(entry)
        return self.to_glyph_mapping.get(entry)


pdf = PDFGenerator('zert4.pdf', 'Empfaenger.xlsx', '.')
pdf.make_pdfs()
