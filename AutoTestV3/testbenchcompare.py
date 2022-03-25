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
from matplotlib import pyplot as plt
import collections
from tool_utils import get_rmse, get_mape, AlignDataLen


class AutoTestCls():
    # 定义、创建对象初始化
    def __init__(self, opt):
        self.spfile_Num = 0
        self.line_list = []
        self.time_list = []
        self.str_list = []
        self.test_dir = opt.tp
        self.ref_filename = 'bench'
        self.cases_nodes_path = "cases_nodes.xlsx"
        self.sh = opt.sh

        # def logfile
        self.autoRunlogfile = open("./output/autoRun.log", "a")
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
        self.check_nodes_dict = dict()
        nodes_df = pd.read_excel(self.cases_nodes_path, index_col=0)  # 指定第一列为行索引
        for row in range(1, len(nodes_df) + 1):
            row_value = nodes_df.loc[row, 'nodes'].split(", ")
            self.check_nodes_dict[row] = row_value


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
        nodelistsresult = collections.OrderedDict()
        # read the number of variables and number of points
        for titles in nodelists:
            number_of_variables = int(titles[4].split(':', 1)[1])
            plotname = titles[2].split(': ')[-1].split('\n')[0]
            plotname_arr.append(plotname)
            nodelistsresult[plotname] = collections.OrderedDict()

            # read the names of the variables
            variable_name_unit = []
            for variable in titles[8:8 + number_of_variables]:
                # 取节点名
                var_name = variable.split('\t', -1)[2]
                # 取节点单位
                var_unit = variable.split('\t', -1)[3].split('\n')[0]
                #节点名和单位之间用----拼接，赋给variable_name_unit
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
                    vlu = eval(st)
                    #如果是虚数，out文件中会有两个值，我们只取实部
                    if type(vlu) == tuple:
                        results[variable_name_unit[variable_index]].append(vlu[0])
                    else:
                        results[variable_name_unit[variable_index]].append(vlu)
                    variable_index += 1
                else:
                    st = value.split('\t', -1)[-1].split('\n')[0]

                    #如果out文件中出现Fail字符串，将其转换成0
                    if st.startswith("FAIL"):
                        st = "0"
                    vlu = eval(st)
                    if type(vlu) == tuple:
                        results[variable_name_unit[variable_index]].append(vlu[0])
                    else:
                        results[variable_name_unit[variable_index]].append(vlu)
                    variable_index = 0
            nodelistsresult[plotname] = results
        # close the output_file
        fo.close()

        assert len(nodelistsresult) > 0
        return nodelistsresult, plotname_arr

    #根据netlist name 获取 caseindex,后续根据caseindex去找对应的输出节点
    def getCaseIndex(self, index):
        netfile = self.data_df_simulator.loc[index].netFile
        # netfile: /home/IC/Case_wayne/TestBench_1BaseCases1/>>>>>case1<<<<<</VCO/lab1_pss_pnoise_btd.scs
        caseindex = netfile.split('/case')[1].split('/')[0]
        # print(caseindex)
        return int(caseindex)

    def calc_error(self, index, original_results_dict, new_results_dict):

        plotname_nodes = []
        #获取所有的plotnames
        plotnames = original_results_dict.keys()

        for plotname in plotnames:
            node_dict = original_results_dict[plotname]

            #获取所有的nodename
            nodes = node_dict.keys()
            for node in nodes:
                plotname_nodes.append('--'.join((plotname, node)))

        # 读取case number，作为index找到对应case需要查看的节点
        caseindex = self.getCaseIndex(index)
        check_nodes = self.check_nodes_dict[caseindex]

        comp_result = {}
        comparelist = []
        for plotname_node in check_nodes:
            plotn = plotname_node.split('--')[0]
            noden = plotname_node.split('--')[1]

            out_plot = original_results_dict[plotn]
            ref_plot = new_results_dict[plotn]

            for xname_unit, xvalue in out_plot.items():
                outx = xvalue
                break

            for xname_unit, xvalue in ref_plot.items():
                refx = xvalue
                break

            for nodename in out_plot.keys():
                if nodename.startswith(noden):
                    outdata = out_plot[nodename]
                    refdata = ref_plot[nodename]

            # 对齐数据
            if len(refdata) != len(outdata):
                _, outdata, refdata = AlignDataLen(outx, refx, outdata, refdata)

            assert len(refdata) == len(outdata)

            # 评估指标
            if opt.metric == "RMSE":
                rmse = get_rmse(outdata, refdata)
                # rmse = self.get_ae(outdata, refdata)
                comp_value = 1e-3 if np.average(outdata) == 0 else np.abs(np.average(outdata))
                compareflag = True if rmse <= comp_value or rmse < 1e-5 else False
                comp_result[plotname_node] = str((rmse, comp_value, compareflag))

            else:
                mape = get_mape(outdata, refdata)
                comp_value = 1e-3 if np.average(outdata) > 1e-6 else 1
                compareflag = True if mape <= comp_value else False
                comp_result[plotname_node] = str((mape, comp_value, compareflag))
            comparelist.append(compareflag)
            compare = False if False in comparelist else True
        return compare, str(comp_result)

    def save_plot(self, index, out_results_dict, ref_results_dict, compare):
        # 根据对比结果定义标题颜色
        titlecolor = 'green' if compare else 'red'

        plotname_nodes = []
        plotnames = out_results_dict.keys()

        for plotname in plotnames:
            node_dict = out_results_dict[plotname]
            nodes = node_dict.keys()
            for node in nodes:
                plotname_nodes.append('--'.join((plotname, node)))

        # 读取case number，作为index找到对应case需要查看的节点
        caseindex = self.getCaseIndex(index)
        check_nodes = self.check_nodes_dict[caseindex]


        for plotname_node in check_nodes:
            plotn = plotname_node.split('--')[0]
            noden = plotname_node.split('--')[1]
            out_plot = out_results_dict[plotn]
            ref_plot = ref_results_dict[plotn]

            #得到第一个nodename、单位、值，因为plotname中第一个节点会作为后续节点画图的横坐标
            for xname_unit, xvalue in out_plot.items():
                out_xname = xname_unit.split('----')[0]
                out_xunit = xname_unit.split('----')[1]
                outx = xvalue
                break

            #因为refout节点名和单位一致，所以不用重复获取
            for xname_unit, xvalue in ref_plot.items():
                refx = xvalue
                break



            for nodename in out_plot.keys():
                if nodename.startswith(noden):
                    #得到y轴的单位
                    yunit = nodename.split("----")[1]
                    #得到y轴的数据
                    outdata = out_plot[nodename]
                    refdata = ref_plot[nodename]

            #长度不一致需做数据对齐
            if len(refdata) != len(outdata):
                xnew, outdata, refdata = self.AlignDataLen(outx, refx, outdata, refdata)
            else:
                xnew = outx

            assert len(refdata) == len(outdata)

            if len(outdata) == 1:
                continue

            # 折线图还是柱状图
            # print("Spectrum" in noden)
            # print(noden)
            # 如果是频谱图，画柱状图
            if "Spectrum" in plotn:
                #设置柱状图y轴的起始值
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
                for i in range(len(xnew)):
                    xnew[i] = xnew[i] + width
                plt.bar(xnew, refdata, width=width, color='r', label='refdata', bottom=bottomvalue)
                plt.xticks(rotation=90)  # 横坐标旋转45度
                plt.xlabel(out_xname + "(" + out_xunit + ")")  # 横坐标标签
                plt.ylabel(noden + "(" + yunit + ")")  # 纵坐标标签
                plt.title(plotname_node, backgroundcolor=titlecolor)  # bar图标题
                # plt.grid(axis='x')
                plt.legend(loc='best')
                savepath = "./output/case" + str(caseindex) + "_" + plotname_node + '.jpg'
                plt.savefig(savepath)
                # plt.show()
                plt.close()

            #否则，画折线图
            else:# plot

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

                plt.plot(xnew, outdata, 'b', label='outdata')  # (横坐标，纵坐标)
                plt.plot(xnew, refdata, 'r', label='refdata')  # (横坐标，纵坐标)
                plt.xlabel(out_xname + "(" + out_xunit + ")")  # 横坐标标签
                plt.ylabel(noden + "(" + yunit + ")")  # 纵坐标标签
                plt.grid()
                plt.title(plotname_node, backgroundcolor=titlecolor)  # 折线图标题

                plt.legend(loc='best')

                savepath = "./output/case" + str(caseindex) + "_" + plotname_node + '.jpg'
                plt.savefig(savepath)
                # plt.show()
                plt.close()


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

                    # 计算误差
                    compare, com_result = self.calc_error(j, results_1_dict, results_2_dict)

                    # 如果参数指定了保存图片，则开始画图
                    if opt.savefig:
                        self.save_plot(j, results_1_dict, results_2_dict, compare)
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
    parser.add_argument("--savesimcsv", type=bool, default=True, help="save final simulator csv file")
    parser.add_argument("--savediffcsv", type=bool, default=True, help="save final diff csv file")
    parser.add_argument("--savefig", type=bool, default=True, help="save final plot")
    parser.add_argument("--metric", type=str, default="MAPE", help="select metrics for diff, i.e. RMSE or MAPE")
    opt = parser.parse_args()
    print(opt)

    os.makedirs("output", exist_ok=True)

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

    date_str = time.strftime("%m%d%H%M%S", time.localtime())
    if opt.savesimcsv:
        # 将仿真结果写入excel
        writer1 = pd.ExcelWriter('./output/data_df_simulator_' + date_str + '.xlsx')
        atc.data_df_simulator.to_excel(writer1)
        writer1.save()

    # 仿真结果对比，并写入excel
    print("start diff out file...")
    if opt.savediffcsv:
        atc.diffout()
        writer2 = pd.ExcelWriter('./output/data_df_diff_' + date_str + '.xlsx')
        atc.data_df_diff.to_excel(writer2)
        writer2.save()
