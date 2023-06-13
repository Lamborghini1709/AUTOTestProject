# coding=utf-8
#!/usr/bin/env python

from sim_time_comp import SimTimeComp
import os
import pandas as pd
import time

class ResultStat(SimTimeComp):
    def __init__(self, opt):
        super(ResultStat, self).__init__(opt)
        date_str = time.strftime("%m%d%H%M%S", time.localtime())
        if opt.savesimcsv:
            writer1 = pd.ExcelWriter(f'{self.output_folder}/data_df_simulator_{date_str}.xlsx')
            self.data_df_simulator.to_excel(writer1)
            writer1.save()

        # 将对比结果写入excel
        if opt.savediffcsv:  
            writer2 = pd.ExcelWriter(f'{self.output_folder}/data_df_diff_{date_str}.xlsx')
            self.data_df_diff.to_excel(writer2)
            writer2.save()
        
        self.result_statistics()
        self.bench_error_data()

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
        r = open(f"{self.test_dir}/result_statistics.txt", "w")
        r.write(f"本次回归测试共执行{t+f}条case, 其中:\n")
        r.write(f"    仿真成功: {t} 条\n")
        r.write(f"    仿真成功case中对比时间超过golden 20%的： {c}条\n")
        r.write(f"    仿真失败: {f} 条\n")
        r.write(f"    结果对比成功: {dt} 条\n")
        r.write(f"    结果对比失败: {df} 条\n")
        r.close()
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
        test_set = self.dir_dict[self.testset]
        if len(failed_df) > 0:
            os.system(f"mkdir /home/mnt/bencherror/{date_str}_{self.dir_dict[self.testset]}")
            for i in list(failed_df.index):
                aa = failed_df.loc[i, "spFile"]
                bb = aa.split(test_set)
                cc = bb[1].split("/")[1]
                dd = f"{bb[0]}{test_set}/{cc}" 
                copyCmd = f"cp -r {dd} /home/mnt/bencherror/{date_str}_{self.dir_dict[self.testset]}/"
                os.system(copyCmd)
            os.system(f"cp -r {self.output_folder} /home/mnt/bencherror/{date_str}_{self.dir_dict[self.testset]}/")
            print(f"INFO: 回归失败案例存放 ip: 10.1.10.11 用户名 test 密码 testing")
            print(f"INFO: 回归失败案例已整理至 /home/mnt/bencherror/{date_str}_{self.dir_dict[self.testset]}/ 目录")


    def outputTerm(self):
        df = self.data_df_diff
        failed_df = df[(df['SimulatorStat'] == 0) | (df['outdiff'] == False) |  (df['time_div'] == 0) | (df['outdiff'].isna())]
        # 可以在大数据量下，没有省略号
        if len(failed_df) > 0:
            print("INFO: 总计失败：" + str(len(failed_df)) + "个用例" + "\n")
            pd.set_option('display.max_columns', 1000000)
            pd.set_option('display.max_rows', 1000000)
            pd.set_option('display.max_colwidth', 1000000)
            pd.set_option('display.width', 1000000)
            # print(failed_df.loc[:, ['spFile', 'SimulatorStat', 'Simulatorcost', 'cost_div', 'outdiff']])
        
            sim_fail_df = failed_df[failed_df['SimulatorStat'] == 0]
            print(f"\nWARNING 仿真失败: {len(sim_fail_df)}条")
            print(sim_fail_df.loc[:, ['spFile', 'SimulatorStat', 'Simulatorcost', 'cost_div', 'outdiff']])

            diff_fail_df = failed_df[(failed_df['SimulatorStat'] == 1) & ((failed_df['outdiff'] == False) | (failed_df['outdiff'].isna()))]
            print(f"\nWARNING 结果对比失败: {len(diff_fail_df)}条")
            print(diff_fail_df.loc[:, ['spFile', 'SimulatorStat', 'Simulatorcost', 'cost_div', 'outdiff']])

            time_out_df = failed_df[(failed_df['SimulatorStat'] == 1) & (failed_df['time_div'] == 0) & (failed_df['outdiff'] == True)]
            print(f"\nWARNING 对比时间超过 golden 20%: {len(time_out_df)}条")
            print(time_out_df.loc[:, ['spFile', 'SimulatorStat', 'Simulatorcost', 'cost_div', 'outdiff']])
        else:
            print(f"INFO: 无失败案例,测试集case全部仿真成功,对比成功,仿真时间未超20%,回归测试通过")

        return len(failed_df['spFile'])