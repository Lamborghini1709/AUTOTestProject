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
    def __init__(self, opt):
        self.spfile_Num = 0
        self.UPDATE_TAG = opt.update
        self.line_list = []
        self.time_list = []
        self.str_list = []
        self.test_dir = opt.tp
        self.ref_filename = 'Linux_Ref'
        self.sh = opt.sh
        self.faster = opt.f

        #def logfile
        self.autoRunlogfile = open("autoRun.log", "a")
        now = datetime.datetime.now()
        self.autoRunlogfile.write(now.strftime("%Y-%m-%d %H:%M:%S \n"))

        #def dataform1
        data_simulator = np.arange(1, 8).reshape((1, 7))
        self.data_df_simulator = pd.DataFrame(data_simulator)
        self.data_df_simulator.columns = ['index', 'spFile', 'logFile', 'outFile', 'LinuxRefoutFile', 'SimulatorStat', 'Simulatorcost']
        self.data_df_simulator = self.data_df_simulator.set_index(['index'])

        # def dataform2
        data_df_diff = np.arange(1, 11).reshape((1, 10))
        self.data_df_diff = pd.DataFrame(data_df_diff)
        self.data_df_diff.columns = ['index', 'spFile', 'logFile', 'outFile', 'LinuxRefoutFile', 'AnalysisType', 'SimulatorStat',
                                          'Simulatorcost', "outdiff", "outdiffdetail"]
        self.data_df_diff = self.data_df_diff.set_index(['index'])

        #判断是否为可执行网表文件
        self.is_netlist = lambda x: any(x.endswith(extension)
                                    for extension in ['.sp', '.cir', 'scs'])

        #binary out files
        self.binaryfiles = ["solver4/altera/Linux_Ref/test.out",
                            "solver4/fla_ait/Linux_Ref/hao_testx0.out",
                            "solver4/fla_ait/Linux_Ref/hao_testx4.out",
                            "solver4/Skyworks_080116_top_PEXdcRC_case2_BTD/Linux_Ref/hao_test.out",
                            "solver4/Spansion_package/Linux_Ref/hao_testx1.out",
                            "test_cases_10folders_batch3/GloNav_PSP/Linux_Ref/input_5066.out",
                            "test_cases_10folders_batch3/klubtftest/Linux_Ref/bob.out",
                            "test_cases_10folders_batch3/motorola/Linux_Ref/motorola.out",
                            "test_cases_10folders_batch3/multiThreadedFactor/GA685/Linux_Ref/tran_mt.out",
                            "test_cases_10folders_batch3/multiThreadedFactor/GA685/Linux_Ref/tran_mt_parasitic.out",
                            "test_cases_10folders_batch3/multiThreadedFactor/toshiba_image_ncp/Linux_Ref/vnegsys_afs_default_mt.out",
                            "test_cases_9folers_batch4/Nestoras4/TimeDomain/Linux_Ref/spsys.out",
                            ]
        #BinaryData
        with open('BinaryData.pickle', 'rb') as f:
            dfpkl = pickle.load(f)
        self.BinaryData = dfpkl

        self.InitCaseForm()

    def InitCaseForm(self):
        if isinstance(self.test_dir, str):
            for filepath, dirnames, filenames in os.walk(self.test_dir, topdown=False):
                for filename in filenames:
                    if self.is_netlist(filename):
                        # sp文件
                        spfile = os.path.join(filepath, filename)
                        if ("model" in spfile or "AHDLINCLUDE" in spfile or "SPECTREINCLUDE" in spfile):
                            continue
                        self.spfile_Num += 1
                        # log文件
                        logFile = self.change_suffix(spfile, '.log')
                        # 仿真sp得到的out文件
                        outFile = self.change_suffix(spfile, '.out')
                        ref_file = os.path.join(filepath, self.ref_filename)
                        ref_file = os.path.join(ref_file, filename)
                        # 需要对比的out文件
                        ref_file = self.change_suffix(ref_file, '.out')
                        # 仿真结果
                        SimulatorStat = 0
                        # 仿真时间
                        Simulatorcost = None
                        # diff result
                        Simulatordiff = None

                        AnalysisType=None

                        #diff result detail
                        outdiffdetail = {}

                        self.data_df_simulator.loc[self.spfile_Num] = [spfile, logFile, outFile, ref_file,
                                                                       SimulatorStat, Simulatorcost]
                        self.data_df_diff.loc[self.spfile_Num] = [spfile, logFile, outFile, ref_file, AnalysisType, SimulatorStat,
                                                             Simulatorcost, Simulatordiff, outdiffdetail]
        else:
            print("Please specify the test folder in string format.")


    #执行仿真
    def sim_folder(self):
        for index in range(1, self.spfile_Num+1):
            ref_file = self.data_df_simulator.loc[index].LinuxRefoutFile
            if not os.path.exists(ref_file):
                self.data_df_simulator.loc[index, "LinuxRefoutFile"] = None
                self.data_df_diff.loc[index, "LinuxRefoutFile"] = None
            self.run_simulation(index)





    def run_simulation(self, spfileID):
        spfile = self.data_df_simulator.loc[spfileID].spFile
        print("Find %s \n" % (spfile))
        if spfile and self.UPDATE_TAG:
            # RunCmd = ['simulator',spfile]
            logfile = self.data_df_simulator.loc[spfileID].logFile
            # changed 0904 >> to >为了每次重新仿真得到的log不会记录之前的结果，
            # 否则autoRun.log的自动判断会出错

            RunCmd = "./" + self.sh + " {} -f nutascii > {}".format(spfile, logfile)
            # os.system(' '.join(RunCmd))
            start = time.time()
            os.system(RunCmd)
            end = time.time()
            cost = int((end - start) * 1000) / 1000
            self.data_df_simulator.loc[spfileID, "Simulatorcost"] = cost
            self.data_df_diff.loc[spfileID, "Simulatorcost"] = cost
            # print("rcmd:", RunCmd)

    #修改文件后缀
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


    def global_out_check(self):
        for id in range(1, self.spfile_Num+1):
            spfile = self.data_df_simulator.loc[id].spFile
            logfile = self.data_df_simulator.loc[id].logFile
            if logfile:
                stat = self.outfile_check(logfile)
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
        print("output check is OK.")
        print("The result is in autoRun.log.")

    # changed 0902
    def outfile_check(self, file):
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


    # changed 0902
    # def get_time(self, spfileID):
    #     file = self.data_df_simulator.loc[spfileID].logFile
    #     with open(file) as f1:
    #         for line in f1.readlines():
    #             if line.find('wall-clock time') > -1:
    #                 # print("time:", line)
    #                 self.line_list.append(line)
    #     # print("line_list:", line_list)
    #     for line in self.line_list:
    #         line_list2 = line.split()
    #         time = line_list2[7]
    #         self.str_list.extend(time)
    #
    #     # print("str_list:", str_list)
    #     length = len(self.str_list)
    #     x = 0
    #     while x < length:
    #         if self.str_list[x] == ":":
    #             # l.remove(l[x])
    #             del self.str_list[x]
    #             x -= 1
    #             length -= 1
    #         x += 1
    #     # print("str_list:", str_list)
    #     time_list = [int(i) for i in self.str_list]
    #
    #     time1 = (time_list[0] * 10 + time_list[1]) * 3600 + (time_list[2] * 10 + time_list[3]) * 60 + \
    #             (time_list[4] * 10 + time_list[5])
    #     time2 = (time_list[6] * 10 + time_list[7]) * 3600 + (time_list[8] * 10 + time_list[9]) * 60 + \
    #             (time_list[10] * 10 + time_list[11])
    #     rst = time2 - time1
    #     # msg = "running time: {} s".format(rst)
    #     # print(msg)
    #     self.data_df_simulator.loc[spfileID, "Simulatorcost"] = rst
    #     self.autoRunlogfile.write("    " + str(rst))

    def output_file_parser(self, file_name):
        fo = open(file_name, "r")
        #def a list with nodes startwith "Title"
        nodelists = []
        #def a list with single node
        nodelist = []
        output_file = fo.readlines()
        notenum = 0
        plotname_arr = []
        #def a flag
        flag = 1
        for i, line in enumerate(output_file):
            if i != 0 and line.startswith('Title'):
                nodelists.append(nodelist)
                flag = 0
                nodelist = []
                nodelist.append(line)
            elif line.startswith('#') or line.startswith(' \n'):
                notenum += 1
                pass
            else:
                nodelist.append(line)
        if flag:
            nodelists.append(nodelist)
        nodelistsresult = {}
        # read the number of variables and number of points
        for titles in nodelists:
            number_of_variables = int(titles[4].split(':', 1)[1])
            # number_of_points = int(titles[5].split(':', 1)[1])
            plotname = titles[2].split(': ')[-1].split('\n')[0]
            plotname_arr.append(plotname)
            nodelistsresult[plotname] = {}
            # print(number_of_variables, number_of_points)

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

            #if this node is PSS
            # if titles[2].split(': ')[-1] in ["Oscillator Steady State Analysis", "Periodic Steady State Analysis"]:
            #     results["PSS"] = "PSSvalue "
            # else:
            #     results["PSS"] = "value "

            for value in titles[8 + number_of_variables + 1:]:
                if variable_index != number_of_variables - 1:
                    # print(variable_index)
                    # print(variable_name[variable_index])
                    vlu = eval(value.split('\t', -1)[-1])
                    if type(vlu) == tuple:
                        results[variable_name[variable_index]].append(vlu[0])
                    else:
                        results[variable_name[variable_index]].append(vlu)
                    variable_index += 1
                else:
                    vlu = eval(value.split('\t', -1)[-1].split('\n')[0])
                    if type(vlu) == tuple:
                        results[variable_name[variable_index]].append(vlu[0])
                    else:
                        results[variable_name[variable_index]].append(vlu)
                    variable_index = 0
            nodelistsresult[plotname] = results
        # close the output_file
        fo.close()
        assert len(nodelistsresult) > 0
        # print(plotname_arr)
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

    def AlignDataLen(self, outdata, refdata):
        flag = 0
        while len(outdata) != len(refdata):
            num_dif = np.abs(len(outdata) - len(refdata))

            if len(outdata) > len(refdata):
                if flag:
                    delvalues = np.random.choice(outdata, num_dif, replace=False)
                    for v in delvalues:
                        outdata.remove(v)
                else:
                    indexs = np.arange(11, len(outdata), int(len(outdata) / num_dif))
                    outdata = np.delete(np.array(outdata), indexs).tolist()
            else:
                if flag:
                    delvalues = np.random.choice(refdata, num_dif, replace=False)
                    for v in delvalues:
                        refdata.remove(v)
                else:
                    indexs = np.arange(11, len(refdata), int(len(refdata) / num_dif))
                    refdata = np.delete(np.array(refdata), indexs).tolist()
            flag = 1

        return outdata, refdata


    def calc_error(self,original_results_dict, new_results_dict):

        plotname_nodes = []
        plotnames = original_results_dict.keys()
        check_nodes = []
        for plotname in plotnames:
            node_dict = original_results_dict[plotname]
            nodes = node_dict.keys()
            for node in nodes:
                plotname_nodes.append('^^^'.join((plotname, node)))
        if self.faster:
            try:
                random_3_node = np.random.choice(plotname_nodes, 3, replace=False)
                check_nodes = random_3_node
            except Exception as e:
                print(plotname_nodes)
                print(e)
        else:
            check_nodes = plotname_nodes

        comp_result = {}
        comparelist = []
        for plotname_node in check_nodes:
            plotn = plotname_node.split('^^^')[0]
            noden = plotname_node.split('^^^')[1]
            outdata = original_results_dict[plotn][noden]
            refdata = new_results_dict[plotn][noden]

            if plotn in ["Oscillator Steady State Analysis", "Periodic Steady State Analysis"]:
                #calc period1
                x1 = original_results_dict[plotn]['time']
                y1 = original_results_dict[plotn][noden]
                doubeldiff1 = np.diff(np.sign(np.diff(y1)))
                peak_locations1 = np.where(doubeldiff1 == -2)[0] + 1
                trough_locations1 = np.where(doubeldiff1 == 2)[0] + 1
                if len(peak_locations1.tolist()) >= 2:
                    period1 = x1[peak_locations1[1]] - x1[peak_locations1[0]]
                else:
                    if len(trough_locations1.tolist()) >= 2:
                        period1 = x1[trough_locations1[1]] - x1[trough_locations1[0]]
                    else:
                        period1 = np.mean(y1)

                #calc period2
                x2 = new_results_dict[plotn]['time']
                y2 = new_results_dict[plotn][noden]
                doubeldiff2 = np.diff(np.sign(np.diff(y2)))
                peak_locations2 = np.where(doubeldiff1 == -2)[0] + 1
                trough_locations2 = np.where(doubeldiff1 == 2)[0] + 1
                if len(peak_locations2.tolist()) >= 2:
                    period2 = x2[peak_locations2[1]] - x2[peak_locations2[0]]
                else:
                    if len(trough_locations2.tolist()) >= 2:
                        period2 = x2[trough_locations2[1]] - x2[trough_locations2[0]]
                    else:
                        period2 = np.mean(y2)

                #compare period
                if int(period1*10000)/10000 == int(period2*10000)/10000:
                    compare = True
                else:
                    compare = False
                comp_result[plotname_node] = str([period1, period2])


            else:

                outdata, refdata = self.AlignDataLen(outdata, refdata)
                assert len(refdata) == len(outdata)

                rmse = self.get_rmse(outdata, refdata)
                # rmse = self.get_ae(outdata, refdata)
                comp_value = 1e-3 if np.average(outdata) == 0 else np.abs(np.average(outdata))
                compareflag = True if rmse <= comp_value or rmse < 1e-5 else False
                comp_result[plotname_node] = str((rmse, comp_value, compareflag))
                comparelist.append(compareflag)
                compare = False if False in comparelist else True
        return compare, str(comp_result)

    def BinaryOut(self, outFile):
        for file in self.binaryfiles:
            if file in outFile:
                return True, file
        return False, None

    def CompareBinaryFile(self, outfile, binaryoutfile):
        results_1_dict, plotname_arr = self.output_file_parser(outfile)
        binaryoutfilenew = binaryoutfile.replace('/', '\\')
        nodes = self.BinaryData[self.BinaryData["outFile"] == binaryoutfilenew].node.values.tolist()
        com_result = {}
        comparelist = []
        for noden in nodes:
            index = self.BinaryData.loc[(self.BinaryData["outFile"] == binaryoutfilenew) & (self.BinaryData["node"] == noden)].index.values.tolist()[0]
            plotn = self.BinaryData.loc[index].Analysis
            plotname_node = "^^^".join((plotn, noden))
            src_out_data = results_1_dict[plotn][noden]
            dst_out_data = ast.literal_eval(self.BinaryData.loc[index].data)
            src_out_data, dst_out_data = self.AlignDataLen(src_out_data, dst_out_data)
            assert len(src_out_data) == len(dst_out_data)
            rmse = self.get_rmse(src_out_data, dst_out_data)
            # rmse = self.get_ae(src_out_data, dst_out_data)
            comp_value = 1e-3 if np.average(src_out_data) == 0 else np.abs(np.average(src_out_data))
            compareflag = True if rmse <= comp_value or rmse < 1e-5 else False
            com_result[plotname_node] = str((rmse, comp_value, compareflag))
            comparelist.append(compareflag)
            compare = False if False in comparelist else True
        return compare, str(com_result), plotname_arr




    def diffout(self):
        for j in range(1, self.spfile_Num+1):
            if self.data_df_diff.loc[j].SimulatorStat and self.data_df_diff.loc[j].LinuxRefoutFile:
                outfile = self.data_df_diff.loc[j].outFile
                print(outfile)
                LinuxRefoutfile = self.data_df_diff.loc[j].LinuxRefoutFile
                binary_out, binaryoutfile = self.BinaryOut(LinuxRefoutfile)
                plotname_arr = []
                if binary_out:
                    compare, com_result, plotname_arr = self.CompareBinaryFile(outfile, binaryoutfile)
                else:
                    compare = None
                    com_result = str({})
                    if os.path.exists(outfile) and os.path.exists(LinuxRefoutfile):
                        results_1_dict, plotname_arr = self.output_file_parser(outfile)
                        results_2_dict, plotname_arr = self.output_file_parser(LinuxRefoutfile)
                        # result = self.root_mean_squared_error(results_1_dict, results_2_dict)
                        compare, com_result = self.calc_error(results_1_dict, results_2_dict)
                self.data_df_diff.loc[j, "outdiff"] = compare
                self.data_df_diff.loc[j, "AnalysisType"] = ','.join(str(i) for i in plotname_arr)

                self.data_df_diff.loc[j, "outdiffdetail"] = com_result




if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--tp", type=str, default="./", help="path to test")
    parser.add_argument("--update", type=int, default=1, help="update out file")
    parser.add_argument("--sh", type=str, default='/mnt/btdsim_for_centos7_hl_v3.2/user/', help="update out file")
    parser.add_argument("--f", type=int, default=1, help="check all nodes")
    opt = parser.parse_args()
    print(opt)
    print("Start AutoSimulator...")
    atc = AutoTestCls(opt)
    atc.sim_folder()
    print("Total: %d files (.sp .scs or .cir)\n" % (atc.spfile_Num))
    print("start check out file...")
    atc.global_out_check()
    date_str=time.strftime("%m%d%H%M%S", time.localtime())
    writer1 = pd.ExcelWriter('data_df_simulator_'+date_str+'.xlsx')
    atc.data_df_simulator.to_excel(writer1)
    writer1.save()
    print("start diff out file...")
    atc.diffout()
    writer2 = pd.ExcelWriter('data_df_diff_'+date_str+'.xlsx')
    atc.data_df_diff.to_excel(writer2)
    writer2.save()
