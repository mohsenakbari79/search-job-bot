import psycopg2
# # add user in database

# connection = psycopg2.connect(
#             database=config('DATABASE_NAME'),
#             user=config('USER_DB'),
#             password=config('PASSWORD_DB'),
#             host=config('HOST_DB'),
#             port=config("PORT_DB")
#         )
import urllib.parse as urlparse
import os


connection = psycopg2.connect(
            database=config('DATABASE_NAME'),
            user=config('USER_DB'),
            password=config('PASSWORD_DB'),
            host=config('HOST_DB'),
            port=config("PORT_DB")
            )

cur = connection.cursor()
print("true")

try:
    cur.execute("""
        CREATE TABLE botuser(
        username VARCHAR(50) PRIMARY KEY,
        count_filter INT DEFAULT 0,
        chat_id VARCHAR(100) NOT NULL,
        firstname VARCHAR(100),
        lastname VARCHAR(100)
        constraint valid_number 
            check ( 0 <= count_filter )
            check (  count_filter <= 10 )

        );

        CREATE TABLE IdPost(
            onerow_id bool PRIMARY KEY DEFAULT TRUE,
            chat_id VARCHAR(100) NOT NULL
        );
        CREATE TABLE jobinja(
        username VARCHAR(50) PRIMARY KEY,
        job VARCHAR(100) NOT NULL,
        city VARCHAR(100) NOT NULL
        );
        CREATE TABLE botuser_filter(
        username VARCHAR(50) ,
        count_filter INT,
        filter VARCHAR(50) NOT NULL,
        PRIMARY KEY (username,count_filter),
        constraint valid_number 
            check ( 0 <= count_filter ),
            check ( count_filter <= 9 )
        );

        """)
except:
    connection.rollback()
finally:
    connection.commit()
    print("Inserting to database succeeded...")
    connection.close()
