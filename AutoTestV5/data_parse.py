# coding=utf-8
#!/usr/bin/env python

from log_paser import LogPaser
import collections

class DataPaser(LogPaser):
    def __init__(self,opt):
        super(DataPaser, self).__init__(opt)
    
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

