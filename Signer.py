import pikepdf
from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PrivateFormat, KeySerializationEncryption
from cryptography.hazmat.primitives.asymmetric import padding, utils
from cryptography.hazmat.primitives import hashes
from CMSSignedData import CMSSignedData
from PDFWriter import PDFWriter
from utils.Files import find_sig_dict_byte_pos
import os, mmap


CONTENTS_PADDING = 10000
HASHING_ALGO = 'sha256'

class Signer:
    def __init__(self, pdf_file_names: [str], pkcs12_file_name: str, passphrase: bytes, in_place: bool = False):
        if not pdf_file_names:
            return

        # Load keystore
        keystore = pkcs12.load_pkcs12(data=open(pkcs12_file_name, 'rb').read(), password=passphrase)
        self.private_key = keystore.key

        # Store all certificates of keystore as der-encoded bytes into list, needed for cms-object later
        der_encoded_certs = [keystore.cert.certificate.public_bytes(Encoding.DER)]
        for additional_cert in keystore.additional_certs:
            der_encoded_certs.append(additional_cert.certificate.public_bytes(Encoding.DER))

        # Create one CMS-object, as only the signature and message digest changes for multiple singed pdfs when the
        # same cert is used
        cms = CMSSignedData()
        cms.load_certs(der_encoded_certs=der_encoded_certs)
        cms.set_digest_algorithms(HASHING_ALGO)

        for pdf_file in pdf_file_names:
            pdf_writer = PDFWriter(file_name=pdf_file, content_padding=CONTENTS_PADDING, in_place=in_place)
            output_file_name = pdf_writer.output_file_name

            # Find byte positions of ByteRange entry and Contents entry,
            byte_start, byte_end, contents_start = find_sig_dict_byte_pos(file_name=output_file_name)

            # Construct the new entry of ByteRange
            range_len = len(str(pdf_writer.byte_range_placeholder))
            file_size = os.stat(output_file_name).st_size

            # CONTENTS_PADDING times 2 because it's saved as hex string -> 1 byte == 2 hex chars -> 2 byte (in file)
            contents_end = contents_start + 2 * CONTENTS_PADDING + 2

            # Add 1 at the end because the end index is exclusive meaning it's an [, ...) interval
            self.byte_range_raw = [0, contents_start, contents_end, file_size - contents_end]
            byte_range = ' {0} {1} {2} {3} '.format(
                str(self.byte_range_raw[0]).zfill(range_len),
                str(self.byte_range_raw[1]).zfill(range_len),
                str(self.byte_range_raw[2]).zfill(range_len),
                str(self.byte_range_raw[3]).zfill(range_len)
            ).encode('utf-8')

            # Replace the old placeholder ByteRange with the correct one
            with open(output_file_name, 'r+b') as f:
                m = mmap.mmap(f.fileno(), 0)
                m[byte_start:byte_end] = byte_range
                m.flush()

            # Calculate hash of file over given ByteRange
            file_hash = self.calculate_hash(file_name=output_file_name, hash_algo=HASHING_ALGO)
            cms.set_signed_attrs(digest=file_hash, privkey=self.private_key)

            # Calculate signature from hash and private key
            # signature = self.private_key.sign(data=file_hash, padding=padding.PKCS1v15(), algorithm=hashes.SHA256())

            # cms.set_signature(signature)
            cms_dump = cms.dump().hex().encode('ascii')

            # Replace part of the /Contents entry with the correct cms-object
            with open(output_file_name, 'r+b') as f:
                m = mmap.mmap(f.fileno(), 0)
                m[contents_start + 1:contents_start + len(cms_dump) + 1] = cms_dump
                m.flush()

    def calculate_hash(self, file_name: str, hash_algo: str):
        if hash_algo == 'sha256':
            digest = hashes.Hash(hashes.SHA256())

        with open(file_name, 'rb') as f:
            # Read everything until start of Contens entry
            data = f.read(self.byte_range_raw[1])
            digest.update(data)

            # Skip the Contents entry
            f.read(self.byte_range_raw[2] - self.byte_range_raw[1])

            # Read the rest
            data = f.read((self.byte_range_raw[3]))
            digest.update(data)
        return digest.finalize()


