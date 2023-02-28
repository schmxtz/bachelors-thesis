from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import pkcs12, Encoding
from pyhanko_certvalidator import CertificateValidator, ValidationContext
from datetime import datetime, timedelta
from asn1crypto import x509
import logging

from crypto.CMSSignedData import CMSSignedData
from SignerContext import DigestAlgorithms, SignerContext
from pdf.PDFWriter import PDFWriter
from utils.Files import find_sig_dict_byte_pos


class PadesBasic:
    def __init__(self, pkcs12_file_name: str, passphrase: bytes, signer_context: SignerContext):
        """
        Loads keystore and performs basic check whether the signing certificate is valid (not revoked or expired).

        :param pkcs12_file_name: PKCS-12 file containing the signing certificate
        :param passphrase: Passphrase used to decrypt the keystore
        :param signer_context: Includes all the necessary information needed to create the signature
        """
        self.pkcs12_file_name = pkcs12_file_name
        self.passphrase = passphrase

        self.private_key = None
        self.der_encoded_certs = None

        self.load_keystore()

        # Perform certificate validation
        self.validate_signing_cert(self.der_encoded_certs[0], self.der_encoded_certs[1:], datetime.now().astimezone())

        # Create CMS object, that is to be filled with signature related information
        self.cms = CMSSignedData()
        self.cms.load_certs(self.der_encoded_certs)
        self.cms.set_digest_algorithms(signer_context.digest_algorithm.value)

    def load_keystore(self) -> None:
        """
        Stores the private key and the corresponding certificate chain.
        """
        logging.info('Loading keystore...')
        keystore = pkcs12.load_pkcs12(data=open(self.pkcs12_file_name, 'rb').read(), password=self.passphrase)

        # Store private key
        self.private_key = keystore.key
        if not self.private_key:
            raise ValueError('Keystore {0} is missing a private key'.format(self.pkcs12_file_name))

        # Store signing certificate
        self.der_encoded_certs = [keystore.cert.certificate.public_bytes(Encoding.DER)]
        if not self.der_encoded_certs[0]:
            raise ValueError('Keystore {0} is missing a signing certificate'.format(self.pkcs12_file_name))

        # Append the intermediate and end certificate
        for additional_cert in keystore.additional_certs:
            self.der_encoded_certs.append(additional_cert.certificate.public_bytes(Encoding.DER))

    def sign(self) -> None:

    @staticmethod
    def validate_signing_cert(signing_cert: bytes, intermediate_certs: [bytes], point_in_time: datetime,
                              custom_trust_root: bytes = None) -> None:
        """
        Checks revocation and expiration of only the signing certificate

        :param signing_cert: Signing certificate
        :param intermediate_certs: Intermediate certificates
        :param point_in_time: Point in time to check whether given cert is valid
        :param custom_trust_root: Parameter is used when using a self-generated certificate whose root certificate
        doesn't appear on the systems trusted root list
        """
        logging.info('Performing certifcate validation (B-Level)...')
        x509_signing_cert = x509.Certificate.load(signing_cert)
        intermediates = None
        if intermediate_certs:
            intermediates = []
            for intermediate in intermediate_certs:
                intermediates.append(x509.Certificate.load(intermediate))

        if custom_trust_root is not None:
            custom_trust_root = x509.Certificate.load(custom_trust_root)

        # Revocation check, allow_fetching true so that the library can do the OCSP calls
        context = ValidationContext(allow_fetching=True, revocation_mode='hard-fail', trust_roots=[custom_trust_root])
        validator = CertificateValidator(end_entity_cert=x509_signing_cert,
                                         intermediate_certs=intermediates,
                                         validation_context=context)
        validator.validate_usage({'digital_signature'})

        # Expiration check with a thirty seconds time_tolerance
        context = ValidationContext(moment=point_in_time, time_tolerance=timedelta(seconds=30),
                                    trust_roots=[custom_trust_root])
        validator = CertificateValidator(end_entity_cert=x509_signing_cert,
                                         intermediate_certs=intermediates,
                                         validation_context=context)
        validator.validate_usage({'digital_signature'})
