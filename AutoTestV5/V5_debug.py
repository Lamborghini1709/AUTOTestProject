# coding=utf-8
#!/usr/bin/env python

import pandas as pd
from sql_utils import DBConnect

# cases_nodes_path = "./AutoTestV5/RegressCaseInfos.xlsx"
# nodes_df = pd.read_excel(cases_nodes_path, index_col=0)  # 指定第一列为行索引
con = DBConnect("10.1.10.13", 5555, "AutoTest", "Test@123456", "AutoTest")

# sql = """INSERT INTO caseInfos 
#         (id, CaseName, Netlist, OldPath, Analysis, Model, CircuitType, NumberOfNodes, NumberOfDevice, `Description`, Grammar, Nodes)
#         VALUE 
#         """
# nd_keys = nodes_df.keys()
# for i in list(nodes_df.index):
#     a = f"({i},"
#     for k in nd_keys:
#         a += '"' +str(nodes_df.loc[i, k]) + '", '
#     sql1 = sql + a[0:-2]+")"
#     data = con.execute_d(sql1)
#     # print(sql1)

# con.close()
sql = "SELECT * FROM caseInfos  WHERE (FIND_IN_SET('cmg107', model) OR FIND_IN_SET('bulk106.1', model)) AND FIND_IN_SET('tran', Analysis)"
data = con.query_d(sql)
print(data)

    
