# coding=utf-8 

import argparse
from queue import Queue
import pandas as pd
import numpy as np
import multiprocessing as mp
import os
import time
import threading

class Testing():
    def __init__(self):
        self.data = dict()
        data_simulator = np.arange(1, 5).reshape((1, 4))
        self.data_df_simulator = pd.DataFrame(data_simulator)
        self.data_df_simulator.columns = ['index', 'tag', 'ppid', 'pid']
        self.data_df_simulator = self.data_df_simulator.set_index(['index'])

    def f_method(self, thread_list):
        for i in range(5):
            self.data[i+1] = mp.Manager().dict()
            p = mp.Process(target=self.s_method, args=(i+1,))
            thread_list.append(p)

        # print(cc,"\n\n")

    def s_method(self, index):
        # data = dict()
        
        time.sleep(10)
        self.data[index]["tag"] = "ASD"
        self.data[index]["ppid"] = os.getppid()
        self.data[index]["pid"] = os.getpid()
        print(self.data[index])
        # print(self.data)

    def processing_start(self, t_l):
        for i in t_l:
            i.start()

        for i in t_l:
            i.join()  
        
    
    def updata_df(self):
        for i in self.data.keys():
            self.data_df_simulator.loc[i, "tag"] = self.data[i]["tag"]
            self.data_df_simulator.loc[i, "ppid"] = self.data[i]["ppid"]
            self.data_df_simulator.loc[i, "pid"] = self.data[i]["pid"]

        

if __name__ == '__main__':
    # info('main line')
    
    atc = Testing()
    s = time.time()
    t_l = []

    atc.f_method(t_l)

    for i in t_l:
        i.start()

    for i in t_l:
        i.join()  
    
    atc.updata_df()
    # data = dict()
    # for index in range(1,6):
        
    #     data[index] = {}
    #     # time.sleep(10)
    #     data[index]["tag"] = "ASD"
    #     data[index]["ppid"] = os.getppid()
    #     data[index]["pid"] = os.getpid()
    e = time.time()
    print(e-s)

    # print(data)
    print(atc.data_df_simulator[:])