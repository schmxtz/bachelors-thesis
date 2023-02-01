from OpenSSL import crypto
from typing import Union

HASHING_ALGO = 'sha256'


def generate_keypair():
    kp = crypto.PKey()
    kp.generate_key(crypto.TYPE_RSA, 2048)
    return kp


def dump_cert_or_key(cert_or_key: Union[crypto.X509, crypto.PKey], encoding: crypto.Type):
    if isinstance(cert_or_key, crypto.X509):
        return crypto.dump_certificate(encoding, cert_or_key)
    if isinstance(cert_or_key, crypto.PKey):
        return crypto.dump_privatekey(encoding, cert_or_key)
    raise ValueError('Given certificate or key is not a valid type.')


def generate_root_cert(not_before_offset: int, not_after_offset: int) -> (crypto.X509, crypto.PKey):
    """
    Creates a self-signed root certificate.

    :param not_before_offset: Offset in seconds when this certificate will become valid
    :param not_after_offset: Offset in seconds when this certificate will become invalid
    :return: Tuple consisting of the certificate and private key
    """
    # Create key pair
    kp = generate_keypair()

    # Create self-signed cert
    cert = crypto.X509()
    cert.get_subject().C = 'DE'
    cert.get_subject().ST = 'Rheinland-Pfalz'
    cert.get_subject().L = 'Trier'
    cert.get_subject().O = 'Hochschule Trier'
    cert.get_subject().CN = 'Hochschule Trier Root CA'
    cert.set_serial_number(1)
    cert.set_version(2)
    cert.gmtime_adj_notBefore(not_before_offset)
    cert.gmtime_adj_notAfter(not_after_offset)
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(kp)
    cert.add_extensions([
        crypto.X509Extension(b'basicConstraints', True, b'CA:TRUE'),
        crypto.X509Extension(b'keyUsage', False, b'keyCertSign, cRLSign, digitalSignature'),
        crypto.X509Extension(b'subjectKeyIdentifier', False, b'hash', subject=cert)
    ])
    cert.add_extensions([
        crypto.X509Extension(b'authorityKeyIdentifier', False, b'keyid:always', issuer=cert)
    ])

    cert.sign(kp, HASHING_ALGO)

    return cert, kp


def generate_intermediate_cert(not_before_offset: int, not_after_offset: int, ca_cert: crypto.X509, ca_key)\
        -> (bytes, bytes):
    """
    Creates an intermediate certificate and signs it with the given root cert.

    :param not_before_offset: Offset in seconds when this certificate will become valid
    :param not_after_offset: Offset in seconds when this certificate will become invalid
    :param ca_cert: Root certificate
    :param ca_key: Private key of root certificate
    :return: Tuple consisting of the certificate and private key
    """
    # Create key pair
    kp = generate_keypair()

    # Create self-signed cert
    cert = crypto.X509()
    cert.get_subject().C = 'DE'
    cert.get_subject().ST = 'Rheinland-Pfalz'
    cert.get_subject().L = 'Trier'
    cert.get_subject().O = 'Hochschule Trier'
    cert.get_subject().CN = 'Fachbereich Informatik CA'
    cert.set_serial_number(2)
    cert.set_version(2)
    cert.gmtime_adj_notBefore(not_before_offset)
    cert.gmtime_adj_notAfter(not_after_offset)
    cert.set_issuer(ca_cert.get_subject())
    cert.set_pubkey(kp)
    cert.add_extensions([
        crypto.X509Extension(b'basicConstraints', False, b'CA:TRUE'),
        crypto.X509Extension(b'subjectKeyIdentifier', False, b'hash', subject=cert),
        crypto.X509Extension(b'keyUsage', False, b'digitalSignature, keyCertSign, cRLSign'),
    ])
    cert.add_extensions([
        crypto.X509Extension(b'authorityKeyIdentifier', False, b'keyid:always', issuer=ca_cert),
    ])

    cert.sign(ca_key, HASHING_ALGO)

    return cert, kp


def generate_end_entity_cert(not_before_offset: int, not_after_offset: int, intermediate_cert: crypto.X509,
                             intermediate_key) -> (bytes, bytes):
    """
    Creates an intermediate certificate and signs it with the given root cert.

    :param not_before_offset: Offset in seconds when this certificate will become valid
    :param not_after_offset: Offset in seconds when this certificate will become invalid
    :param intermediate_cert: Intermediate certificate
    :param intermediate_key: Private key of intermediate certificate
    :return: Tuple consisting of the certificate and private key
    """
    # Create key pair
    kp = generate_keypair()

    # Create self-signed cert
    cert = crypto.X509()
    cert.get_subject().C = 'DE'
    cert.get_subject().ST = 'Rheinland-Pfalz'
    cert.get_subject().L = 'Trier'
    cert.get_subject().O = 'Hochschule Trier'
    cert.get_subject().CN = 'End-Entity Zertifikat'
    cert.set_serial_number(3)
    cert.set_version(2)
    cert.gmtime_adj_notBefore(not_before_offset)
    cert.gmtime_adj_notAfter(not_after_offset)
    cert.set_issuer(intermediate_cert.get_subject())
    cert.set_pubkey(kp)
    cert.add_extensions([
        crypto.X509Extension(b'basicConstraints', False, b'CA:FALSE'),
        crypto.X509Extension(b'keyUsage', False, b'digitalSignature'),
        crypto.X509Extension(b'subjectKeyIdentifier', False, b'hash', subject=cert),

    ])
    cert.add_extensions([
        crypto.X509Extension(b'authorityKeyIdentifier', False, b'keyid:always', issuer=intermediate_cert),
    ])

    cert.sign(intermediate_key, HASHING_ALGO)

    return cert, kp

