# coding=utf-8 

import argparse
from queue import Queue
import pandas as pd
import numpy as np
import multiprocessing as mp
import os
import time
import threading

def error_diff():
    file_name = r"D:\Ubuntu_IC618\share\eehemt\HBcase3\result\case3_pin10"
    f = open(file_name)
    content = f.readlines()
    btd_list = []
    ads_list = []
    spec_list = []

    for line in content:
        if line.startswith("COL_HEADERS"):
            pass
        else:
            data = line.replace("\n", '')
            data = data.split(' ')
            btd_list.append([eval(data[0]), eval(data[1])])
            ads_list.append([eval(data[2]), eval(data[3])])
            spec_list.append([eval(data[4]), eval(data[5])])

    print("*"*20 + f"{file_name}" + "*"*20)

    new_btd = sorted(btd_list, key=lambda x:x[0])
    new_ads = sorted(ads_list, key=lambda x:x[0])
    new_spec = sorted(spec_list, key=lambda x:x[0])

    for d in range(len(new_btd)):
        btd = abs(new_btd[d][1])
        ads = abs(new_ads[d][1])
        spec = abs(new_spec[d][1])
        try:
            btd_ads = abs((btd - ads)/ads)*100
            ads_spec = abs((ads - spec)/ads)*100
        except:
            btd_ads = 0
            ads_spec = 0
        print(f"freq={new_btd[d][0]}")
        print(f"btd & ads: ")
        print(f"ε1: {btd_ads}%")
        print(f"spec & ads: ")
        print(f"ε2: {ads_spec}%\n")

class Testing():
    def __init__(self):
        data_simulator = np.arange(1, 5).reshape((1, 4))
        self.data_df_simulator = pd.DataFrame(data_simulator)
        self.data_df_simulator.columns = ['index', 'tag', 'ppid', 'pid']
        self.data_df_simulator = self.data_df_simulator.set_index(['index'])

    def f_method(self, thread_list, queue):
        for i in range(5):
            p = mp.Process(target=self.s_method, args=(i+1, queue,))
            thread_list.append(p)

        # print(cc,"\n\n")

    
    def s_method(self, index, queue):
        data = dict()
        data[index] = {}
        # time.sleep(10)
        data[index]["tag"] = "ASD"
        data[index]["ppid"] = os.getppid()
        data[index]["pid"] = os.getpid()
        queue.put(data)
        # print(data)

    def processing_start(self, t_l, queue):
        fd = dict()
        for i in t_l:
            i.start()
        data = queue.get()
        print(data)
        for i in t_l:
            i.join()  
        
        return fd
    
    def updata_df(self, fd):
        for i in range(len(fd)):
            self.data_df_simulator.loc[i+1, "tag"] = fd[i+1]["tag"]
            self.data_df_simulator.loc[i+1, "ppid"] = fd[i+1]["ppid"]
            self.data_df_simulator.loc[i+1, "pid"] = fd[i+1]["pid"]

        

if __name__ == '__main__':
    # info('main line')
    
    atc = Testing()
    s = time.time()
    t_l = []
    queue = mp.Queue()
    atc.f_method(t_l, queue)
    fd = atc.processing_start(t_l, queue)
    # atc.updata_df(fd)
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
    # print(atc.data_df_simulator[:])

