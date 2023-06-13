# coding=utf-8
#!/usr/bin/env python

from sim import Simulator
import os

class LogPaser(Simulator):
    def __init__(self, opt):
        super(LogPaser, self).__init__(opt)
        print("start check out simulator stat...")
        self.global_log_check()

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
                    self.autoRunlogfile.write(f'{spfile}, YES\n')
                else:
                    SimulatorStat = 0
                    self.data_df_simulator.loc[id, "Simulatorcost"] = None
                    self.data_df_diff.loc[id, "Simulatorcost"] = None
                    self.autoRunlogfile.write(f'{spfile}, NO\n')
                self.data_df_simulator.loc[id, "SimulatorStat"] = SimulatorStat
                self.data_df_diff.loc[id, "SimulatorStat"] = SimulatorStat
            # print out_file;
        print("log file check is OK.")
        print("The result is in autoRun.log.")


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
