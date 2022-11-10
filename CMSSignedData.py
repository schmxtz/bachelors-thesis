from asn1crypto import cms, x509, core
from collections import OrderedDict
from cryptography.hazmat.primitives.hashes import SHA224


class CMSSignedData:
    def __init__(self):
        """
        Initializes the cms-objects with default values
        """
        self.asn1obj = cms.ContentInfo()
        self.asn1obj['content_type'] = 'signed_data'
        self.singed_data = cms.SignedData()
        self.signer_info = cms.SignerInfo()
        self.__set_version()
        self.__set_encap_content_info()

    def load_certs(self, der_encoded_certs: [bytes]):
        certs = []
        for der_encoded_cert in der_encoded_certs:
            certs.append(x509.Certificate.load(der_encoded_cert))
        self.singed_data['certificates'] = certs
        signing_cert = certs[0]
        signature_algorithm = signing_cert.native['signature_algorithm']['algorithm']
        issuer = signing_cert.native['tbs_certificate']['issuer']
        ias = cms.IssuerAndSerialNumber()
        ias['serial_number'] = signing_cert.native['tbs_certificate']['serial_number']
        ias['issuer'] = x509.Name.build(OrderedDict([
            ('country_name', issuer['country_name']),
            ('state_or_province_name', issuer['state_or_province_name']),
            ('organization_name', issuer['organization_name']),
            ('organizational_unit_name', issuer['organizational_unit_name']),
            ('common_name', issuer['common_name']),
            ('email_address', issuer['email_address']),
        ]), use_printable=True)
        sid = cms.SignerIdentifier(name='issuer_and_serial_number', value=ias)
        self.signer_info['sid'] = sid

        self.signer_info['signature_algorithm'] = OrderedDict([
                ('algorithm', signature_algorithm),
                ('parameters', None)
        ])

    def set_signature(self, signature: bytes):
        self.signer_info['signature'] = signature

    def set_signed_attrs(self, digest: bytes):
        self.signer_info['signed_attrs'] = [
            OrderedDict([
                ('type', 'content_type'),
                ('values', ['data'])
            ]),
            OrderedDict([
                ('type', 'message_digest'),
                ('values', [digest])
            ])
        ]

    def set_digest_algorithms(self, name: str):
        self.singed_data['digest_algorithms'] = [OrderedDict([
            ('algorithm', name),
            ('parameters', None)
        ])]
        self.signer_info['digest_algorithm'] = OrderedDict([
            ('algorithm', name),
            ('parameters', None)
        ])

    def dump(self):
        self.singed_data['signer_infos'] = [self.signer_info]
        self.asn1obj['content'] = self.singed_data
        return self.asn1obj.dump()

    def __set_version(self):
        self.singed_data['version'] = 'v1'
        self.signer_info['version'] = 'v1'

    def __set_encap_content_info(self):
        self.singed_data['encap_content_info'] = OrderedDict([
            ('content_type', 'data')
        ])
