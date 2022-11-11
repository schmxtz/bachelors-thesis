import pikepdf, os
from pikepdf import Pdf, Rectangle
from utils.ArgumentValidator import validate_sig_pos

SIGNATURE_BOX_WIDTH = 200
SIGNATURE_BOX_HEIGHT = 50


class PDFWriter:
    def __init__(self, file_name: str, content_padding: int, in_place: bool = False, page_index: int = None,
                 sig_pos: [int] = None):
        """
        Initializes the PDF-object that can be later fed with signature information

        :param file_name: Name of the file that should be signed
        :param content_padding: Padding size of the /Contents value in bytes
        :param in_place: Boolean indicating whether to create a new file or overwrite the current one
        :param page_index: Number stating on which page to place the signature, if left blank -> signature placed on
        last page
        :param sig_pos: Coordinates of the signature field (lower-left x, lower-left y, upper-right x, upper-right y),
        if left blank it's placed in the bottom right corner, if sig_pos is [0, 0, 0, 0] signature will not be rendered
        """
        self.doc = Pdf.open(filename_or_stream=file_name, allow_overwriting_input=True)
        self.file_name = file_name
        self.content_padding = content_padding
        self.in_place = in_place

        num_of_pages = len(self.doc.pages)
        if page_index is None or page_index >= num_of_pages:
            self.page_index = len(self.doc.pages) - 1

        # MediaBox object is a rectangle, but it still needs to be 'put' into one in order to access the attributes
        page_specs = Rectangle(self.doc.pages[self.page_index]['/MediaBox'])
        self.sig_pos = sig_pos
        if self.sig_pos is None:
            # ll = lower-left, ur = upper-right
            # Use maximum of desired coords and 0, because the page could be smaller than the desired width/height
            llx = max(0, page_specs.urx - SIGNATURE_BOX_WIDTH)
            lly = max(0, page_specs.ury - SIGNATURE_BOX_HEIGHT)
            urx = page_specs.urx
            ury = page_specs.ury
            self.sig_pos = [llx, lly, urx, ury]

        else:
            validate_sig_pos(sig_pos, page_specs)

        """
        The ByteRange key is placed automatically in front of the Contents key in the signature dictionary. This poses a
        problem as the values in the ByteRange would shift the position of the Contents key. For example:
        /ByteRange [0 100 2500 1000] would be shorter than /ByteRange [0 1000 17000 5400] and would thus shift the 
        following content. To ensure that changing the ByteRange won't shift the following contents, I just calculate
        the maximum size of possible byte ranges and later replace them with the actual ranges padded with leading 
        zeros.
        """

        size_in_bytes = os.stat(file_name).st_size
        # Content padding times 2 because it's saved as hex string -> 1 byte == 2 hex chars -> 2 byte (in file)
        size_in_bytes_with_signature = size_in_bytes + self.content_padding * 2
        number_of_digits = len(str(size_in_bytes_with_signature)) - 1
        self.byte_range_placeholder = pow(10, number_of_digits)
        self.sig_dict_obj = None
        self.annot_dict_obj = None
        self.sig_field_dict_obj = None

        # Create dictionaries necessary for a valid signature
        self.create_sig_dict()
        self.create_annot_dict()
        self.create_sig_field_dict()

        # Annots might not exist on desired page
        if not '/Annots' in self.doc.pages[self.page_index]:
            self.doc.pages[self.page_index].Annots = pikepdf.Array()

        # Add reference to annotation dict to the annotations array for this page
        self.doc.pages[self.page_index].Annots.append(self.doc.make_indirect(self.annot_dict_obj))

        # Add reference to AcroForm entry in Root dictionary
        self.doc.Root['/AcroForm'] = self.doc.make_indirect(self.sig_field_dict_obj)
        self.output_file_name = self.save()

    def save(self):
        if self.in_place:
            self.doc.save(self.file_name, normalize_content=False, static_id=True)
            return self.file_name
        else:
            out_file_name = self.file_name[:-4] + '_signed.pdf'
            self.doc.save(out_file_name, normalize_content=False, static_id=True, deterministic_id=True)
            return out_file_name

    def create_sig_dict(self):
        sig_dict = pikepdf.Dictionary(
            {
                '/Type': pikepdf.Name('/Sig'),
                '/Filter': pikepdf.Name('/Adobe.PPKLite'),
                '/SubFilter': pikepdf.Name('/ETSI.CAdES.detached'),
                # Fill the Contents value with zero-padding, should be large enough to fit the CMS-SignedData object
                '/Contents': pikepdf.String(b'\0'*self.content_padding),
                '/ByteRange': [self.byte_range_placeholder,
                               self.byte_range_placeholder,
                               self.byte_range_placeholder,
                               self.byte_range_placeholder]
            }
        )
        self.sig_dict_obj = self.doc.make_indirect(sig_dict)

    def create_annot_dict(self):
        annot_dict = pikepdf.Dictionary(
            {
                '/Type': pikepdf.Name('/Annot'),
                '/SubType': pikepdf.Name('/Widget'),
                '/FT': pikepdf.Name('/Sig'),
                '/Rect': [0.0, 0.0, 0.0, 0.0],
                '/V': self.sig_dict_obj,
                '/T': 'Signature1',
                '/F': 132,
                '/P': self.doc.pages[self.page_index].obj,
                '/AP': pikepdf.Dictionary(
                    {
                        '/N': pikepdf.Dictionary(
                            {
                                '/Length': 0,
                                '/Type': pikepdf.Name('/XObject'),
                                '/Subtype': pikepdf.Name('/Form'),
                                '/BBox': [0.0, 0.0, 0.0, 0.0]
                            }
                        )
                    }
                )
            }
        )
        self.annot_dict_obj = self.doc.make_indirect(annot_dict)

    def create_sig_field_dict(self):
        sig_field_dict = pikepdf.Dictionary(
            {
                '/Fields': pikepdf.Array([self.annot_dict_obj]),
                '/SigFlags': 3
            }
        )
        self.sig_field_dict_obj = self.doc.make_indirect(sig_field_dict)

