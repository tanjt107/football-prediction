from footballprediction.util import break_list_into_chunks, read_file


def test_break_list_into_chunks():
    data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    res = break_list_into_chunks(data, 3)
    assert next(res) == [1, 2, 3]
    assert next(res) == [4, 5, 6]
    assert next(res) == [7, 8, 9]
    assert next(res) == [10]


def test_read_file():
    assert read_file("tests/test.sql") == "INSERT INTO movie VALUES(?, ?, ?)"
