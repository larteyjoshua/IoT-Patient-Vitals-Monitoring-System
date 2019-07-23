"""
This module creates sqlite database 

"""


import sqlite3
import random
import datetime
import time

con = sqlite3.connect('iot_wqms_data.db')
# con = sqlite3.connect(':memory:') # when db locks
cursor = con.cursor()

def create_table():

        cursor.execute(
                """ CREATE TABLE IF NOT EXISTS iot_wqms_table( 
                        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                        Time TIMESdTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                        temperature REAL, 
                        turbidity REAL,
                        ph REAL) """)
                        
        print('...inside create db fxn') 

# if not included, creates only DB without any table    
create_table()

def create_user():

        cursor.execute(
                """ CREATE TABLE IF NOT EXISTS users( 
                        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                        name text NOT NULL, 
                        email text NOT NULL,
                        ml_number text NOT NULL,
                        password text NOT NULL) """)
                        
        print('...inside create db fxn') 

# if not included, creates only DB without any table    
create_user()

