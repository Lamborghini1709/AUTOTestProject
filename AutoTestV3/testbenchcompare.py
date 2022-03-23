# -*- coding: utf-8 -*-
# @Time    : 2021/9/8 11:13
# @Author  : Wayne
# @File    : autotestcls.py
# @Software: PyCharm
import argparse
import datetime
import os
import time
import math
import pickle
import pandas as pd
import numpy as np
from math import sqrt
import ast


class AutoTestCls():
    # 定义、创建对象初始化
    def __init__(self, opt):
        self.spfile_Num = 0
        self.line_list = []
        self.time_list = []
        self.str_list = []
        self.test_dir = opt.tp
        self.ref_filename = 'bench'
        self.sh = opt.sh

        # def logfile
        self.autoRunlogfile = open("autoRun.log", "a")
        now = datetime.datetime.now()
        self.autoRunlogfile.write(now.strftime("%Y-%m-%d %H:%M:%S \n"))

        # def dataform1
        data_simulator = np.arange(1, 7).reshape((1, 6))
        self.data_df_simulator = pd.DataFrame(data_simulator)
        self.data_df_simulator.columns = ['index', 'netFile', 'logFile', 'outFile', 'SimulatorStat', 'Simulatorcost']
        self.data_df_simulator = self.data_df_simulator.set_index(['index'])

        # def dataform2
        data_df_diff = np.arange(1, 11).reshape((1, 10))
        self.data_df_diff = pd.DataFrame(data_df_diff)
        self.data_df_diff.columns = ['index', 'spFile', 'logFile', 'outFile', 'RefoutFile', 'AnalysisType',
                                     'SimulatorStat', 'Simulatorcost', "outdiff", "outdiffdetail"]
        self.data_df_diff = self.data_df_diff.set_index(['index'])

        # 判断是否为可执行网表文件
        self.is_netlist = lambda x: any(x.endswith(extension)
                                        for extension in ['.sp', '.cir', 'scs'])

        # 选择对比节点
        self.check_nodes_stella = dict()
        # self.check_nodes = {
        #     1: ["Transient Analysis--Vout", "Oscillator Period and Frequency--period",
        #         "Oscillator Period and Frequency--frequency", "Single-sideband Phase Noise Spectral Density--phnoise"],
        #     2: ["Oscillator Period and Frequency--period", "Oscillator Period and Frequency--frequency",
        #         "Harmonic Balance Oscillator Steady State Analysis--vout",
        #         "Harmonic Balance Oscillator Steady State Spectrum--vout"],
        #     3: ["Harmonic Balance Noise Analysis--out", "Harmonic Balance Steady State Analysis--net037",
        #         "Harmonic Balance Steady State Spectrum--net037"],
        #     4: ["Harmonic Balance Steady State Analysis--RF", "Harmonic Balance Steady State Spectrum--RF",
        #         "Harmonic Balance AC Analysis--RF"],
        #     5: ["Harmonic Balance Steady State Analysis--RF", "Harmonic Balance Steady State Spectrum--RF"],
        #     6: ["Harmonic Balance Steady State Spectrum--RF", "Harmonic Balance Steady State Spectrum--IFp"],
        #     7: ["Harmonic Balance Steady State Analysis--RFOUT", "Harmonic Balance Steady State Spectrum--RFOUT"],
        #     8: ["Transient Analysis--net44", "Periodic Steady State Analysis--net44",
        #         "Periodic Steady State Spectrum--net44",
        #         "Periodic Noise Analysis--out", "Integrated Noise--onoise_total"],
        #     9: ["Harmonic Balance Steady State Analysis--SUB_LNA", "Harmonic Balance Steady State Spectrum--SUB_LNA",
        #         "Harmonic Balance Noise Analysis--out", "Integrated Noise--onoise_total"],
        #     10: ["Transient Analysis--ip(V37)", "Transient Analysis--VVCOBYP"],
        #     11: ["Transient Analysis--I0.net4", "Transient Analysis--I0.net3"],
        #     12: ["Transient Analysis--I71.I8_CC0_pos", "Transient Analysis--I71.I8_CC0_neg"],
        #     13: ["Transient Analysis--i1(ravdi)", "Transient Analysis--x01.xck0_clk1600a"],
        #     14: ["Transient Analysis--ip(V1)", "Transient Analysis--D7", "Transient Analysis--I0.VOUT_DAC"],
        #     15: ["Operating Point--i1(m2)", "Operating Point--i4(m2)"],
        #     16: ["AC Analysis--out", "AC Analysis--vp(out)"],
        #     17: ["AC Analysis--ip(V0)", "AC Analysis--net02"],
        #     18: ["Periodic Steady State Analysis--RFout", "Periodic Steady State Spectrum--RFout",
        #          "Periodic Noise Analysis--out",
        #          "Integrated Noise--onoise_total"],
        #     19: ["Transient Analysis--voqb", "Transient Analysis--voi"],
        #     20: ["AC Analysis--anot", "AC Analysis--out", "Noise Analysis--out",
        #          "Integrated Noise--onoise_total"]
        # }

        self.InitCaseForm()

    def InitCaseForm(self):
        if isinstance(self.test_dir, str):
            # 遍历目录下的所有文件
            for filepath, dirnames, filenames in os.walk(self.test_dir, topdown=False):
                for filename in filenames:
                    if self.is_netlist(filename):
                        # sp文件
                        netfile = os.path.join(filepath, filename)
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

                        self.data_df_simulator.loc[self.spfile_Num] = [netfile, logFile, outFile, SimulatorStat,
                                                                       Simulatorcost]

                        self.data_df_diff.loc[self.spfile_Num] = [netfile, logFile, outFile, ref_file, AnalysisType,
                                                                  SimulatorStat, Simulatorcost, Simulatordiff,
                                                                  outdiffdetail]

                    if filename == 'cases_nodes.xlsx':
                        nodes_df = pd.read_excel('cases_nodes.xlsx', index_col = 0) # 指定第一列为行索引
                        for row in range(1, self.spfile_Num + 1):
                            row_value = nodes_df.loc[row, 'nodes'].split(", ")
                            self.check_nodes_stella[row] = row_value
                        # print(self.check_nodes_stella)
                        # print(self.check_nodes)
                        # print(self.check_nodes_stella == self.check_nodes)

        else:
            print("Please specify the test folder in string format.")

    # 执行仿真
    def sim_folder(self):
        for index in range(1, self.spfile_Num + 1):
            # 找case对应的bench文件结果
            ref_file = self.data_df_diff.loc[index].RefoutFile
            if not os.path.exists(ref_file):
                self.data_df_diff.loc[index, "RefoutFile"] = None
                self.data_df_diff.loc[index, "RefoutFile"] = None
            # 执行仿真
            self.run_simulation(index)

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
            os.system(RunCmd)
            end = time.time()
            cost = int((end - start) * 1000) / 1000

            self.data_df_simulator.loc[netfileID, "Simulatorcost"] = cost
            self.data_df_diff.loc[netfileID, "Simulatorcost"] = cost

            # print("rcmd:", RunCmd)

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
                stat = self.logfile_check(logfile)
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
                        if 'SIMULATION is completed sucessfully' in line:
                            return 1
            except:
                try:
                    with open(file, encoding='latin-1') as f:
                        for line in f.readlines():
                            if 'SIMULATION is completed sucessfully' in line:
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
                notenum += 1
                nodelist = []
                nodelist.append(line)
            elif line.startswith('#') or line.startswith(' \n'):
                pass
            else:
                nodelist.append(line)

        nodelists.append(nodelist)
        assert len(nodelists) == notenum
        nodelistsresult = {}
        # read the number of variables and number of points
        for titles in nodelists:
            number_of_variables = int(titles[4].split(':', 1)[1])
            plotname = titles[2].split(': ')[-1].split('\n')[0]
            plotname_arr.append(plotname)
            nodelistsresult[plotname] = {}

            # read the names of the variables
            variable_name = []
            for variable in titles[8:8 + number_of_variables]:
                variable_name.append(variable.split('\t', -1)[2])
            # print(variable_name)

            # read the values of the variables
            results = {}
            variable_index = 0
            for variable in variable_name:
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
                    vlu = eval(st)
                    if type(vlu) == tuple:
                        results[variable_name[variable_index]].append(vlu[0])
                    else:
                        results[variable_name[variable_index]].append(vlu)
                    variable_index += 1
                else:
                    st = value.split('\t', -1)[-1].split('\n')[0]
                    if st.startswith("FAIL"):
                        st = "0"
                    vlu = eval(st)
                    if type(vlu) == tuple:
                        results[variable_name[variable_index]].append(vlu[0])
                    else:
                        results[variable_name[variable_index]].append(vlu)
                    variable_index = 0
            nodelistsresult[plotname] = results
        # close the output_file
        fo.close()

        assert len(nodelistsresult) > 0
        return nodelistsresult, plotname_arr

    def get_mse(self, records_real, records_predict):
        """
        均方误差 估计值与真值 偏差
        """
        if len(records_real) == len(records_predict):
            return sum([(x - y) ** 2 for x, y in zip(records_real, records_predict)]) / len(records_real)
        else:
            return None

    def get_rmse(self, records_real, records_predict):
        """
        均方根误差：是均方误差的算术平方根
        """
        mse = self.get_mse(records_real, records_predict)
        if mse or mse == 0:
            return math.sqrt(mse)
        else:
            return None

    def get_ae(self, records_real, records_predict):
        if len(records_real) == len(records_predict):
            return sum([np.abs(x - y) for x, y in zip(records_real, records_predict)]) / len(records_real)
        else:
            return None

    def getCaseIndex(self, index):
        netfile = self.data_df_simulator.loc[index].netFile
        caseindex = netfile.split('/case')[1].split('/')[0]
        print(caseindex)
        return int(caseindex)

    def calc_error(self, index, original_results_dict, new_results_dict):

        plotname_nodes = []
        plotnames = original_results_dict.keys()
        check_nodes = []
        for plotname in plotnames:
            node_dict = original_results_dict[plotname]
            nodes = node_dict.keys()
            for node in nodes:
                plotname_nodes.append('--'.join((plotname, node)))

        # 读取case number，作为index找到对应case需要查看的节点
        caseindex = self.getCaseIndex(index)
        check_nodes = self.check_nodes_stella[caseindex]

        comp_result = {}
        comparelist = []
        for plotname_node in check_nodes:
            plotn = plotname_node.split('--')[0]
            noden = plotname_node.split('--')[1]
            outdata = original_results_dict[plotn][noden]
            refdata = new_results_dict[plotn][noden]

            assert len(refdata) == len(outdata)

            rmse = self.get_rmse(outdata, refdata)
            # rmse = self.get_ae(outdata, refdata)
            comp_value = 1e-3 if np.average(outdata) == 0 else np.abs(np.average(outdata))
            compareflag = True if rmse <= comp_value or rmse < 1e-5 else False
            comp_result[plotname_node] = str((rmse, comp_value, compareflag))
            comparelist.append(compareflag)
            compare = False if False in comparelist else True
        return compare, str(comp_result)

    def diffout(self):
        for j in range(1, self.spfile_Num + 1):
            if self.data_df_diff.loc[j].SimulatorStat & os.path.exists(self.data_df_diff.loc[j].outFile):
                outfile = self.data_df_diff.loc[j].outFile
                print(outfile)
                # bench文件
                ref_file = self.data_df_diff.loc[j].RefoutFile

                compare = None
                com_result = str({})
                # 解析两份out文件，找到对比的内容，并执行对比
                if os.path.exists(outfile) and os.path.exists(ref_file):
                    results_1_dict, plotname_arr1 = self.outfile_parser(outfile)
                    results_2_dict, plotname_arr2 = self.outfile_parser(ref_file)
                    compare, com_result = self.calc_error(j, results_1_dict, results_2_dict)
                AnalysisTypes = list(set(plotname_arr1))
                self.data_df_diff.loc[j, "AnalysisType"] = ";".join(AnalysisTypes)
                self.data_df_diff.loc[j, "outdiff"] = compare
                self.data_df_diff.loc[j, "outdiffdetail"] = com_result


