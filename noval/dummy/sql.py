

CREATE_USER_TABLE_SQL = '''
    CREATE TABLE user (
        id INTEGER primary key autoincrement,
        user_id varchar (24),
        user_name varchar (100),
        os_bit varchar (50),
        sn varchar (100),
        os varchar (260),
        phone varchar (100),
        email varchar (300),
        password text,
        version varchar (20),
        created_time datetime default (datetime('now', 'localtime'))
    )
'''

CREATE_USER_DATA_TABLE_SQL = '''
    CREATE TABLE data (
        id INTEGER primary key autoincrement,
        user_id int,
        app_version varchar (100),
        submited BOOLEAN default 0,
        start_time datetime default (datetime('now', 'localtime')),
        end_time datetime
    )
'''