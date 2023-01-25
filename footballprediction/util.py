def read_file(filename: str) -> str:
    """
    Read a file's contents.

    Parameters:
        filename: The path to the file.

    Returns:
        The file's contents.
    """
    with open(filename) as f:
        return f.read()
