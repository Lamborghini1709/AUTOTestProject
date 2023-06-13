# coding=utf-8
#!/usr/bin/env python

import datetime
import os
import time
import pandas as pd
import numpy as np
import collections
from calc_utils import get_rmse, get_mape, AlignDataLen, max_diff, cos_sim
import multiprocessing as mp
import sys
from tools_utils import change_suffix
from sql_utils import DBConnect


class AutoTestCls():
    # 定义、创建对象初始化
    def __init__(self, opt):
        # 最小阈值
        self.min_threshold = 1e-14
        self.spfile_Num = 0
        self.isdelold = opt.isdelold
        self.iscpset = opt.iscpset
        self.outputpath = opt.outputpath
        self.sh = opt.execufilename
        self.version = opt.btdversion # TODO(待优化)
        self.savefig = opt.savefig
        self.metric = opt.metric
        self.casename = opt.casename
        self.testset = opt.testset
        self.ref_filename = "bench"
        self.test_dir = os.path.join(self.outputpath, "V5_Regress")
        self.output_folder = os.path.join(self.test_dir, "output")
        self.check_nodes_dict = dict()
        
        # 父进程与子进程的共享数据
        self.sim_data = dict()
        self.diff_data = dict()

        # def dataform1
        data_simulator = np.arange(1, 8).reshape((1, 7))
        self.data_df_simulator = pd.DataFrame(data_simulator)
        self.data_df_simulator.columns = ['index', 'caseN', 'netFile', 'logFile', 'outFile', 'SimulatorStat', 'Simulatorcost']
        self.data_df_simulator = self.data_df_simulator.set_index(['index'])

        # def dataform2
        data_df_diff = np.arange(1, 18).reshape((1, 17))
        self.data_df_diff = pd.DataFrame(data_df_diff)
        self.data_df_diff.columns = ['index', 'caseN', 'spFile', 'logFile', 'outFile', 'RefoutFile', 'ReflogFile','AnalysisType',
                                     'SimulatorStat', 'Simulatorcost', "time_div", "cost_div","cputime_rate","walltime_rate",
                                     "outdiff", "outdiffCost", "outdiffdetail"]
        self.data_df_diff = self.data_df_diff.set_index(['index'])

        self.InitCaseForm()

    def InitCaseForm(self):
        con = DBConnect("10.1.10.13", 5555, "AutoTest", "Test@123456", "AutoTest")
        sql = "SELECT * FROM caseInfos "
        if self.casename == "": 
            if self.testset == None:
                conditions = "1234"
            else:
                cond_dict = {}
                for c in self.testset:
                    kv = c.split(",")
                    if kv[0] in cond_dict.keys():
                        try:
                            cond_dict[kv[0]].append(kv[1])
                        except:
                            cond_dict[kv[0]] = [cond_dict[kv[0]], kv[1]]
                    else:
                        cond_dict[kv[0]] = kv[1]
                conditions = " WHERE "
                for k in cond_dict.keys():
                    if type(cond_dict[k]) == str:
                        conditions += f"FIND_IN_SET('{cond_dict[k]}', {k}) AND "
                    else:
                        data = ""
                        for v in cond_dict[k]:
                            data += f"FIND_IN_SET('{v}', {k}) OR "
                        conditions += f"({data[0:-4]}) AND "
        else:
            conditions = f" WHERE CaseName IN {tuple(self.casename)}1234"

        f_sql = sql + conditions[0:-4] + " ORDER BY id"
        data = con.query_d(f_sql)

        # 仿真结果
        SimulatorStat = 0
        # 仿真时间
        Simulatorcost = None
        # 仿真类型
        AnalysisType = None
        # diff result
        Simulatordiff = None
        # diff result detail
        outdiffdetail = {}

        time_div = None
        cost_div = None
        outdiffCost = None
        cputime_rate = None
        walltime_rate =None

        cp_list = []
        for row in data:
            self.spfile_Num += 1
            netfile = row["Netlist"]
            logFile = change_suffix(netfile, ".log")
            outFile = self.change_suffix(netfile, '.out')
            caseN = row["CaseName"]
            ref_path = os.path.join(os.path.dirname(outFile), self.ref_filename)
            ref_file = os.path.join(ref_path, os.path.basename(outFile))
            ref_log = os.path.join(ref_path,os.path.basename(logFile))

            self.data_df_simulator.loc[self.spfile_Num] = [
                caseN, netfile, logFile, outFile, SimulatorStat, Simulatorcost
                ]

            self.data_df_diff.loc[self.spfile_Num] = [
                caseN, netfile, logFile, outFile, ref_file, ref_log, AnalysisType,
                SimulatorStat, Simulatorcost, time_div, cost_div, cputime_rate,
                walltime_rate, Simulatordiff,outdiffCost,outdiffdetail
                ]
            
            cp_list.append(row["id"])
            # 选择对比节点
            row_value = row["Nodes"].split(", ")
            self.check_nodes_dict[row["id"]] = row_value

        # 删除tp目录下的测试集
        if self.isdelold is True:
            self.del_case_dir()
        
        if self.iscpset is True:
            self.cp_test_set(cp_list)

        # def logfile
        os.makedirs(self.output_folder, exist_ok=True)
        self.autoRunlogfile = open(f"{self.output_folder}/autoRun.log", "a")
        now = datetime.datetime.now()
        self.autoRunlogfile.write(now.strftime("AutoTest Start %Y-%m-%d %H:%M:%S \n"))


    def cp_test_set(self, lis):
        initCmd = f"cp -r /home/mnt/V5_Regress/case{lis}  {self.test_dir}"
        print("INFO COPY CMD: "+initCmd)
        os.system(initCmd)


    def del_case_dir(self):
        delCmd = f"rm -rf {self.test_dir}"
        if os.path.exists(self.test_dir):
            print("INFO DEL CMD: "+delCmd)
            os.system(delCmd)


    def not_check_file_list(self, netfile):
        # netfile: /home/IC/Case_wayne/TestBench_1BaseCases1/>>>>>case1<<<<<</VCO/lab1_pss_pnoise_btd.scs
        caseindex = netfile.split('case')[1].split('/')[0]
        #测试打通阶段略略这些case
        if f"case{caseindex}" in self.not_check_case:
            return 1
        else:
            return 0

    def getCaseIndex(self, index):
        netfile = self.data_df_simulator.loc[index].netFile
        # print(netfile)
        # netfile: /home/IC/Case_wayne/TestBench_1BaseCases1/>>>>>case1<<<<<</VCO/lab1_pss_pnoise_btd.scs
        caseindex = netfile.split('case')[1].split('/')[0]
        # print(caseindex)
        return int(caseindex)