# -*- coding: utf-8 -*-
# @Time    : 2021/9/8 11:13
# @Author  : Wayne
# @File    : autotestcls.py
# @Software: PyCharm
import argparse
import datetime
import os
import time
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
import collections
from tool_utils import get_rmse, get_mape, AlignDataLen, max_diff, cos_sim
import multiprocessing as mp
import sys


class AutoTestCls():
    # 定义、创建对象初始化
    def __init__(self, opt):
        # 最小阈值
        self.min_threshold = 1e-14
        self.spfile_Num = 0
        self.sh = opt.sh
        self.exsign = opt.si
        self.version = opt.bv
        self.dir_dict = {
            "all": "All_regress_Cases",
            "hisi": "hisiCaseAll",
            "huali": "regress_Cases_all-cmg-bulk_20230307-1400",
            "hbt": "hbt_regression",
            "K3": "K3_regression",
            "XVA": "XVA_pin_current_regression",
            "bbd_small": "bbd_small_Cases",
            "bbd_large": "bbd_large_Cases",
            "0": "All_regress_Cases",
            "1": "hisiCaseAll",
            "2": "regress_Cases_all-cmg-bulk_20230307-1400",
            "3": "RegressCasesCircuitLimit5K_20230330-1000",
            "4": "cmg_regress_Cases_version-107_20220909",
            "5": "cmg_regress_Cases_version-110.0_20220705",
            "6": "bulk_regress_Cases_version-106.2_20220824",
            "7": "regress_Cases_bulk107_2022-11-30",
            "8": "haisiRegre",
            "9": "radioCircuit", 
            "10": "huali_Case_regress_20221015",
            "11": "regress_Cases_all-cmg-bulk_20221202-1600",
            "12": "cmg_regress_Cases_version-106.1_20230201",
            "13": "hisiCaseAll_part2",
            "14": "regress_Cases_all-cmg-bulk_20230307-1400_part2"
        }
        self.test_dir = os.path.join(opt.tp, self.dir_dict[opt.rp])
        self.ref_filename = 'bench'
        self.cases_nodes_path = os.path.join(self.test_dir, "cases_nodes.xlsx")
        self.output_folder = os.path.join(self.test_dir, "output")
        self.case_dir = os.path.join(self.test_dir, opt.cn)
        # 父进程与子进程的共享数据
        self.sim_data = dict()
        self.diff_data = dict()

        # 需要跳过不进行测试的case
        self.not_check_case = ["case999"]

        # 回归测试集初始化
        # 删除tp目录下的测试集
        if opt.isdelold == 1:
            self.del_case_dir()
        else:
            pass
        initCmd = f"cp -r /home/mnt/BTD/{self.dir_dict[opt.rp]}  {opt.tp}"
        print("INFO COPY CMD: "+initCmd)
        os.system(initCmd)

        # def logfile
        os.makedirs(self.output_folder, exist_ok=True)
        self.autoRunlogfile = open(f"{self.output_folder}/autoRun.log", "a")
        now = datetime.datetime.now()
        self.autoRunlogfile.write(now.strftime("AutoTest Start %Y-%m-%d %H:%M:%S \n"))

        # def result_statistics
        self.rs = open(os.path.join(opt.tp, "result_statistics.log"), "a+")
        self.rs.write(f"""\n---------------------------------------------------------分隔符---------------------------------------------------------
# AutoTest V5 result statistics {now.strftime("%Y-%m-%d %H:%M:%S")}""")

        # def dataform1
        data_simulator = np.arange(1, 7).reshape((1, 6))
        self.data_df_simulator = pd.DataFrame(data_simulator)
        self.data_df_simulator.columns = ['index', 'netFile', 'logFile', 'outFile', 'SimulatorStat', 'Simulatorcost']
        self.data_df_simulator = self.data_df_simulator.set_index(['index'])

        # def dataform2
        data_df_diff = np.arange(1, 16).reshape((1, 15))
        self.data_df_diff = pd.DataFrame(data_df_diff)
        self.data_df_diff.columns = ['index', 'spFile', 'logFile', 'outFile', 'RefoutFile', 'ReflogFile','AnalysisType',
                                     'SimulatorStat', 'Simulatorcost', "time_div","cputime_rate","walltime_rate",
                                     "outdiff", "outdiffCost", "outdiffdetail"]
        self.data_df_diff = self.data_df_diff.set_index(['index'])

        # 判断是否为可执行网表文件
        self.is_netlist = lambda x: any(x.endswith(extension)
                                        for extension in ['.sp', '.cir', 'scs'])

        # 选择对比节点
        self.check_nodes_dict = dict()
        self.check_time_dict = dict()
        self.case_limit = dict()
        nodes_df = pd.read_excel(self.cases_nodes_path, index_col=0)  # 指定第一列为行索引
        for row in list(nodes_df.index):
            row_value = nodes_df.loc[row, 'nodes'].split(", ")
            self.check_nodes_dict[row] = row_value
            limit_value = nodes_df.loc[row, 'limits']
            self.case_limit[row] = limit_value
            if opt.ccost == 1:
                time_value = nodes_df.loc[row, 'times']
                self.check_time_dict[row] = time_value
            if pd.isna(limit_value):
                pass
            else:
                self.case_limit[row] = limit_value

        self.InitCaseForm()

    def InitCaseForm(self):
        if isinstance(self.case_dir, str):
            # 遍历目录下的所有文件
            for filepath, dirnames, filenames in os.walk(self.case_dir, topdown=False):
                for filename in filenames:
                    if self.is_netlist(filename):
                        # sp文件
                        netfile = os.path.join(filepath, filename)
                        if 'model' in netfile or 'gpdk' in netfile or 'INCLUDE' in netfile or 'SpectreModels' in netfile:
                            continue
                        ret = self.not_check_file_list(netfile)
                        caseindex = netfile.split('case')[1].split('/')[0]
                        if(ret == 1):
                            continue
                        if self.exsign == "huali" and int(caseindex) >=1000:
                            continue
                        elif self.exsign == "hisi" and int(caseindex) <=1000:
                            continue
                        self.spfile_Num += 1

                        # log文件
                        logFile = self.change_suffix(netfile, '.log')

                        # 仿真结果
                        SimulatorStat = 0
                        # 仿真时间
                        Simulatorcost = None
                        # 仿真类型
                        AnalysisType = None

                        # 仿真sp得到的out文件
                        outFile = self.change_suffix(netfile, '.out')

                        # 需要对比的out文件
                        ref_path = os.path.join(os.path.dirname(outFile), self.ref_filename)
                        ref_file = os.path.join(ref_path, os.path.basename(outFile))
                        ref_log = os.path.join(ref_path,os.path.basename(logFile))

                        # diff result
                        Simulatordiff = None

                        # diff result detail
                        outdiffdetail = {}
                        
                        # diff time_div
                        time_div = None
                        outdiffCost = None
                        cputime_rate = None
                        walltime_rate =None

                        self.data_df_simulator.loc[self.spfile_Num] = [netfile, logFile, outFile, SimulatorStat,
                                                                       Simulatorcost]

                        self.data_df_diff.loc[self.spfile_Num] = [netfile, logFile, outFile, ref_file, ref_log, AnalysisType,
                                                                  SimulatorStat, Simulatorcost, time_div, cputime_rate,
                                                                  walltime_rate, Simulatordiff,outdiffCost,outdiffdetail]
        else:
            print("Please specify the test folder in string format.")


    def del_case_dir(self):
        case_dir = f"{opt.tp}/{self.dir_dict[opt.rp]}"
        delCmd = f"rm -rf {case_dir}"
        if os.path.exists(case_dir):
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

    # 修改文件后缀
    def change_suffix(self, file, suffix):
        if file.endswith('.sp'):
            file = file.replace('.sp', suffix)
        elif file.endswith('.cir'):
            file = file.replace('.cir', suffix)
        elif file.endswith('.scs'):
            file = file.replace('.scs', suffix)
        else:
            pass
        return file

    def global_log_check(self):
        for id in range(1, self.spfile_Num + 1):
            spfile = self.data_df_simulator.loc[id].netFile
            logfile = self.data_df_simulator.loc[id].logFile
            if logfile:
                caseindex = self.getCaseIndex(id)
                tag = self.case_limit[caseindex]
                if self.version == "base":
                    if tag == "base" or tag == "plus":
                        stat = self.limit_logfile_check(logfile)
                    else:
                        stat, wall_time = self.logfile_check(logfile)
                elif self.version == "plus":
                    if tag == "plus":
                        stat = self.limit_logfile_check(logfile)
                    else:
                        stat, wall_time = self.logfile_check(logfile)
                else: 
                    stat, wall_time = self.logfile_check(logfile)
              
                # print("stat: {}".format(stat))
                if stat:
                    SimulatorStat = 1
                    # self.get_time(id)
                    self.autoRunlogfile.write(' '.join([spfile, 'YES', wall_time]))
                else:
                    SimulatorStat = 0
                    self.data_df_simulator.loc[id, "Simulatorcost"] = None
                    self.data_df_diff.loc[id, "Simulatorcost"] = None
                    self.autoRunlogfile.write(' '.join([spfile, 'NO', wall_time]))
                self.data_df_simulator.loc[id, "SimulatorStat"] = SimulatorStat
                self.data_df_diff.loc[id, "SimulatorStat"] = SimulatorStat
            # print out_file;
        print("log file check is OK.")
        print("The result is in autoRun.log.")

    # def global_out_check(self):
    #     for id in range(1, self.spfile_Num+1):
    #         outfile = self.data_df_simulator.loc[id].outFile
    #         if os.path.exists(outfile):
    #             _, analysistypes = self.outfile_parser(outfile)
    #             if analysistypes:
    #                 self.data_df_simulator.loc[id, "AnalysisType"] = ";".join(analysistypes)
    #     print("outfile check is OK.")

    # changed 0902
    def logfile_check(self, file):
        if os.path.exists(file):
            try:
                f = open(file, "r", encoding='latin-1')
                content = f.readlines()
                for line in content:
                    if 'SIMULATION is completed successfully' in line:
                        return 1, content[-1]
            except:
                try:
                    f = open(file, "r")
                    content = f.readlines()
                    for line in content():
                        if 'SIMULATION is completed successfully' in line:
                            return 1, content[-1]
                except:
                    print("error decode:" + file)
        return 0, "parser log failed\n"

    def limit_logfile_check(self, file):
        if os.path.exists(file):
            try:
                with open(file) as f:
                    for line in f.readlines():
                        if 'This version is limited to' in line:
                            return 1
            except:
                try:
                    with open(file, encoding='latin-1') as f:
                        for line in f.readlines():
                            if 'This version is limited to' in line:
                                return 1
                except:
                    print("error decode:" + file)
        return 0

    def outfile_parser(self, file_name):
        fo = open(file_name, "r", encoding='latin-1')
        # def a list with nodes startwith "Title"
        nodelists = []
        # def a list with single node
        nodelist = []
        output_file = fo.readlines()
        notenum = 1
        plotname_arr = []

        for i, line in enumerate(output_file):
            if i != 0 and line.startswith('Title'):
                nodelists.append(nodelist)
                # print(nodelists)
                notenum += 1
                nodelist = []
                nodelist.append(line)
            elif line.startswith('#') or line.startswith(' \n'):
                pass
            else:
                nodelist.append(line)

        nodelists.append(nodelist)
        # print(nodelists)
        assert len(nodelists) == notenum
        nodelistsresult = collections.OrderedDict()
        # read the number of variables and number of points
        for titles in nodelists:
            number_of_variables = int(titles[4].split(':', 1)[1])
            plotname = titles[2].split(': ', 1)[-1].split('\n')[0]
            plotname_arr.append(plotname)
            # multi_plotname_result = list()
            if plotname not in nodelistsresult.keys():
                nodelistsresult[plotname] = list()

            # read the names of the variables
            variable_name_unit = []
            for variable in titles[8:8 + number_of_variables]:
                # 取节点名
                var_name = variable.split('\t', -1)[2]
                # 取节点单位
                var_unit = variable.split('\t', -1)[3].split('\n')[0]
                # 节点名和单位之间用----拼接，赋给variable_name_unit
                var_name_unit = var_name + "----" + var_unit
                variable_name_unit.append(var_name_unit)
            # print(variable_name_unit)

            # read the values of the variables
            results = collections.OrderedDict()
            variable_index = 0
            for variable in variable_name_unit:
                results[variable] = []

            # if this node is PSS
            # if titles[2].split(': ')[-1] in ["Oscillator Steady State Analysis", "Periodic Steady State Analysis"]:
            #     results["PSS"] = "PSSvalue "
            # else:
            #     results["PSS"] = "value "

            for value in titles[8 + number_of_variables + 1:]:
                if variable_index != number_of_variables - 1:
                    # print(variable_index)
                    # print(variable_name[variable_index])
                    st = value.split('\t', -1)[-1]
                    if st.startswith("FAIL"):
                        st = "0"
                    try:
                        vlu = eval(st)
                    except:
                        st = value.split(' ', -1)[-1]
                    vlu = eval(st)
                    # 如果是虚数，out文件中会有两个值，我们只取实部
                    # if type(vlu) == tuple:
                    #     results[variable_name_unit[variable_index]].append(vlu[0])
                    # 如果是虚数，out文件中会有两个值，我们取abs

                    if type(vlu) == tuple:
                        vlu_abs = abs(complex(vlu[0], vlu[1]))
                        if vlu_abs < self.min_threshold:
                            results[variable_name_unit[variable_index]].append(0)
                        else:
                            results[variable_name_unit[variable_index]].append(vlu_abs)
                    else:
                        if vlu < self.min_threshold:
                            results[variable_name_unit[variable_index]].append(0)
                        else: 
                            results[variable_name_unit[variable_index]].append(vlu)
                    variable_index += 1
                else:
                    st = value.split('\t', -1)[-1].split('\n')[0]

                    # 如果out文件中出现Fail字符串，将其转换成0
                    if st.startswith("FAIL"):
                        st = "0"
                    vlu = eval(st)
                    if type(vlu) == tuple:
                        if vlu[0] < self.min_threshold:
                            results[variable_name_unit[variable_index]].append(0)
                        else:
                            results[variable_name_unit[variable_index]].append(vlu[0])
                    else:
                        if vlu < self.min_threshold:
                            results[variable_name_unit[variable_index]].append(0)
                        else: 
                            results[variable_name_unit[variable_index]].append(vlu)
                    variable_index = 0
            # multi_plotname_result.append(results)
            nodelistsresult[plotname].append(results)
            # nodelistsresult[plotname] = results
            # print("FINAL result: {}".format(nodelistsresult))
        # close the output_file
        fo.close()

        assert len(nodelistsresult) > 0
        return nodelistsresult, plotname_arr

    # 根据netlist name 获取 caseindex,后续根据caseindex去找对应的输出节点
    def getCaseIndex(self, index):
        netfile = self.data_df_simulator.loc[index].netFile
        # print(netfile)
        # netfile: /home/IC/Case_wayne/TestBench_1BaseCases1/>>>>>case1<<<<<</VCO/lab1_pss_pnoise_btd.scs
        caseindex = netfile.split('case')[1].split('/')[0]
        # print(caseindex)
        return int(caseindex)

    # cost 获得的time的比较 只对仿真时间大于 100S 的进行比较
    # def time_divcheck(self):
    #     for id in range(1,self.spfile_Num+1):
    #         if self.data_df_diff.loc[id].SimulatorStat:
    #             simulator_cost = self.data_df_diff.loc[id, "Simulatorcost"]
    #             caseindex = self.getCaseIndex(id)
    #             stand_cost = self.check_time_dict[caseindex]
    #             if float(simulator_cost) >= 100:
    #                 diff_cost = (simulator_cost - stand_cost)/ stand_cost *100
    #                 tag = self.case_limit[caseindex]
    #                 self.data_df_diff.loc[id,"cost_div"] = '%.3f'%diff_cost+"%"
    #                 if diff_cost<= 20 :
    #                     self.data_df_diff.loc[id,"time_div"] = 1                  
    #                 elif diff_cost>20:
    #                     if self.version == "base":
    #                         if tag == "base" or tag == "plus":
    #                             continue
    #                         else:
    #                             self.data_df_diff.loc[id, "time_div"] = 0
    #                     elif self.version == "plus":
    #                         if tag == "plus":
    #                             continue
    #                         else:
    #                             self.data_df_diff.loc[id, "time_div"] = 0
    #                     else:
    #                         self.data_df_diff.loc[id, "time_div"] = 0
    #             else:
    #                 self.data_df_diff.loc[id,"time_div"] = 1

    # 从 log 里获取 CPU_time 和 Wall_time
    def get_logtime(self,fp):
        log_time = {}
        try:
            f = open(fp, "r", encoding='latin-1')
            content = f.readlines()
            for line in range(0,len(content)):
                if content[line].startswith("Total CPU time(s):"):
                    CPU_time = content[line].split(":")[-1]
                    log_time["CPU_time"] = CPU_time
                elif content[line].startswith("Total Wall time(s):"):
                    Wall_time = content[line].split(":")[-1]
                    log_time["Wall_time"] = Wall_time
            return log_time
        except:
            return "NOTBENCH"

    # 当前log 文件 CPU_time / Wall_time 和 bench 文件夹中 log 文件 CPU_time / Wall_time 的比率
    # （只对仿真时间超过 100s 的进行比较）
    def diff_logtime(self):
        for id in range(1,self.spfile_Num+1):
            caseN = self.data_df_diff.loc[id, "spFile"]
            fp1 = self.data_df_diff.loc[id, "logFile"]
            fp2 = self.data_df_diff.loc[id, "ReflogFile"]
            logtime = self.get_logtime(fp1)
            golden_logtime = self.get_logtime(fp2)
            log_cputime = float(logtime["CPU_time"])
            log_walltime = float(logtime["Wall_time"])
            if golden_logtime=="NOTBENCH":
                print(f"{caseN}: 缺少bench log文件, 跳过时间对比")
                self.data_df_diff.loc[id,"time_div"] = "NOTDIFF"
            else:
                golden_cputime = float(golden_logtime["CPU_time"])
                golden_walltime = float(golden_logtime["Wall_time"])
                if log_walltime > 100:
                    cputime_rate = (log_cputime - golden_cputime) / golden_cputime *100
                    walltime_rate = (log_walltime - golden_walltime) / golden_walltime *100
                    self.data_df_diff.loc[id,"cputime_rate"] = '%.3f'%cputime_rate+"%"
                    self.data_df_diff.loc[id,"walltime_rate"] = '%.3f'%walltime_rate+"%"
                    tag = self.case_limit[id]
                    if walltime_rate<= 20 :
                        self.data_df_diff.loc[id,"time_div"] = 1                  
                    elif walltime_rate>20:
                        if self.version == "base":
                            if tag == "base" or tag == "plus":
                                continue
                            else:
                                self.data_df_diff.loc[id, "time_div"] = 0
                        elif self.version == "plus":
                            if tag == "plus":
                                continue
                            else:
                                self.data_df_diff.loc[id, "time_div"] = 0
                        else:
                            self.data_df_diff.loc[id, "time_div"] = 0
                else:
                    self.data_df_diff.loc[id,"time_div"] = "NOTDIFF"


    def calc_error(self, index, original_results_dict, new_results_dict):

        plotname_nodes = []
        plotnames = set()
        # 获取所有的plotnames
        for item in original_results_dict:
            # print(item)
            plotnames.add(item)
        print("Total plotnames: {}".format(plotnames))
        # print("Original_results_dict: {}".format(original_results_dict))

        for plotname in plotnames:
            # node_dict is a list of ordered dictionaries
            node_dict = original_results_dict[plotname]
            # print(type(node_dict))
            # 获取所有的nodename
            if type(node_dict) == list:
                nodes = node_dict[0].keys()
            else:
                print("node_dict type error.")
            for node in nodes:
                plotname_nodes.append('--'.join((plotname, node)))
                # print(plotname_nodes)

        # 读取case number，作为index找到对应case需要查看的节点
        caseindex = self.getCaseIndex(index)
        check_nodes = self.check_nodes_dict[caseindex]

        comp_result = {}
        comparelist = []
        for plotname_node in check_nodes:
            plotn = plotname_node.split('--')[0]
            noden = plotname_node.split('--')[1]
            # print(original_results_dict)
            # print("{}".format(plotn))
            out_plot = original_results_dict[plotn]
            # print(len(out_plot))
            ref_plot = new_results_dict[plotn]
            # print(ref_plot)
            if len(out_plot) != len(ref_plot):
                return False, 'length of out_plot and ref_plot not match,please check the outfile'

            for i in range(len(out_plot)):
                # 同名plotname情况下，第i个plotname中的所有nodes
                copy_out_plot = out_plot[i]
                # first one is x axis
                first_out = next(iter(copy_out_plot.values()))

                outx = first_out
                copy_ref_plot = ref_plot[i]
                first_ref = next(iter(copy_ref_plot.values()))
                refx = first_ref
                #
                # for xname_unit, xvalue in ref_plot[0].items():
                #     refx = xvalue
                #     break

                tag = 1
                for nodename in out_plot[i].keys():
                    if nodename.startswith(noden):
                        outdata = out_plot[i][nodename]
                        refdata = ref_plot[i][nodename]

                        # 对齐数据
                        if len(refdata) != len(outdata):
                            
                            x_value, outdata, refdata = AlignDataLen(outx, refx, outdata, refdata)
                            
                            if x_value is None:
                              return False, "AlignData Failed"

                        assert len(refdata) == len(outdata)

                        # 评估指标
                        if opt.metric == "RMSE":
                            metrix_value = get_rmse(outdata, refdata)
                        else:
                            metrix_value = get_mape(outdata, refdata)
                        cos_s = cos_sim(outdata, refdata)
                        comp_value = 3e-2
                        comp_value_cos = 1e-2
                        unit = nodename.split("----")[-1]
                        if unit=="A":
                            metrix_value2 = max_diff(outdata, refdata)
                            comp_value2 = 1e-9
                            compareflag1 = True if metrix_value <= comp_value else False
                            compareflag2 = True if metrix_value2 <= comp_value2 else False
                            compareflag3 = True if cos_s <= comp_value_cos else False
                            compareflag = compareflag1 | compareflag2 | compareflag3
                        elif unit=="V":
                            metrix_value2 = max_diff(outdata, refdata)
                            comp_value2 = 1e-4
                            compareflag1 = True if metrix_value <= comp_value else False
                            compareflag2 = True if metrix_value2 <= comp_value2 else False
                            compareflag3 = True if cos_s <= comp_value_cos else False
                            compareflag = compareflag1 | compareflag2 | compareflag3
                        else:
                            compareflag1 = True if metrix_value <= comp_value else False
                            compareflag3 = True if cos_s <= comp_value_cos else False
                            compareflag = compareflag1 | compareflag3
                        
                        if plotname_node in comp_result.keys():
                            if compareflag == False:
                                comp_result[plotname_node+"_"+str(tag)] = str((metrix_value, comp_value, compareflag))
                        else:
                            comp_result[plotname_node] = str((metrix_value, comp_value, compareflag))

                        comparelist.append(compareflag)
                        tag+=1

            compare = False if False in comparelist else True

        return compare, str(comp_result)

    def save_plot(self, index, out_results_dict, ref_results_dict, compare):
        # 根据对比结果定义标题颜色
        titlecolor = 'green' if compare else 'red'

        plotname_nodes = []
        # print("PART B: od {}".format(out_results_dict))
        plotnames = out_results_dict.keys()
        # print("PART B: {}".format(plotnames))

        for plotname in plotnames:
            node_dict = out_results_dict[plotname]
            # print("PART B: odkey already matched: {}".format(node_dict))
            code_node_dict = node_dict
            nodes = node_dict[0].keys()
            # print("PART B: nodes: {}".format(nodes))
            for node in nodes:
                plotname_nodes.append('--'.join((plotname, node)))
            # print("PART B: plotname and nodes: {}".format(plotname_nodes))

        # 读取case number，作为index找到对应case需要查看的节点
        caseindex = self.getCaseIndex(index)
        check_nodes = self.check_nodes_dict[caseindex]
        # print("PART B: check_nodes: {}".format(check_nodes))

        for plotname_node in check_nodes:
            plotn = plotname_node.split('--')[0]
            noden = plotname_node.split('--')[1]
            out_plot = out_results_dict[plotn]
            ref_plot = ref_results_dict[plotn]

            if len(out_plot) != len(ref_plot):
                continue

            for i in range(len(out_plot)):
                # print("current i: {}".format(i))
                x_info_key = list(out_plot[i].keys())[0]
                out_xname = x_info_key.split('----')[0]
                out_xunit = x_info_key.split('----')[1]
                outx = next(iter(out_plot[i].values()))
                refx = next(iter(ref_plot[i].values()))
                # print("out_xname: {}, out_xunit: {}, outx: {}, refx: {}".format(out_xname, out_xunit, outx, refx))

                for nodename in out_plot[i].keys():
                    # print("PART C: out_plot[i]: {}".format(out_plot[i]))
                    if nodename.startswith(noden):
                        # 得到y轴的单位
                        yunit = nodename.split("----")[1]
                        # 得到y轴的数据
                        outdata = out_plot[i][nodename]
                        refdata = ref_plot[i][nodename]
                        # print("PART C: yname: {}, yunit: {}".format(nodename, yunit))
                        # print("PART C: outdata: {}".format(outdata))
                        # print("PART C: refdata: {}".format(refdata))

                        # 长度不一致需做数据对齐
                        if len(refdata) != len(outdata):
                            xnew, outdata, refdata = AlignDataLen(outx, refx, outdata, refdata)
                            if xnew is None:
                              continue
                        else:
                            xnew = outx

                        assert len(refdata) == len(outdata)

                        if len(outdata) == 1:
                            continue

                        # 折线图还是柱状图
                        # print("Spectrum" in noden)
                        # print(noden)
                        # 如果是频谱图，画柱状图
                        # 同一个plotname的该节点的所有值，只画第一张和最后一张
                        if i == 0 or i == len(out_plot) - 1:
                            # print("PART D: current plot i: {}".format(i))
                            try:
                                if "Spectrum" in plotn:
                                    # 设置柱状图y轴的起始值
                                    bottomvalue = np.min(np.array(outdata)) - 10

                                    # GHz transform
                                    if np.max(xnew) > 1e9:
                                        xnew = (np.array(xnew) * 1e-9).tolist()
                                        out_xunit = "G" + out_xunit

                                    total_width, n = 0.6, 2
                                    width = total_width / n
                                    # fig = plt.figure()
                                    outdata = (np.array(outdata) + np.abs(bottomvalue)).tolist()
                                    refdata = (np.array(refdata) + np.abs(bottomvalue)).tolist()
                                    plt.bar(xnew, outdata, width=width, color='b', label='outdata', bottom=bottomvalue)
                                    # for a, b in zip(xnew, outdata):  # 柱子上的数字显示
                                    #     plt.text(a, b, '%.3f' % b, ha='center', va='bottom', fontsize=10);
                                    for j in range(len(xnew)):
                                        xnew[j] = xnew[j] + width
                                    plt.bar(xnew, refdata, width=width, color='r', label='refdata', bottom=bottomvalue)
                                    plt.xticks(rotation=90)  # 横坐标旋转45度
                                    plt.xlabel(out_xname + "(" + out_xunit + ")")  # 横坐标标签
                                    plt.ylabel(noden + "(" + yunit + ")")  # 纵坐标标签
                                    if i == 0:
                                        mark = "first"
                                    else:
                                        mark = "last"
                                    plt.title("{} {}".format(plotname_node, mark), backgroundcolor=titlecolor)  # bar图标题
                                    # plt.grid(axis='x')
                                    plt.legend(loc='best')
                                    savepath = f"{self.output_folder}/case{str(caseindex)}_{plotname_node} {mark}.jpg"
                                    plt.savefig(savepath)
                                    # plt.show()
                                    plt.close()

                                # 否则，画折线图
                                else:  # plot

                                    # GHz transform
                                    if "noise" in plotname_node or "Noise" in plotname_node:
                                        # log transform
                                        # if "noise" in noden or "Hz" in out_xunit:
                                        xnew = np.log10(xnew)
                                        out_xname = out_xname + "_log"
                                    else:
                                        if np.max(xnew) > 1e6:
                                            xnew = (np.array(xnew) * 1e-9).tolist()
                                            out_xunit = "G" + out_xunit
                                        # nano transform
                                        elif np.max(xnew) < 1e-6:
                                            xnew = (np.array(xnew) * 1e9).tolist()
                                            out_xunit = "n" + out_xunit
                                        else:
                                            pass

                                    # print("xnew: {}".format(xnew))
                                    # print("outdata: {}".format(outdata))
                                    # print("refdata: {}".format(refdata))
                                    plt.plot(xnew, outdata, 'b', label='outdata')  # (横坐标，纵坐标)
                                    plt.plot(xnew, refdata, 'r', label='refdata')  # (横坐标，纵坐标)
                                    plt.xlabel(out_xname + "(" + out_xunit + ")")  # 横坐标标签
                                    plt.ylabel(noden + "(" + yunit + ")")  # 纵坐标标签
                                    plt.grid()
                                    if i == 0:
                                        mark = "first"
                                    else:
                                        mark = "last"
                                    plt.title("{} {}".format(plotname_node, mark), backgroundcolor=titlecolor)  # 折线图标题

                                    plt.legend(loc='best')

                                    savepath = f"{self.output_folder}/case" + str(caseindex) + "_" + plotname_node + " " + mark + '.jpg'
                                    plt.savefig(savepath)
                                    # plt.show()
                                    plt.close()

                            except TypeError as e:
                                print("Errors occured in plotting. {}".format(e))

    def diffout(self, thread_list2):
        for netId in range(1, self.spfile_Num + 1):
            self.diff_data[netId] = mp.Manager().dict()
            t2 = mp.Process(target=self.calc_deviation, args=(netId,), daemon=True)
            thread_list2.append(t2)

    def calc_deviation(self, netId):
        start = time.time()
        caseindex = self.getCaseIndex(netId)
        tag = self.case_limit[caseindex]
        self.diff_data[netId]["outdiffCost"]=None
        self.diff_data[netId]["AnalysisType"]=None
        self.diff_data[netId]["outdiffdetail"]=None
        self.diff_data[netId]["outdiff"]=None
        if self.version == "base" and self.data_df_diff.loc[netId].SimulatorStat:
            if tag == "base" or tag == "plus":
                # self.data_df_diff.loc[netId, "outdiff"] = "PASS"
                self.diff_data[netId]["outdiff"] = "PASS"
                print(f"INFO: {self.data_df_diff.loc[netId].outFile} 不进行结果比较")
                return 1
        elif self.version == "plus" and self.data_df_diff.loc[netId].SimulatorStat:
            if tag == "plus":
                print(f"INFO: {self.data_df_diff.loc[netId].outFile} 不进行结果比较")
                # self.data_df_diff.loc[netId, "outdiff"] = "PASS"
                self.diff_data[netId]["outdiff"] = "PASS"
                return 1
        else: 
            pass
        
        if self.data_df_diff.loc[netId].SimulatorStat & os.path.exists(self.data_df_diff.loc[netId].outFile):
            outfile = self.data_df_diff.loc[netId].outFile
            # print(outfile)
            # bench文件
            ref_file = self.data_df_diff.loc[netId].RefoutFile

            compare = None
            com_result = str({})
            # 解析两份out文件，找到对比的内容，并执行对比
            # print(f"error info: {self.data_df_diff.loc[j]}")
            try:
                if os.path.exists(outfile) and os.path.exists(ref_file):

                    results_1_dict, plotname_arr1 = self.outfile_parser(outfile)
                    results_2_dict, plotname_arr2 = self.outfile_parser(ref_file)

                    # 计算误差
                    compare, com_result = self.calc_error(netId, results_1_dict, results_2_dict)

                # 如果参数指定了保存图片，则开始画图
                    if opt.savefig:
                        self.save_plot(netId, results_1_dict, results_2_dict, compare)
                AnalysisTypes = list(set(plotname_arr1))
                self.diff_data[netId]["AnalysisType"] = ";".join(AnalysisTypes)
                self.diff_data[netId]["outdiff"] = compare
                self.diff_data[netId]["outdiffdetail"] = com_result
                # self.data_df_diff.loc[netId, "AnalysisType"] = ";".join(AnalysisTypes)
                # self.data_df_diff.loc[netId, "outdiff"] = compare
                # self.data_df_diff.loc[netId, "outdiffdetail"] = com_result
            except Exception as err:
                # print(f"outfile: {outfile}, ref_file: {ref_file}")
                print(f"ERROR INFO: {self.data_df_diff.loc[netId]}")
                print('ERROR MSG: ' + str(err))
        
            end = time.time()
            cost = end-start
            self.diff_data[netId]["outdiffCost"] = cost
            # self.data_df_diff.loc[netId, "outdiffCost"] = cost
            # print(f"\nINFO: Start calculating the deviation:")
            print(f"INFO: {outfile} 误差计算耗时: \n    diffCost: {cost}\n")

    def update_df_data(self):
        for netId in self.sim_data.keys():
            self.data_df_simulator.loc[netId, "Simulatorcost"] = self.sim_data[netId]["Simulatorcost"]
            self.data_df_diff.loc[netId, "Simulatorcost"] = self.sim_data[netId]["Simulatorcost"]

        for netId in self.diff_data.keys():
            self.data_df_diff.loc[netId, "AnalysisType"] = self.diff_data[netId]["AnalysisType"]
            self.data_df_diff.loc[netId, "outdiff"] = self.diff_data[netId]["outdiff"]
            self.data_df_diff.loc[netId, "outdiffdetail"] = self.diff_data[netId]["outdiffdetail"]
            self.data_df_diff.loc[netId, "outdiffCost"] = self.diff_data[netId]["outdiffCost"]

    def result_statistics(self):
        t = 0
        f = 0
        dt = 0
        df = 0
        c = 0
        for id in range(1, self.spfile_Num + 1):
            status = self.data_df_diff.loc[id, "SimulatorStat"]
            diff_status = self.data_df_diff.loc[id, "outdiff"]
            diff_time = self.data_df_diff.loc[id, "time_div"]
            if status==1:
                t+=1
                if diff_time == 0:
                    c+=1
                if diff_status==True or diff_status=="PASS":
                    dt+=1
                else:
                    df+=1
            else:
                f+=1
        
        self.rs.write(f"""
# Test Set: {self.dir_dict[opt.rp]}
*********************************************************
*                     测试结果统计                      *
*********************************************************
    本次回归测试共执行{t+f}条case, 其中:
        仿真成功: {t} 条
        仿真成功case中对比时间超过golden 20%的： {c}条
        仿真失败: {f} 条
        结果对比成功: {dt} 条
        结果对比失败: {df} 条

*********************************************************\n""")
        print("\n")
        print("*"*100+"\n")
        print("*" + "      测试结果统计\n")
        print("*"*100+"\n")
        print(f"        本次回归测试共执行 {t+f} 条case, 其中:\n")
        print(f"            仿真成功: {t} 条\n")
        print(f"           仿真成功case中对比时间超过golden 20%的： {c}条\n")
        print(f"            仿真失败: {f} 条\n")
        print(f"            结果对比成功: {dt} 条\n")
        print(f"            结果对比失败: {df} 条\n")
        print("\n")
        print("*"*100+"\n")
        
    def bench_error_data(self):
        date_str = time.strftime("%m%d%H%M%S", time.localtime())
        df = self.data_df_diff
        failed_df = df[(df['SimulatorStat'] == 0) | (df['outdiff'] == False) | (df['outdiff'].isna())]
        test_set = self.dir_dict[opt.rp]
        if len(failed_df) > 0:
            os.system(f"mkdir /home/mnt/bencherror/{date_str}_{self.dir_dict[opt.rp]}")
            for i in list(failed_df.index):
                aa = failed_df.loc[i, "spFile"]
                bb = aa.split(test_set)
                cc = bb[1].split("/")[1]
                dd = f"{bb[0]}{test_set}/{cc}" 
                copyCmd = f"cp -r {dd} /home/mnt/bencherror/{date_str}_{self.dir_dict[opt.rp]}/"
                os.system(copyCmd)
            os.system(f"cp -r {self.output_folder} /home/mnt/bencherror/{date_str}_{self.dir_dict[opt.rp]}/")
            print(f"INFO: 回归失败案例存放 ip: 10.1.10.11 用户名 test 密码 testing")
            print(f"INFO: 回归失败案例已整理至 /home/mnt/bencherror/{date_str}_{self.dir_dict[opt.rp]}/ 目录")
        now = datetime.datetime.now()
        self.autoRunlogfile.write(now.strftime("AutoTest End %Y-%m-%d %H:%M:%S \n"))

    def dataframe_to_log(self, data_frame, file_path=r'./tmp.log', file_object=None, isclose=True):
        data = data_frame.to_dict(orient='dict')
        d_keys = data.keys()
        key_len = {}
        for a in d_keys:
            key_len[a] = len(a)
            dvalue = data[a]
            for b in dvalue.keys():
                if len(str(dvalue[b])) > key_len[a]:
                    key_len[a] = len(str(dvalue[b]))
        if file_object is None:
            f = open(file_path, 'a+')
        else:
            f = file_object
        for c in d_keys:
            dvalue = str(c).ljust(key_len[c]+2, ' ')
            f.write(dvalue)
        f.write("\n")
        for d in data_frame.index:
            for e in d_keys:
                value = data[e][d]
                fvalue = str(value).ljust(key_len[e]+2, ' ')
                f.write(fvalue)
            f.write("\n")
        if isclose==False:
            pass
        else:
            f.close()

    def outputTerm(self):
        df = self.data_df_diff
        failed_df = df[(df['SimulatorStat'] == 0) | (df['outdiff'] == False) |  (df['time_div'] == 0) | (df['outdiff'].isna())]
        # 可以在大数据量下，没有省略号
        if len(failed_df) > 0:
            print("INFO: 总计失败：" + str(len(failed_df)) + "个用例" + "\n")
            pd.set_option('display.max_columns', 20)
            pd.set_option('display.max_rows', 100)
            pd.set_option('display.max_colwidth', 500)
            pd.set_option('display.width', 1000000)
            # print(failed_df.loc[:, ['spFile', 'SimulatorStat', 'Simulatorcost', 'cost_div', 'outdiff']])
        
            sim_fail_df = failed_df[failed_df['SimulatorStat'] == 0]
            print(f"\nWARNING 仿真失败: {len(sim_fail_df)}条")
            print(sim_fail_df.loc[:, ['spFile', 'SimulatorStat', 'Simulatorcost', 'walltime_rate', 'outdiff']])
            self.rs.write(f"\nWARNING 仿真失败: {len(sim_fail_df)}条:\n")
            self.dataframe_to_log(sim_fail_df.loc[:, ["spFile", "SimulatorStat", "Simulatorcost", 'walltime_rate', 'outdiff', 'outdiffdetail']] ,file_object=self.rs, isclose=False)

            diff_fail_df = failed_df[(failed_df['SimulatorStat'] == 1) & ((failed_df['outdiff'] == False) | (failed_df['outdiff'].isna()))]
            print(f"\nWARNING 结果对比失败: {len(diff_fail_df)}条")
            print(diff_fail_df.loc[:, ['spFile', 'SimulatorStat', 'Simulatorcost', 'walltime_rate', 'outdiff']])
            self.rs.write(f"\nWARNING 结果对比失败: {len(diff_fail_df)}条:\n")
            self.dataframe_to_log(diff_fail_df.loc[:, ["spFile", "SimulatorStat", "Simulatorcost", 'walltime_rate', 'outdiff', 'outdiffdetail']] ,file_object=self.rs, isclose=False)

            time_out_df = failed_df[(failed_df['SimulatorStat'] == 1) & (failed_df['time_div'] == 0) & (failed_df['outdiff'] == True)]
            print(f"\nWARNING 对比时间超过 golden 20%: {len(time_out_df)}条")
            print(time_out_df.loc[:, ['spFile', 'SimulatorStat', 'Simulatorcost', 'walltime_rate', 'outdiff']])
            self.rs.write(f"\nWARNING 对比时间超过 golden 20%: {len(time_out_df)}条:\n")
            self.dataframe_to_log(time_out_df.loc[:, ["spFile", "SimulatorStat", "Simulatorcost", 'walltime_rate', 'outdiff', 'outdiffdetail']] ,file_object=self.rs, isclose=False)
            self.rs.write(datetime.datetime.now().strftime("AutoTest End %Y-%m-%d %H:%M:%S \n"))
            self.rs.close()
        else:
            print(f"INFO: 无失败案例,测试集case全部仿真成功,对比成功,仿真时间未超20%,回归测试通过")
            self.rs.write(f"\nINFO: 无失败案例,测试集case全部仿真成功,对比成功,仿真时间未超20%,回归测试通过")
            self.rs.write(datetime.datetime.now().strftime("\nAutoTest End %Y-%m-%d %H:%M:%S \n"))
            self.rs.close()

        return len(failed_df['spFile'])


