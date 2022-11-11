from Signer import Signer
s = Signer(pdf_file_names=['Expose.pdf'], pkcs12_file_name='myfile.p12', passphrase=b'password',
           in_place=False)

from pyhanko.sign.general import load_cert_from_pemder
from pyhanko_certvalidator import ValidationContext
from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.sign.validation import validate_pdf_signature

root_cert = load_cert_from_pemder('cert.pem')
vc = ValidationContext(trust_roots=[root_cert])

with open('Expose_signed.pdf', 'rb') as doc:
    r = PdfFileReader(doc)
    sig = r.embedded_signatures[0]
    status = validate_pdf_signature(sig, vc)
    print(status.pretty_print_details())
