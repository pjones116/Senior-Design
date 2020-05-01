'''
ECE4925W - Final Capstone Submission, Spring 2020
Phillip Jones, Connor Kraft, Rachel Zaltz

final_atlas - takes data, organizes storage structure, submits queue request for transportation to storage server
final_atlas_worker - takes resulting data and actually submits to queue
final_atlas_upload - submits data to sql database on storage server
    
For detailed questions on packages used / scripts, please see User Manual Appendix and the FPR, in general

This program was provided entirely via the RQ setup guide

Launch Redis server first, type the following on cmd: "redis-server"

Launch with the following on cmd: "python final_atlas_worker.py atlas"

This names the queue that jobs will be submitted to

This script acts as middleman transport, can be left running at all times (script works automatically)
'''

import sys
from rq import Connection, Worker

with Connection():
    qs = sys.argv[1:] or ['default']
    w = Worker(qs)
    w.work()