if __name__ == '__main__':
    # 创建解析对象，并向对象添加关注的命令参数，解析参数
    # argparse module: 命令参数解析
    parser = argparse.ArgumentParser()
    parser.add_argument("--tp", type=str, default="./", help="the save path to test case")
    parser.add_argument("--sh", type=str, default='btdsim', help="choose simulator path")
    parser.add_argument("--savesimcsv", type=bool, default=True, help="save final simulator csv file")
    parser.add_argument("--savediffcsv", type=bool, default=True, help="save final diff csv file")
    parser.add_argument("--savefig", type=bool, default=False, help="save final plot")
    parser.add_argument("--metric", type=str, default="MAPE", help="select metrics for diff, i.e. RMSE or MAPE")
    parser.add_argument("--isdelold", type=int, default=1, help="Whether to delete the old case dir")
    parser.add_argument("--rp", type=str, default="all", help="""path to test case""")
    parser.add_argument("--cn", type=str, default="", help="case name")
    parser.add_argument("--si", type=str, default="all", help="execute case selector, all、hisi、huali")
    parser.add_argument("--bv", type=str, default="rf", help="btdsim version: base, plus, rf")
    parser.add_argument("--ccost", type=str, default=0, help="废弃参数,待删除")
    parser.add_argument("--logtime", type=int, default=1, help="Whether to compare the cputime and walltime")
    opt = parser.parse_args()
    print(opt)


    # 初始化
    atc = AutoTestCls(opt)

    # 创建线程池
    thread_list = []

    # 执行仿真
    ##print("Start AutoSimulator...")
    atc.sim_folder(thread_list)
    ##print("Total: %d files (.sp .scs or .cir)\n" % (atc.spfile_Num))

    #等待子线程全部运行完毕
    for t in thread_list:
        # t.daemon(True)  # 设置为守护线程，不会因主线程结束而中断
        t.start()
        time.sleep(1)

    for t in thread_list:
        t.join()  # 子线程全部加入，主线程等所有子线程运行完毕

    # 仿真状态统计
    print("start check out simulator stat...")
    atc.global_log_check()

    # #仿真类型统计
    # print("start check out Analysis Type...")
    # atc.global_out_check()

    print("start diff out file...")

    # 结果对比线程池
    thread_list2 = []

    atc.diffout(thread_list2)

    for t2 in thread_list2:
        # t.daemon(True)  # 设置为守护线程，不会因主线程结束而中断
        t2.start()
        time.sleep(1)

    for t2 in thread_list2:
        t2.join()  # 子线程全部加入，主线程等所有子线程运行完毕
    
    # 同步父线程和子线程的数据
    atc.update_df_data()

    # 时间对比(DONE)
    if opt.logtime == 1:
        print("start check out log CPU time and Wall time...")
        atc.diff_logtime()

    # 将仿真结果写入excel
    date_str = time.strftime("%m%d%H%M%S", time.localtime())
    if opt.savesimcsv:
        writer1 = pd.ExcelWriter(f'{atc.output_folder}/data_df_simulator_{date_str}.xlsx')
        atc.data_df_simulator.to_excel(writer1)
        writer1.save()

    # 将对比结果写入excel
    if opt.savediffcsv:  
        writer2 = pd.ExcelWriter(f'{atc.output_folder}/data_df_diff_{date_str}.xlsx')
        atc.data_df_diff.to_excel(writer2)
        writer2.save()
    
    atc.result_statistics()
    atc.bench_error_data()
    ret = atc.outputTerm()
    if(ret >=1):
        print("ERROR Count: ")
        print(ret)
        sys.exit(1)
    else:
        sys.exit(0)