if __name__ == '__main__':
    # 创建解析对象，并向对象添加关注的命令参数，解析参数
    # argparse module: 命令参数解析
    parser = argparse.ArgumentParser()
    parser.add_argument("--tp", type=str, default="./", help="path to test case")
    parser.add_argument("--sh", type=str, default='btdsim', help="choose simulator path")
    opt = parser.parse_args()
    print(opt)

    # 执行仿真
    print("Start AutoSimulator...")
    atc = AutoTestCls(opt)
    atc.sim_folder()
    print("Total: %d files (.sp .scs or .cir)\n" % (atc.spfile_Num))

    # 仿真状态统计
    print("start check out simulator stat...")
    atc.global_log_check()

    # #仿真类型统计
    # print("start check out Analysis Type...")
    # atc.global_out_check()

    # 将仿真结果写入excel
    date_str = time.strftime("%m%d%H%M%S", time.localtime())
    writer1 = pd.ExcelWriter('data_df_simulator_' + date_str + '.xlsx')
    atc.data_df_simulator.to_excel(writer1)
    writer1.save()

    # 仿真结果对比，并写入excel
    print("start diff out file...")
    atc.diffout()
    writer2 = pd.ExcelWriter('data_df_diff_' + date_str + '.xlsx')
    atc.data_df_diff.to_excel(writer2)
    writer2.save()
