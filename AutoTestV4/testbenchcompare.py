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
from tool_utils import get_rmse, get_mape, AlignDataLen, max_diff
import threading
import sys


class AutoTestCls():
    # 定义、创建对象初始化
    def __init__(self, opt):
        # 最小阈值
        self.min_threshold = 1e-14
        self.spfile_Num = 0
        self.line_list = []
        self.time_list = []
        self.str_list = []
        self.sh = opt.sh
        self.exsign = opt.si
        self.version = opt.bv
        self.dir_dict = {
            0: "All_regress_Cases",
            1: "hisiCaseAll",
            2: "regress_Cases_all-cmg-bulk_20230307-1400",
            3: "RegressCasesCircuitLimit5K_20230330-1000",
            4: "cmg_regress_Cases_version-107_20220909",
            5: "cmg_regress_Cases_version-110.0_20220705",
            6: "bulk_regress_Cases_version-106.2_20220824",
            7: "regress_Cases_bulk107_2022-11-30",
            8: "haisiRegre",
            9: "radioCircuit", 
            10: "huali_Case_regress_20221015",
            11: "regress_Cases_all-cmg-bulk_20221202-1600",
            12: "cmg_regress_Cases_version-106.1_20230201",
            13: "hisiCaseAll_part2",
            14: "regress_Cases_all-cmg-bulk_20230307-1400_part2"
        }
        self.test_dir = os.path.join(opt.tp, self.dir_dict[int(opt.rp)])
        self.ref_filename = 'bench'
        self.cases_nodes_path = os.path.join(self.test_dir, "cases_nodes.xlsx")
        self.output_folder = os.path.join(self.test_dir, "output")
        self.case_dir = os.path.join(self.test_dir, opt.cn)

        # 需要跳过不进行测试的case
        self.not_check_case = ["case999"]

        # 回归测试集初始化
        initCmd = f"cp -r /home/mnt/BTD/{self.dir_dict[int(opt.rp)]}  {opt.tp}"
        print("CMD: "+initCmd)
        os.system(initCmd)

        # def logfile
        os.makedirs(self.output_folder, exist_ok=True)
        self.autoRunlogfile = open(f"{self.output_folder}/autoRun.log", "a")
        now = datetime.datetime.now()
        self.autoRunlogfile.write(now.strftime("%Y-%m-%d %H:%M:%S \n"))

        # def dataform1
        data_simulator = np.arange(1, 7).reshape((1, 6))
        self.data_df_simulator = pd.DataFrame(data_simulator)
        self.data_df_simulator.columns = ['index', 'netFile', 'logFile', 'outFile', 'SimulatorStat', 'Simulatorcost']
        self.data_df_simulator = self.data_df_simulator.set_index(['index'])

        # def dataform2
        data_df_diff = np.arange(1, 12).reshape((1, 11))
        self.data_df_diff = pd.DataFrame(data_df_diff)
        self.data_df_diff.columns = ['index', 'spFile', 'logFile', 'outFile', 'RefoutFile', 'AnalysisType',
                                     'SimulatorStat', 'Simulatorcost', "time_div", "outdiff", "outdiffdetail"]
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
            # time_value = nodes_df.loc[row, 'times']
            # self.check_time_dict[row] = time_value
            limit_value = nodes_df.loc[row, 'limits']
            self.case_limit[row] = limit_value
            # if pd.isna(limit_value):
            #     pass
            # else:
            #     self.case_limit[row] = limit_value

        self.InitCaseForm()

    def InitCaseForm(self):
        if isinstance(self.case_dir, str):
            # 遍历目录下的所有文件
            for filepath, dirnames, filenames in os.walk(self.case_dir, topdown=False):
                for filename in filenames:
                    if self.is_netlist(filename):
                        # sp文件
                        netfile = os.path.join(filepath, filename)
                        ret = self.not_check_file_list(netfile)
                        caseindex = netfile.split('case')[1].split('/')[0]
                        if(ret == 1):
                            continue
                        if self.exsign == "huali" and int(caseindex) >=1000:
                            continue
                        elif self.exsign == "hisi" and int(caseindex) <=1000:
                            continue
                        if 'model' in netfile or 'gpdk' in netfile or 'INCLUDE' in netfile:
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

                        # diff result
                        Simulatordiff = None

                        # diff result detail
                        outdiffdetail = {}
                        
                        # diff time_div
                        time_div = None

                        self.data_df_simulator.loc[self.spfile_Num] = [netfile, logFile, outFile, SimulatorStat,
                                                                       Simulatorcost]

                        self.data_df_diff.loc[self.spfile_Num] = [netfile, logFile, outFile, ref_file, AnalysisType,
                                                                  SimulatorStat, Simulatorcost, time_div, Simulatordiff,
                                                                  outdiffdetail]
                        
                        # 删除bench目录外的out文件
                        if opt.isdelout == True:
                            self.del_out(netfile)
                        else:
                            pass

        else:
            print("Please specify the test folder in string format.")


    def del_out(self, netfile):
        outFile = self.change_suffix(netfile, '.out')
        if os.path.exists(outFile):
            os.remove(outFile)


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
            RunCmd = self.sh + " {} -f nutascii -m4 > {}".format(netfile, logfile)
            start = time.time()
            os.system(RunCmd)
            end = time.time()
            # print("cmd: {}".format(RunCmd))
            cost = int((end - start) * 1000) / 1000

            self.data_df_simulator.loc[netfileID, "Simulatorcost"] = cost
            self.data_df_diff.loc[netfileID, "Simulatorcost"] = cost
            # print("Simulatorcost: {}".format(self.data_df_simulator.loc[netfileID].Simulatorcost))
            # print("rcmd:", RunCmd)

    def run_simulation(self, netfileID):
        netfile = self.data_df_simulator.loc[netfileID].netFile
        print("Find %s \n" % (netfile))
        if netfile:
            # RunCmd = ['simulator',spfile]
            logfile = self.data_df_simulator.loc[netfileID].logFile
            # changed 0904 >> to >为了每次重新仿真得到的log不会记录之前的结果，
            # 否则autoRun.log的自动判断会出错
            # 执行仿真并记录仿真时间
            RunCmd = self.sh + " {} -f nutascii > {}".format(netfile, logfile)
            # os.system(' '.join(RunCmd))
            start = time.time()
            # print("start time: {}".format(start))
            print("cmd: {}".format(RunCmd))
            os.system(RunCmd)
            end = time.time()
            cost = int((end - start) * 1000) / 1000
            # print("end time: {}".format(end))
            # print("cost: {}".format(cost))

            self.data_df_simulator.loc[netfileID, "Simulatorcost"] = cost
            self.data_df_diff.loc[netfileID, "Simulatorcost"] = cost
            # print("Simulatorcost: {}".format(self.data_df_simulator.loc[netfileID].Simulatorcost))
            # print("rcmd:", RunCmd)

    # 执行仿真
    def sim_folder(self,thread_list):
        for index in range(1, self.spfile_Num + 1):
            # 找case对应的bench文件结果
            ref_file = self.data_df_diff.loc[index].RefoutFile
            if not os.path.exists(ref_file):
                self.data_df_diff.loc[index, "RefoutFile"] = None
                self.data_df_diff.loc[index, "RefoutFile"] = None
            # 执行仿真
            t1 = threading.Thread(target=self.run_simulation_g,args=(index,))
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
                        stat = self.logfile_check(logfile)
                elif self.version == "plus":
                    if tag == "plus":
                        stat = self.limit_logfile_check(logfile)
                    else:
                        stat = self.logfile_check(logfile)
                else: 
                    stat = self.logfile_check(logfile)
              
                # print("stat: {}".format(stat))
                if stat:
                    SimulatorStat = 1
                    # self.get_time(id)
                    self.autoRunlogfile.write(' '.join([spfile, 'YES']))
                else:
                    SimulatorStat = 0
                    self.data_df_simulator.loc[id, "Simulatorcost"] = None
                    self.data_df_diff.loc[id, "Simulatorcost"] = None
                    self.autoRunlogfile.write(' '.join([spfile, 'NO']))
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
                with open(file) as f:
                    for line in f.readlines():
                        if 'SIMULATION is completed successfully' in line:
                            return 1
            except:
                try:
                    with open(file, encoding='latin-1') as f:
                        for line in f.readlines():
                            if 'SIMULATION is completed successfully' in line:
                                return 1
                except:
                    print("error decode:" + file)
        return 0

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
            plotname = titles[2].split(': ')[-1].split('\n')[0]
            plotname_arr.append(plotname)
            # multi_plotname_result = list()
            if plotname not in nodelistsresult.keys():
                #     mark = True
                #     # print("aaaaa" + str(mark))
                #     # print(nodelistsresult[plotname])
                #     multi_plotname_result.append(nodelistsresult[plotname])
                # else:
                nodelistsresult[plotname] = list()
                # print("bbbb")

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
        print(netfile)
        # netfile: /home/IC/Case_wayne/TestBench_1BaseCases1/>>>>>case1<<<<<</VCO/lab1_pss_pnoise_btd.scs
        caseindex = netfile.split('case')[1].split('/')[0]
        print(caseindex)
        return int(caseindex)
    
    def time_divcheck(self):
        for id in range(1,self.spfile_Num+1):
            if self.data_df_diff.loc[id].SimulatorStat:
                simulator_cost = self.data_df_diff.loc[id, "Simulatorcost"]
                caseindex = self.getCaseIndex(id)
                stand_cost = self.check_time_dict[caseindex]
                diff_cost = (stand_cost - simulator_cost)/ stand_cost *100
                if abs(diff_cost)<=15:
                    self.data_df_diff.loc[id,"time_div"] = 1
                elif abs(diff_cost)>15:
                    self.data_df_diff.loc[id, "time_div"] = 0

    def calc_error(self, index, original_results_dict, new_results_dict):

        plotname_nodes = []
        plotnames = set()
        # 获取所有的plotnames
        # print("HEREHEREHEREHEREHEREHEREHEREHERE")
        # print(original_results_dict)
        # print(type(original_results_dict))
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
                # print("True")
                # print(type(node_dict))
                # print(type(node_dict[0]))
                nodes = node_dict[0].keys()
                # print('node_dict: {}'.format(node_dict))
                # print("nodes: {}".format(nodes))
                # print(len(nodes))
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
                # print("aaa: {}".format(out_plot[i]))
                # each out_plot[i] is an OrderedDict
                # print(type(out_plot[i]))
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
                                                    # 评估指标
                        if opt.metric == "RMSE":
                            metrix_value = get_rmse(outdata, refdata)
                        else:
                            metrix_value = get_mape(outdata, refdata)
                        comp_value = 3e-2
                        unit = nodename.split("----")[-1]
                        if unit=="A":
                            metrix_value2 = max_diff(outdata, refdata)
                            comp_value2 = 1e-9
                            compareflag1 = True if metrix_value <= comp_value else False
                            compareflag2 = True if metrix_value2 <= comp_value2 else False
                            compareflag = compareflag1 | compareflag2
                        elif unit=="V":
                            metrix_value2 = max_diff(outdata, refdata)
                            comp_value2 = 1e-4
                            compareflag1 = True if metrix_value <= comp_value else False
                            compareflag2 = True if metrix_value2 <= comp_value2 else False
                            compareflag = compareflag1 | compareflag2
                        else:
                            compareflag = True if metrix_value <= comp_value else False
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

    def diffout(self):
        for netId in range(1, self.spfile_Num + 1):
            caseindex = self.getCaseIndex(netId)
            tag = self.case_limit[caseindex]
            if self.version == "base" and self.data_df_diff.loc[netId].SimulatorStat:
                if tag == "base" or tag == "plus":
                    self.data_df_diff.loc[netId, "outdiff"] = "PASS"
                    continue
            elif self.version == "plus" and self.data_df_diff.loc[netId].SimulatorStat:
                if tag == "plus":
                    self.data_df_diff.loc[netId, "outdiff"] = "PASS"
                    continue
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
                    self.data_df_diff.loc[netId, "AnalysisType"] = ";".join(AnalysisTypes)
                    self.data_df_diff.loc[netId, "outdiff"] = compare
                    self.data_df_diff.loc[netId, "outdiffdetail"] = com_result
                except Exception as err:
                    # print(f"outfile: {outfile}, ref_file: {ref_file}")
                    print(f"ERROR INFO: {self.data_df_diff.loc[netId]}")
                    print('ERROR MSG: ' + str(err))
            

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
            else:
                f+=1
            if diff_status==True or diff_status=="PASS":
                dt+=1
            else:
                df+=1
        r = open(f"{self.test_dir}/result_statistics.txt", "w")
        r.write(f"本次回归测试共执行{t+f}条case, 其中:\n")
        r.write(f"    仿真成功: {t} 条\n")
        # r.write(f"    仿真成功 中对比时间超过golden15%的： {c}条\n")
        r.write(f"    仿真失败: {f} 条\n")
        r.write(f"    结果对比成功: {dt} 条\n")
        r.write(f"    结果对比失败: {df} 条\n")
        r.close()
        print(f"本次回归测试共执行 {t+f} 条case, 其中:\n")
        print(f"    仿真成功: {t} 条\n")
        # print(f"    仿真成功 中对比时间超过golden15%的： {c}条\n")
        print(f"    仿真失败: {f} 条\n")
        print(f"    结果对比成功: {dt} 条\n")
        print(f"    结果对比失败: {df} 条\n")
        
    def bench_error_data(self):
        date_str = time.strftime("%m%d%H%M%S", time.localtime())
        df = self.data_df_diff
        failed_df = df[(df['SimulatorStat'] == 0) | (df['outdiff'] == False) | (df['outdiff'].isna())]
        test_set = self.dir_dict[int(opt.rp)]
        os.system(f"mkdir /home/mnt/bencherror/{date_str}_{self.dir_dict[int(opt.rp)]}")
        for i in list(failed_df.index):
            aa = failed_df.loc[i, "spFile"]
            bb = aa.split(test_set)
            cc = bb[1].split("/")[1]
            dd = f"{bb[0]}{test_set}/{cc}" 
            copyCmd = f"cp -r {dd} /home/mnt/bencherror/{date_str}_{self.dir_dict[int(opt.rp)]}/"
            os.system(copyCmd)
        os.system(f"cp -r {self.output_folder} /home/mnt/bencherror/{date_str}_{self.dir_dict[int(opt.rp)]}/")
        print(f"INFO: 回归失败案例已整理至 /home/mnt/bencherror/{date_str}_{self.dir_dict[int(opt.rp)]}/ 目录")


    def outputTerm(self):
        df = self.data_df_diff
        failed_df = df[(df['SimulatorStat'] == 0) | (df['outdiff'] == False) | (df['outdiff'].isna())]
        # 可以在大数据量下，没有省略号
        print("总计失败：" + str(len(failed_df)) + "个用例" + "\n")
        pd.set_option('display.max_columns', 1000000)
        pd.set_option('display.max_rows', 1000000)
        pd.set_option('display.max_colwidth', 1000000)
        pd.set_option('display.width', 1000000)
        print(failed_df.loc[:, ['spFile', 'SimulatorStat', 'Simulatorcost', 'outdiff']])
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
    parser.add_argument("--isdelout", type=bool, default=True, help="Whether to delete the out file")
    parser.add_argument("--rp", type=str, default=0, help="path to test case")
    parser.add_argument("--cn", type=str, default="", help="case name")
    parser.add_argument("--si", type=str, default="all", help="execute case selector, all、hisi、huali")
    parser.add_argument("--bv", type=str, default="rf", help="btdsim version: base, plus, rf")
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
        t.setDaemon(True)  # 设置为守护线程，不会因主线程结束而中断
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

    # 时间对比(TODO)
    # atc.time_divcheck()

    date_str = time.strftime("%m%d%H%M%S", time.localtime())
    if opt.savesimcsv:
        # 将仿真结果写入excel
        writer1 = pd.ExcelWriter(f'{atc.output_folder}/data_df_simulator_{date_str}.xlsx')
        atc.data_df_simulator.to_excel(writer1)
        writer1.save()

    # 仿真结果对比，并写入excel
    print("start diff out file...")
    if opt.savediffcsv:
        atc.diffout()
        
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

