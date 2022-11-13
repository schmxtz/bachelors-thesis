- Requirements:
    - Python 3.9
    - Run pip install -r requirements.txt

- TODO's:
    - Add certificate validation
    - Add feature to generate self-signed certificate
    - Make changes to comply with PAdES-baseline and additional level
    - Add feature to generate PDFs based on the table
    - Clean up code
    - Feature for adding image signature
    - UI

- Explanation for choice of library:
    - pikepdf: Library to work with PDF files on the object-level
    - asn1crypto: Library to create the CMS-object and is useful for parsing certificates
    - cryptography: Library to parse the keystore and to create the signature
    - pyhanko: Was used to validate my created signatures/error debugging
    - openpyxl: Library to parse the excel sheet containing the information necessary for generating the PDF files
    
