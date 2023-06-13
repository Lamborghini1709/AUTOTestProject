# coding=utf-8
#!/usr/bin/env python

from data_parse import DataPaser
import time
import os
from calc_utils import get_rmse, get_mape, AlignDataLen, max_diff, cos_sim
import multiprocessing as mp
from matplotlib import pyplot as plt
import numpy as np

class DataDiff(DataPaser):
    def __init__(self, opt):
        super(DataDiff, self).__init__(opt)
        print("start diff out file...")
        thread_list2 = []
        self.diffout(thread_list2)

        for t2 in thread_list2:
            t2.start()
            time.sleep(1)

        for t2 in thread_list2:
            t2.join()

    def diffout(self, thread_list2):
        for netId in range(1, self.spfile_Num + 1):
            self.diff_data[netId] = mp.Manager().dict()
            t2 = mp.Process(target=self.calc_deviation, args=(netId,), daemon=True)
            thread_list2.append(t2)

    def calc_deviation(self, netId):
        start = time.time()
        tag = 1
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
                    if self.savefig:
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
                        if self.metric == "RMSE":
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

