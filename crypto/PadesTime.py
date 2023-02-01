from PadesBasic import PadesBasic

class PadesTime(PadesBasic):
    def __init__(self, pdf_file_names: [str], pkcs12_file_name: str, passphrase: bytes):
        """
        Only needs to call the __init__ function of the upper class as it needs the same initialization. From B-B level
        to B-T level we only add a timestamp.

        :param pdf_file_names:
        :param pkcs12_file_name:
        :param passphrase:
        """
        super.__init__(self, pdf_file_names, pkcs12_file_name, passphrase)


