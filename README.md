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
    - python-docx: Library to replace the placeholders inside the .docx files and save them as new documents. Library 
                   hasn't been updated in a year and doesn't state it supports Python 3.9, but it works for the features
                   that have been used in this project. Should be replaced in the future.

- Notes for PDF-Generation:
    - VBS-script should stay as of now in the same directory as PDFGenerator.py
    - There can't be any instance of Word running when executing the script
    - It is necessary to give an output_path when executing the script
    
