
# coding=utf-8 

import argparse
import pandas as pd
import numpy as np
import os

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
        self.si = opt.si
        self.version = opt.btdVersion
        self.dir_dict = {
            "all": "All_regress_Cases",
            "hisi": "hisiCaseAll",
            "huali": "regress_Cases_all-cmg-bulk_20230307-1400",
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

        # def dataform2
        data_df_diff = np.arange(1, 17).reshape((1, 16))
        self.data_df_diff = pd.DataFrame(data_df_diff)
        self.data_df_diff.columns = ['index', 'spFile', 'logFile', 'outFile', 'RefoutFile', 'ReflogFile','AnalysisType',
                                     'SimulatorStat', 'Simulatorcost', "time_div", "cost_div","cputime_rate","walltime_rate",
                                     "outdiff", "outdiffCost", "outdiffdetail"]
        self.data_df_diff = self.data_df_diff.set_index(['index'])

        self.is_netlist = lambda x: any(x.endswith(extension)
                                        for extension in ['.sp', '.cir', 'scs'])


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
    
    def InitCaseForm(self):
        if isinstance(self.case_dir, str):
            # 遍历目录下的所有文件
            for filepath, dirnames, filenames in os.walk(self.case_dir, topdown=False):
                for filename in filenames:
                    if self.is_netlist(filename):
                        # sp文件
                        netfile = os.path.join(filepath, filename)
                        caseindex = netfile.split('case')[1].split('/')[0]
                        if self.si == "huali" and caseindex >=1000:
                            continue
                        elif self.si == "hisi" and caseindex <=1000:
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
                        ref_log = os.path.join(ref_path,os.path.basename(logFile))

                        # diff result
                        Simulatordiff = None

                        # diff result detail
                        outdiffdetail = {}
                        
                        # diff time_div
                        time_div = None
                        cost_div = None
                        outdiffCost = None
                        cputime_rate = None
                        walltime_rate =None
                        self.data_df_diff.loc[self.spfile_Num] = [netfile, logFile, outFile, ref_file, ref_log, AnalysisType,
                                                                  SimulatorStat, Simulatorcost, time_div, cost_div, cputime_rate,
                                                                  walltime_rate, Simulatordiff,outdiffCost,outdiffdetail]
        else:
            print("Please specify the test folder in string format.")



    def cp_log_file(self):
        for id in range(1,self.spfile_Num+1):
            logfile = self.data_df_diff.loc[id,"logFile"]
            reflogfile = self.data_df_diff.loc[id,"ReflogFile"]
            cpCmd = f"mv {logfile} {reflogfile}"
            if os.path.exists(logfile):
                print("INFO CP CMD: " + cpCmd )
                os.system(cpCmd)

    def rename_benchout(self):
        for id in range(1,self.spfile_Num+1):
            outfile = self.data_df_diff.loc[id,"outFile"]
            ref_path = os.path.join(os.path.dirname(outfile), self.ref_filename)
            ref_outfile = self.data_df_diff.loc[id,"RefoutFile"]
            refoutfile_name = os.path.basename(ref_outfile)
            refoutfile_newname = refoutfile_name + ".20230505"
            ref_newoutfile = os.path.join(ref_path,refoutfile_newname)
            mvCmd = f"mv {ref_outfile} {ref_newoutfile}" 
            if os.path.exists(ref_outfile):
                print("INFO CP CMD: " + mvCmd )
                os.system(mvCmd)


    def cp_benchout(self):
        for id in range(1,self.spfile_Num+1):
            ref_outfile = self.data_df_diff.loc[id,"RefoutFile"]
            outfile = self.data_df_diff.loc[id,"outFile"]
            cpCmd = f"mv {outfile} {ref_outfile}"
            if os.path.exists(outfile):
                print("INFO CP CMD: " + cpCmd )
                os.system(cpCmd)



if __name__ == '__main__':
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
    parser.add_argument("-b", "--btdVersion", type=str, default="rf", help="btdsim version: base, plus, rf")
    parser.add_argument("--ccost", type=str, default=1, help="Simulatorcost Compare")
    parser.add_argument("--logtime", type=int, default=0, help="Whether to compare the cputime and walltime")
    opt = parser.parse_args()
    print(opt)

    atc = AutoTestCls(opt)
    atc.InitCaseForm()
    atc.rename_benchout()
    atc.cp_log_file()
    atc.cp_benchout()