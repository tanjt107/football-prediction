from typing import Generator


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


def break_list_into_chunks(lst: list, size: int) -> Generator[list, None, None]:
    """ """
    for i in range(0, len(lst), size):
        yield lst[i : i + size]
