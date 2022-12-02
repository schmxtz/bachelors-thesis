def has_numbers(s: str):
    """
    Checks if given string contains numbers

    :param s: Given string
    :return: Boolean indicating the presence of a number
    """
    return any(char.isdigit() for char in s)
