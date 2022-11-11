from distutils.core import setup

setup(name='Python PDF signer',
      version='1.0',
      description='description',
      author='Philipp Schmitz',
      author_email='schmitph@hochschule-trier.de',
      packages=['pyhanko', 'pikepdf', asn1crypto, cryptography],
     )
