import os
import sqlite3
from sqlite3 import Error

conn = sqlite3.connect("data.db")
c = conn.cursor()

def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)

    return conn

def main():
    currentDirectory = os.getcwd()
    database = r"data.db"
    # create tables
    if conn is not None:
        # create dosage_schedule table
        create_table(conn, sql_create_dosage_schedule)
    else:
        print("Error! cannot create the database connection.")