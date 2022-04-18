INSERT INTO test
SET
    idx = %(index)s,
    num = %(value)s,
    transformed = %(transformed)s
ON DUPLICATE KEY UPDATE
    num = %(value)s,
    transformed = %(transformed)s