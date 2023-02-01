from asn1crypto import cms, x509, tsp
from collections import OrderedDict
from hashlib import sha256
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes


class CMSSignedData:
    def __init__(self):
        """
        Initializes the cms-objects with default values
        """
        self.signing_cert_raw = None
        self.signing_cert = None
        # SignedData object is encapsulated by ContentInfo object
        self.asn1obj = cms.ContentInfo()
        self.asn1obj['content_type'] = 'signed_data'
        self.singed_data = cms.SignedData()
        self.signer_info = cms.SignerInfo()
        """
        Version might need to change in the future if the type of certificate changes, more information to the version
        is in corresponding RFC, RFC 5652 clause 5.1
        """
        self.__set_version()
        self.__set_encap_content_info()

    def load_certs(self, der_encoded_certs: [bytes]):
        certs = []

        # Parse raw DER-encoded certificate bytes into x509.Certificate object
        for der_encoded_cert in der_encoded_certs:
            certs.append(x509.Certificate.load(der_encoded_cert))
        self.singed_data['certificates'] = certs
        self.signing_cert = certs[0]

        # Raw signing cert is later needed to calculate hash, see set_signed_attrs function
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

    def set_signed_attrs(self, digest: bytes, privkey) -> None:
        """
        List of signed attributes used in a PAdES signature as specified in EN 319 122-1 - V1.2.1:
        Required attributes:
            - content-type: Must be id-data ('data' as string) see EN 319 142-1 - V1.1.1 clause 6.3 c
            - message-digest: The message-digest of the entire document exluding the cms-object itself
            - signing-certificate-v2: A protection of the signing certificate shall be provided, as we don't want to use
                                      SHA-1 for the certificate hash calculation we have to use signing-certificate-v2,
                                      see EN 319 122-1 - V1.0.0 clause 5.2.2.2/5.2.2.3


        Optional:
            - signer-attributes-v2: Won't be present as it only represents attributes set by the signing entity,
                                    not the signature or signed content
            - content-time-stamp: Not yet implemented, only timestamps the document before signing
            - signature-policy-identifier: As no signature policy is defined, there is no need for an identifier, see
                                           RFC 3280 for more information about policies
            - commitment-type-indication: Either commitment is given in CMS or the reason is given inside the signature
                                          dictionary inside the PDF, we use the latter

        :param digest: The digest of the entire document excluding the cms-object
        :param privkey: The private key with which the signature is generated
        """
        # Calculate certificate hash used in SigningCertificateV2 attribute, any SHA2 or SHA3 hash can be used, don't
        # use SHA-1 or MD-5
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
            # SigningCertificateV2 is defined in RFC 5035 clause 3
            OrderedDict([
                ('type', 'signing_certificate_v2'),
                ('values', [tsp.SigningCertificateV2({
                    'certs': [
                        # ESSCertIDv2 is defined in RFC 5035 clause 4
                        tsp.ESSCertIDv2({
                            'hash_algorithm': {'algorithm': 'sha256'},
                            'cert_hash': cert_hash,
                            # IssuerSerial is defined in RFC 5035 clause 4
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

        data = self.signer_info['signed_attrs'].untag().dump()
        self.signer_info['signature'] = privkey.sign(data=data, padding=padding.PKCS1v15(), algorithm=hashes.SHA256())

    def set_digest_algorithms(self, name: str) -> None:
        """
        Sets the digest-algorithm to be later used to calculate the message digest of the pdf file.

        :param name: Name of the digest-algorithm
        """
        self.singed_data['digest_algorithms'] = [OrderedDict([
            ('algorithm', name),
            ('parameters', None)
        ])]
        self.signer_info['digest_algorithm'] = OrderedDict([
            ('algorithm', name),
            ('parameters', None)
        ])

    def dump(self):
        """
        Object can only be constructed at the end, when it's properly populated.

        :return:
        """
        self.singed_data['signer_infos'] = [self.signer_info]
        self.asn1obj['content'] = self.singed_data
        return self.asn1obj.dump()

    def __set_version(self):
        """
        Sets the version of the SignedData and SignerInfo objects. Is for now in our use-case always version 1, but that
        could change. Check RFC 5652 clause 5.1 for SignedData version and RFC 5652 clause 5.3 for SignerInfo version.

        :return:
        """
        self.singed_data['version'] = 'v1'
        self.signer_info['version'] = 'v1'

    def __set_encap_content_info(self):
        """
        Content-type must be set to 'id-data' as specified in RFC 5652 clause 5.2 because we're calculating external
        signatures. In this case setting it to 'data', sets it to id-data. I don't know if that's an implementation
        error but setting it to 'id-data' doesn't work.

        :return:
        """
        self.singed_data['encap_content_info'] = OrderedDict([
            ('content_type', 'data')
        ])
