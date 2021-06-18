import time
from functools import wraps

## For the other .pys ##
import asyncio
import sys, os, csv, time, json
import numpy as np
import subprocess as sp
import matplotlib
import matplotlib.pyplot as plt


############### GOOD TIMES ###############
PROF_DATA = {}

def profile(fn):
    @wraps(fn)
    def with_profiling(*args, **kwargs):
        start_time = time.time()

        ret = fn(*args, **kwargs)

        elapsed_time = time.time() - start_time

        if fn.__name__ not in PROF_DATA:
            PROF_DATA[fn.__name__] = [0, []]
        PROF_DATA[fn.__name__][0] += 1
        PROF_DATA[fn.__name__][1].append(elapsed_time)

        return ret

    return with_profiling

def print_prof_data():
    for fname, data in PROF_DATA.items():
        max_time = max(data[1])
        avg_time = sum(data[1]) / len(data[1])
        print("Function %s called %d times. " % (fname, data[0]),)
        print('Execution time max: %.3f, average: %.3f' % (max_time, avg_time))

def clear_prof_data():
    global PROF_DATA
    PROF_DATA = {}


@profile
def good_times():
    current_time = time.localtime(time.time())
    tm_year  = str(current_time[0]-2000)
    tm_month = current_time[1]
    tm_mday  = current_time[2]
    tm_hour  = current_time[3]
    tm_min   = current_time[4]
    tm_sec   = current_time[5]

    if tm_month < 10:
        tm_month = str(0) + str(tm_month)
    else:
        tm_month = str(tm_month)

    if tm_mday < 10:
        tm_mday = str(0) + str(tm_mday)
    else:
        tm_mday = str(tm_mday)

    if tm_hour < 10:
        tm_hour = str(0) + str(tm_hour)
    else:
        tm_hour = str(tm_hour)

    if tm_min < 10:
        tm_min = str(0) + str(tm_min)
    else:
        tm_min = str(tm_min)

    if tm_sec < 10:
        tm_sec = str(0) + str(tm_sec)
    else:
        tm_sec = str(tm_min)

    return f'{tm_year}{tm_month}{tm_mday}-{tm_hour}{tm_min}{tm_sec}'

