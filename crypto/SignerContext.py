from enum import Enum


class PadesLevel(Enum):
    PADES_BASELINE_B = 'PAdES-BASELINE-B'
    PADES_BASELINE_T = 'PAdES-BASELINE-T'
    PADES_BASELINE_LT = 'PAdES-BASELINE-LT'
    PADES_BASELINE_LTA = 'PAdES-BASELINE-LTA'


class DigestAlgorithms(Enum):
    """
    List as specified in ETSI TS 119 312 - V1.2.1 (ch. 5.1), this is list is set to be used as specified in the PAdES
    BASELINE document ETSI EN 319 142-1 V1.1.1 (ch. 6.2.1)
    """
    SHA_224 = 'sha224'
    SHA_256 = 'sha256'
    SHA_384 = 'sha384'
    SHA_512 = 'sha512'
    SHA3_256 = 'sha3_224'
    SHA3_384 = 'sha3_256'
    SHA3_512 = 'sha3_384'


class SignerContext:
    def __init__(self, pades_level: PadesLevel, digest_algorithm: DigestAlgorithms, in_place: bool = False):
        self.pades_level = pades_level
        self.digest_algorithm = digest_algorithm
        self.in_place = in_place


