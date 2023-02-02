from asn1crypto import cms, x509, core, tsp
from collections import OrderedDict
import hashlib
from hashlib import sha256
import rfc3161ng


class CMSSignedData:
    def __init__(self):
        """
        Initializes the cms-objects with default values
        """
        self.signing_cert = None
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
        self.signing_cert = certs[0]
        self.signing_cert_raw = der_encoded_certs[0]
        signature_algorithm = self.signing_cert.native['signature_algorithm']['algorithm']
        issuer = self.signing_cert.native['tbs_certificate']['issuer']
        ias = cms.IssuerAndSerialNumber()
        ias['serial_number'] = self.signing_cert.native['tbs_certificate']['serial_number']
        ias['issuer'] = x509.Name.build(issuer, use_printable=True)
        sid = cms.SignerIdentifier(name='issuer_and_serial_number', value=ias)
        self.signer_info['sid'] = sid

        self.signer_info['signature_algorithm'] = OrderedDict([
            ('algorithm', signature_algorithm)
        ])

    def set_signature(self, signature: bytes):
        self.signer_info['signature'] = signature

    def set_signed_attrs(self, digest: bytes, privkey):
        m = sha256()
        m.update(self.signing_cert_raw)
        cert_hash = m.digest()
        self.signer_info['signed_attrs'] = [
            OrderedDict([
                ('type', 'content_type'),
                ('values', ['data'])
            ]),
            OrderedDict([
                ('type', 'message_digest'),
                ('values', [digest])
            ]),
            OrderedDict([
                ('type', 'signing_certificate_v2'),
                ('values', [tsp.SigningCertificateV2({
                    'certs': [
                        tsp.ESSCertIDv2({
                            'hash_algorithm': {'algorithm': 'sha256'},
                            'cert_hash': cert_hash,
                            'issuer_serial': {
                                'issuer': [
                                    x509.GeneralName({'directory_name': self.signing_cert.issuer})
                                ],
                                'serial_number': self.signing_cert.native['tbs_certificate']['serial_number']
                            }
                        })
                    ]
                })])
            ])
        ]
        import hashlib
        from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PrivateFormat, \
            KeySerializationEncryption
        from cryptography.hazmat.primitives.asymmetric import padding, utils
        from cryptography.hazmat.primitives import hashes
        data = self.signer_info['signed_attrs'].untag().dump()
        self.signer_info['signature'] = privkey.sign(data=data, padding=padding.PKCS1v15(), algorithm=hashes.SHA256())
        # self.add_timestamp_token()

    def set_digest_algorithms(self, name: str):
        self.singed_data['digest_algorithms'] = [OrderedDict([
            ('algorithm', name),
            ('parameters', None)
        ])]
        self.signer_info['digest_algorithm'] = OrderedDict([
            ('algorithm', name),
            ('parameters', None)
        ])

    def add_timestamp_token(self):
        rt = rfc3161ng.RemoteTimestamper(url='http://freetsa.org/tsr', hashname='sha256')
        hash_obj = hashlib.new('sha256')
        hash_obj.update(self.signer_info['signature'].native)
        signature_hash = hash_obj.digest()
        print(signature_hash.hex())

        tst = rt.timestamp(digest=signature_hash, include_tsa_certificate=False)

        signature_time_stamp = cms.ContentInfo.load(tst)

        self.signer_info['unsigned_attrs'] = [
            OrderedDict([
                ('type', 'signature_time_stamp_token'),
                ('values', [signature_time_stamp])
            ])
        ]

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
