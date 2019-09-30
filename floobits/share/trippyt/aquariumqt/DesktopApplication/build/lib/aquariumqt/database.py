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
    database = r"dose_sch_database.db"
    # create a database connection
    conn = create_connection(database)

    # create tables
    if conn is not None:
        # create dosage_schedule table
        create_table(conn, sql_create_dosage_schedule)
    else:
        print("Error! cannot create the database connection.")


def create_dosage_schedule(conn, dosage_schedule):
    """
    Create a new task
    :param conn:
    :param dosage_schedule:
    :return:
    """

    sql = ''' INSERT INTO dosage_schedule(Setting,Date,Time,Repeat)
              VALUES(?,?,?,?) '''
    cur = conn.cursor()
    cur.execute(sql, dosage_schedule)
    return cur.lastrowid

def update_schedule(conn, schedule):
    """
    update priority, begin_date, and end date of a task
    :param conn:
    :param schedule:
    :return: project id
    """
    sql = ''' UPDATE schedule
              SET Setting = ? ,
              SET Date = ? ,
              SET Time = ? ,
              SET Repeat = ?'''
    cur = conn.cursor()
    cur.execute(sql, schedule)
    conn.commit()

if __name__ == '__main__':
    main()