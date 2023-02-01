import unittest
from datetime import datetime, timedelta
from pyhanko_certvalidator import errors

from test.utils.CertGenerator import *
from crypto.PadesBasic import PadesBasic

MINUTE_IN_SECS = 60
HOUR_IN_SECS = MINUTE_IN_SECS * 60
DAY_IN_SECS = HOUR_IN_SECS * 24
YEAR_IN_SECS = DAY_IN_SECS * 365


class PadesBasicTest(unittest.TestCase):
    def setUp(self) -> None:
        root_cert, root_key = generate_root_cert(0, DAY_IN_SECS)
        int_cert, int_key = generate_intermediate_cert(0, HOUR_IN_SECS, root_cert, root_key)
        end_cert, _ = generate_end_entity_cert(0, MINUTE_IN_SECS, int_cert, int_key)
        self.signing_cert = dump_cert_or_key(end_cert, crypto.FILETYPE_ASN1)
        self.intermediates = [dump_cert_or_key(int_cert, crypto.FILETYPE_ASN1)]
        self.custom_trust_root = dump_cert_or_key(root_cert, crypto.FILETYPE_ASN1)
        self.time = datetime.now().astimezone()

    def test_cert_is_valid(self):
        try:
            PadesBasic.validate_signing_cert(self.signing_cert, self.intermediates, self.time, self.custom_trust_root)
        except errors.PathValidationError:
            self.fail('Should not have raised {0}'.format(errors.PathValidationError.__class__.__name__))

    # Validation has 30 seconds time tolerance, check the validate_signing_cert function
    def test_cert_not_yet_valid(self):
        with self.assertRaises(errors.PathValidationError):
            new_time = self.time - timedelta(seconds=35)
            PadesBasic.validate_signing_cert(self.signing_cert, self.intermediates, new_time, self.custom_trust_root)

    def test_cert_is_expired(self):
        with self.assertRaises(errors.PathValidationError):
            new_time = self.time + timedelta(minutes=2)
            PadesBasic.validate_signing_cert(self.signing_cert, self.intermediates, new_time, self.custom_trust_root)
