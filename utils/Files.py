

def find_sig_dict_byte_pos(file_name: str):
    """
    This function assumes alot of the given file:,
        - it assumes that the line containing the signature dictionary starts with << /ByteRange
        - it assumes that the entire dictionary is contained in one line, even if the signature were to contain a
        carrier return, the cms object is saved a hex string, so we're good here
        - it assumes that the ByteRange comes prior to the Contents entry

    :param file_name:
    :return: Returns byte position of /ByteRange [ ... ] and /Contents <
    """
    with open(file_name, 'rb') as pdf_file:
        lines = pdf_file.readlines()
        sig_dict = None
        ctr = 0
        byte_range_start = None
        byte_range_end = None
        contents_start = None
        for line in lines:
            if line.startswith(b'<< /ByteRange'):
                # Skip first 2 chars because they are already chars we're looking for ('<')
                for i in range(2, len(line)):
                    if line[i] == ord('['):
                        byte_range_start = ctr + i + 1
                    elif line[i] == ord(']'):
                        byte_range_end = ctr + i
                    elif line[i] == ord('<'):
                        contents_start = ctr + i + 1
                        return byte_range_start, byte_range_end, contents_start
            else:
                ctr += len(line)
        raise ValueError('Byte Position of signature cannot be found inside output file.')


