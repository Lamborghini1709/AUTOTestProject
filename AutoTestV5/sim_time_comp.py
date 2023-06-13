# coding=utf-8
#!/usr/bin/env python

from data_diff import DataDiff

class SimTimeComp(DataDiff):
    def __init__(self, opt):
        super(SimTimeComp, self).__init__(opt)
        self.update_df_data()
        if opt.ccost == 1:
            print("start check out simulator cost...")
            self.time_divcheck()
        if opt.logtime == 1:
            print("start check out log CPU time and Wall time...")
            self.diff_logtime()
    
    def time_divcheck(self):
        for id in range(1,self.spfile_Num+1):
            if self.data_df_diff.loc[id].SimulatorStat:
                simulator_cost = self.data_df_diff.loc[id, "Simulatorcost"]
                caseindex = self.getCaseIndex(id)
                stand_cost = self.check_time_dict[caseindex]
                if float(simulator_cost) >= 100:
                    diff_cost = (simulator_cost - stand_cost)/ stand_cost *100
                    tag = self.case_limit[caseindex]
                    self.data_df_diff.loc[id,"cost_div"] = '%.3f'%diff_cost+"%"
                    if diff_cost<= 20 :
                        self.data_df_diff.loc[id,"time_div"] = 1                  
                    elif diff_cost>20:
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
                    self.data_df_diff.loc[id,"time_div"] = 1

    # 从 log 里获取 CPU_time 和 Wall_time
    def get_logtime(self,fp):
        log_time = {}
        with open(fp, "r", encoding='latin-1') as f:
            content = f.readlines()
            for line in range(0,len(content)):
                if content[line].startswith("Total CPU time(s):"):
                    CPU_time = content[line].split(":")[-1]
                    log_time["CPU_time"] = CPU_time
                elif content[line].startswith("Total Wall time(s):"):
                    Wall_time = content[line].split(":")[-1]
                    log_time["Wall_time"] = Wall_time
            return log_time

    # 当前log 文件 CPU_time / Wall_time 和 bench 文件夹中 log 文件 CPU_time / Wall_time 的比率
    # （只对仿真时间超过 100s 的进行比较）
    def diff_logtime(self):
        for id in range(1,self.spfile_Num+1):            
            fp1 = self.data_df_diff.loc[id, "logFile"]
            fp2 = self.data_df_diff.loc[id, "ReflogFile"]
            logtime = self.get_logtime(fp1)
            golden_logtime = self.get_logtime(fp2)
            log_cputime = float(logtime["CPU_time"])
            log_walltime = float(logtime["Wall_time"])
            golden_cputime = float(golden_logtime["CPU_time"])
            golden_walltime = float(golden_logtime["Wall_time"])
            if log_cputime > 100 or log_walltime > 100:
                cputime_rate = (log_cputime - golden_cputime) / golden_cputime *100
                walltime_rate = (log_walltime - golden_walltime) / golden_walltime *100
                self.data_df_diff.loc[id,"cputime_rate"] = '%.3f'%cputime_rate+"%"
                self.data_df_diff.loc[id,"walltime_rate"] = '%.3f'%walltime_rate+"%"




    def update_df_data(self):
        for netId in self.sim_data.keys():
            self.data_df_simulator.loc[netId, "Simulatorcost"] = self.sim_data[netId]["Simulatorcost"]
            self.data_df_diff.loc[netId, "Simulatorcost"] = self.sim_data[netId]["Simulatorcost"]

        for netId in self.diff_data.keys():
            self.data_df_diff.loc[netId, "AnalysisType"] = self.diff_data[netId]["AnalysisType"]
            self.data_df_diff.loc[netId, "outdiff"] = self.diff_data[netId]["outdiff"]
            self.data_df_diff.loc[netId, "outdiffdetail"] = self.diff_data[netId]["outdiffdetail"]
            self.data_df_diff.loc[netId, "outdiffCost"] = self.diff_data[netId]["outdiffCost"]