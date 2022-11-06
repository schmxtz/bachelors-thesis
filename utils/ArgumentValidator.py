from pikepdf import Rectangle


def validate_sig_pos(sig_pos: [int], rect: Rectangle):
    """
    Validates whether given position for signature is valid. Throws Exception if the given position coordinates are
    invalid.

    :param rect: Rectangle object containing the page specification
    :param sig_pos: Array containing 4 corner points of rectangle that surrounds the signature
    :return:
    """
    borders = [rect.urx, rect.ury, rect.urx, rect.ury]
    if len(sig_pos) != 4:
        raise ValueError('Argument sig_pos must specify 4 values.')
    for coord in range(4):
        if 0 > sig_pos[coord]:
            raise ValueError('Argument sig_pos coordinates cannot be negative.')
        if sig_pos[coord] > borders[coord]:
            raise ValueError('Argument sig_pos coordinates cannot exceed the page borders')
