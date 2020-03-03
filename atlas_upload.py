import pyodbc
from rq import Queue
from rq import get_current_job
from redis import Redis
from time import sleep

def upload_to_db(data):
    redis_conn=Redis()
    q=Queue('atlas',connection=redis_conn,default_timeout=300)
    conn = pyodbc.connect(driver='{FreeTDS}',
                      server='161.253.78.140',
                      port='1433',
                      database='capstone',
                      uid='SA',
                      pwd='Capstone2020!')
    cursor=conn.cursor()
    
    tval=str(data.values()[0])
    phval=float(data.values()[1])
    condval=float(data.values()[2])
    tempval=data.values()[3]
    humval=data.values()[4]
    cursor.execute('INSERT INTO capstone.testing.example (Timestamp,pH,Cond,Temp,Hum) VALUES (?,?,?,?,?)', tval,phval,condval,tempval,humval)
    conn.commit()
    return
