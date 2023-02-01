import mmap
import os

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import pkcs12, Encoding

from CMSSignedData import CMSSignedData
from pdf.PDFWriter import PDFWriter
from utils.Files import find_sig_dict_byte_pos
from SignerContext import SignerContext, PadesLevel
from PadesBasic import PadesBasic

CONTENTS_PADDING = 10000
HASHING_ALGO = 'sha256'


class Signer:
    def __init__(self, pdf_file_names: [str], pkcs12_file_name: str, passphrase: bytes, signer_context: SignerContext):
        if not pdf_file_names:
            return

        self.pades_object = None
        if signer_context.pades_level == PadesLevel.PADES_BASELINE_B:
            self.pades_object = PadesBasic(pdf_file_names=pdf_file_names,
                                           pkcs12_file_name=pkcs12_file_name,
                                           passphrase=passphrase)
            self.pades_object.set_digest_algorithm(signer_context.digest_algorithm)
