#!/usr/bin/env python3
# coding:utf8

import sys
import multiprocessing
import subprocess
from concurrent.futures import ThreadPoolExecutor

def run(arg):
    print("starting %s" % arg)
    p = multiprocessing.Process(target=print, args=("running", arg))
    p.start()
    p.join()
    print("finished %s" % arg)


if __name__ == "__main__":
    n = 16
    tests = range(n)
    with ThreadPoolExecutor(n) as pool:
        for r in pool.map(run, tests):
            pass
