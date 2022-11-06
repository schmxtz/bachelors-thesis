from asn1crypto import cms, x509
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
        key_id = certs[0].key_identifier_value.native
        signature_algorithm = certs[0].native['signature_algorithm']['algorithm']
        self.signer_info['sid'] = cms.SignerIdentifier({
            'subject_key_identifier': key_id})
        self.signer_info['signature_algorithm'] = OrderedDict([
                ('algorithm', signature_algorithm),
                ('parameters', None)
        ])

    def set_signature(self, signature: bytes):
        self.signer_info['signature'] = signature

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
        self.singed_data['version'] = 'v0'
        self.signer_info['version'] = 'v0'

    def __set_encap_content_info(self):
        self.singed_data['encap_content_info'] = OrderedDict([
            ('content_type', 'data')
        ])
