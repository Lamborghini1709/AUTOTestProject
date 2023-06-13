# coding=utf-8
#!/usr/bin/env python

import pymysql

class DBConnect(object):
    def __init__(self, host, port, user, pwd, database) -> None:
        self.host = host
        self.port = port
        self.user = user
        self.pwd = pwd
        self.db = database
        self.con = pymysql.connect(
            host = self.host, 
            user = self.user, 
            passwd = self.pwd, 
            port = self.port, 
            db = self.db)
        # self.cursor = con.cursor()
    
    # def execute(self, sql):
    #     self.cursor.execute(sql)
    #     data = self.cursor.fetchall()
    #     return data

    def query_d(self, sql):
        # select data, or create、drop table
        cur = self.con.cursor(pymysql.cursors.DictCursor)
        cur.execute(sql)
        data = cur.fetchall()
        cur.close()
        return data

    def execute_d(self, sql):
        # insert、update、delete
        try:
            cur = self.con.cursor()
            cur.execute(sql)
            self.con.commit()
            cur.close()
            print("INFO: execute succeed")
        except:
            self.con.rollback()
            print(f"ERROR SQL: {sql}")
            print("ERROR: execute failed, has been rolled back")       

    def close(self):
        self.con.close()
        

if __name__=="__main__":
    import pandas as pd
    import numpy as np
    import tools_utils
    con = DBConnect("10.1.10.13", 5555, "AutoTest", "Test@123456", "AutoTest")
    sql = "SELECT * FROM caseInfos  WHERE (FIND_IN_SET('cmg107', model) OR FIND_IN_SET('bulk106.1', model)) AND FIND_IN_SET('tran', Analysis)"
    data = con.query_d(sql)
    # sql2 = "select * from caseInfos where id=2"
    # data2 = con.query_d(sql2)
    con.close()
    # print(data)
    # print(data2)
    data_simulator = np.arange(1, 6).reshape((1, 5))
    data_df_simulator = pd.DataFrame(data_simulator)
    data_df_simulator.columns = ['index', 'caseN', 'netFile', 'logFile', 'outFile']
    data_df_simulator = data_df_simulator.set_index(['index'])
    spfile_Num = 0
    nc = []
    for row in data:
        spfile_Num += 1
        netfile = row["Netlist"]
        logFile = tools_utils.change_suffix(netfile, "log")
        outFile = tools_utils.change_suffix(netfile, 'out')
        caseN = row["CaseName"]
        nc.append(row["id"])
        data_df_simulator.loc[spfile_Num] = [caseN, netfile, logFile, outFile]
    # print(data_df_simulator)
    print(nc)
    outputpath = "./V5_Regress"
    aa = f"cp -r /home/mnt/V5_Regress/case{nc}  {outputpath}"
    print(aa)


