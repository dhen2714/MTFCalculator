CREATE_TABLE = """ CREATE TABLE edges (
    fpath text,
    name text,
    manufacturer text,
    mode text,
    orientation text,
    frequency text,
    left text,
    right text,
    top text,
    bottom text,
    processed integer,
    PRIMARY KEY (fpath, name)
); """

INSERT_ROWS = """ INSERT INTO edges
    (fpath, name, manufacturer, mode, orientation, frequency, left, right, top, bottom, processed)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?); """

DELETE_ALL = """DELETE FROM edges;"""

UPDATE_MTF_VALUES = """ UPDATE edges SET
    manufacturer = ?,
    mode = ?,
    orientation = ?,
    frequency = ?,
    left = ?,
    right = ?,
    top = ?,
    bottom = ?,
    processed = 1
    WHERE fpath = ?;"""

SELECT_PROCESSED = """SELECT * FROM edges WHERE processed = 1"""
