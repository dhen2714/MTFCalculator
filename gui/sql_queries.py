CREATE_TABLE = """ CREATE TABLE edges (
    fpath text,
    name text,
    left text,
    right text,
    top text,
    bottom text,
    processed integer,
    PRIMARY KEY (fpath, name)
); """

INSERT_ROWS = """ INSERT INTO edges
    (fpath, name, left, right, top, bottom, processed)
    VALUES (?, ?, ?, ?, ?, ?, ?); """

DELETE_ALL = """DELETE FROM edges;"""
