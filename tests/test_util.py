from footballprediction.util import read_file


def test_read_file():
    assert read_file("tests/test.sql") == "INSERT INTO movie VALUES(?, ?, ?)"
