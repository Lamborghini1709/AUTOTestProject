# -*- coding: utf-8 -*-
# @Time : 2022/4/12 15:12 
# @Author : wayne
# @File : GeneralComparsionAPP.py 
# @Software: PyCharm

import argparse
import os

class GeneralComparsionCls():
    # 定义、创建对象初始化
    def __init__(self, opt):
        self.silver_points = None
        self.golden_points = None
        self.AEthreshold = 0
        self.REthreshold = 0
        self.com_result = False
        self.reports_AE = {}
        self.reports_RE = {}
        self.sort_report_outliers = None

    def set_silver_points(self, filepath):
        pass

    def set_golden_points(self, filepath):
        pass

    def set_AEthreshold(self, AEthreshold):
        self.AEthreshold = AEthreshold

    def set_REthreshold(self, REthreshold):
        self.REthreshold = REthreshold

    def get_comp_resut(self):
        return self.com_result

    def get_reports_AE(self):
        return self.reports_AE

    def get_reports_RE(self):
        return self.reports_RE

    def get_sort_report_outliers(self):
        return self.sort_report_outliers


if __name__ == '__main__':

    inputs = {
        'silver_file' : "btdsim_gummel_pmos_btdsim6_ids_vg0_data.csv",
        'golden_file' : "spectre_gummel_pmos_btdsim6_ids_vg0_data.csv",
        'AEthreshold' : 0.3,
        'REthreshold' : 0.05,
    }
    gcc = GeneralComparsionCls()

    os.makedirs("output", exist_ok=True)
