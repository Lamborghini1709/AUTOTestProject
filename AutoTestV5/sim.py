# coding=utf-8
#!/usr/bin/env python

from init_p import AutoTestCls
import os
import time
import multiprocessing as mp

class Simulator(AutoTestCls):
    def __init__(self, opt):
        super(Simulator, self).__init__(opt)
        thread_list = []
        self.sim_folder(thread_list)

        for t in thread_list:
            t.start()
            time.sleep(1)

        for t in thread_list:
            t.join() 

    def run_simulation_g(self, netfileID):
        netfile = self.data_df_simulator.loc[netfileID].netFile

        if netfile:
            # RunCmd = ['simulator',spfile]
            logfile = self.data_df_simulator.loc[netfileID].logFile
            # changed 0904 >> to >为了每次重新仿真得到的log不会记录之前的结果，
            # 否则autoRun.log的自动判断会出错
            # 执行仿真并记录仿真时间
            if "case13/transient_analysis/hao_testx0_post2.sp" in netfile :
                RunCmd = self.sh + " {} -f nutascii > {}".format(netfile, logfile)
            else:
                RunCmd = self.sh + " {} -f nutascii -m4 > {}".format(netfile, logfile)
            start = time.time()
            os.system(RunCmd)
            end = time.time()
            print("INFO RUN cmd: {}".format(RunCmd))
            cost = int((end - start) * 1000) / 1000

            self.sim_data[netfileID]["Simulatorcost"] = cost
            # self.data_df_simulator.loc[netfileID, "Simulatorcost"] = cost
            # self.data_df_diff.loc[netfileID, "Simulatorcost"] = cost


    # 执行仿真
    def sim_folder(self,thread_list):
        for index in range(1, self.spfile_Num + 1):
            self.sim_data[index] = mp.Manager().dict()
            # 找case对应的bench文件结果
            ref_file = self.data_df_diff.loc[index].RefoutFile
            if not os.path.exists(ref_file):
                self.data_df_diff.loc[index, "RefoutFile"] = None
                self.data_df_diff.loc[index, "RefoutFile"] = None
            # 执行仿真
            t1 = mp.Process(target=self.run_simulation_g, args=(index,), daemon=True)
            thread_list.append(t1)

