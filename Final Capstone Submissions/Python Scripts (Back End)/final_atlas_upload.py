'''
ECE4925W - Final Capstone Submission, Spring 2020
Phillip Jones, Connor Kraft, Rachel Zaltz
    
final_atlas - takes data, organizes storage structure, submits queue request for transportation to storage server
final_atlas_worker - takes resulting data and actually submits to queue
final_atlas_upload - submits data to sql database on storage server
    
For detailed questions on packages used / scripts, please see User Manual Appendix and the FPR, in general

This script is automatically called by the main application
'''

import pyodbc                       # Use to make Python connection to SQL Server on storage server
from rq import Queue                # Use to implement Redis queue actions
from rq import get_current_job      # Use to get information on submitted jobs
from redis import Redis             # Use to make Python connection to Redis server on RPi
from time import sleep              # Use to make program stop for period

def upload_to_db(data):
    redis_conn=Redis()
    q=Queue('atlas',connection=redis_conn,default_timeout=300)
    # The following information currently works with the provided server
    # Contact Mark Aglipay if you arrive with issues on the server / with the SQL Server application
    conn = pyodbc.connect(driver='{FreeTDS}',
                      server='X.X.X.X',
                      port='XXXX',
                      database='XXXX',
                      uid='XXXX',
                      pwd='XXXX!')
    cursor=conn.cursor()
    
    # Following data is taken from the constructed dictionary in final_atlas.py
    # Data is out of order, but submits to server in correct order, due to how the queueing orders the information
    # Sleep is used to reduce load on server between sensor readings / data commits
    tval=str(data.values()[3])
    phval=str(data.values()[4])
    condval=str(data.values()[5])
    tempval=str(data.values()[0])
    humval=str(data.values()[2])
    imgval=str(tval + '.png')
    expname=str(data.values()[1])
    cursor.execute('INSERT INTO XXXX.XXXX.XXXX (Timestamp,pH,Cond,Temp,Hum,img_name,exp_name) VALUES (?,?,?,?,?,?,?)', tval,phval,condval,tempval,humval,imgval,expname)
    conn.commit()
    sleep(5)
    return
