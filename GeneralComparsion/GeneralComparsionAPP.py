# -*- coding: utf-8 -*-
# @Time : 2022/4/12 15:12 
# @Author : wayne
# @File : GeneralComparsionAPP.py 
# @Software: PyCharm

import argparse
import os
import pandas as pd
import numpy as np
import plotly.graph_objs as go
import dash
import dash_core_components as dcc                  # 交互式组件
import dash_html_components as html                 # 代码转html
from dash.dependencies import Input, Output         # 回调
from jupyter_plotly_dash import JupyterDash         # Jupyter中的Dash
from dash import Dash

class GeneralComparsionCls():
    # 定义、创建对象初始化
    def __init__(self, data=None):
        if data:
            self.silver_points = data['silver_points']
            self.golden_points = data['golden_points']
            self.AEthreshold = data['AEthreshold']
            self.REthreshold = data['REthreshold']
        else:
            self.silver_points = None
            self.golden_points = None
            self.AEthreshold = 0
            self.REthreshold = 0

        self.com_result = False
        self.reports_AE = {}
        self.reports_RE = {}
        self.sort_report_outliers = None
        self.app = None

    def set_silver_points(self, silver_points):
        self.silver_points = silver_points

    def set_golden_points(self, golden_points):
        self.golden_points = golden_points


    def set_AEthreshold(self, AEthreshold):
        self.AEthreshold = AEthreshold

    def set_REthreshold(self, REthreshold):
        self.REthreshold = REthreshold

    def get_comp_resut(self):
        if (np.array(self.ae_points) <= self.AEthreshold).all() and (np.array(self.re_points) <= self.REthreshold).all():
            self.com_result = True
        else:
            self.com_result = False
        return self.com_result

    def get_reports_AE(self):
        self.reports_AE['max_AE'] = np.max(self.ae_points)
        self.reports_AE['min_AE'] = np.min(self.ae_points)
        self.reports_AE['ave_AE'] = np.average(self.ae_points)
        self.reports_AE['stdv_AE'] = np.std(self.ae_points)
        return self.reports_AE

    def get_reports_RE(self):
        self.reports_RE['max_RE'] = np.max(self.re_points)
        self.reports_RE['min_RE'] = np.min(self.re_points)
        self.reports_RE['ave_RE'] = np.average(self.re_points)
        self.reports_RE['stdv_RE'] = np.std(self.re_points)
        return self.reports_RE

    def get_sort_report_outliers(self):
        return self.sort_report_outliers

    def run_comparsion(self):

        self.ae_points = np.abs(np.array(self.silver_points) - np.array(self.golden_points))
        self.re_points = np.abs(self.ae_points) / (np.array(self.golden_points))

        self.AEthreshold = 1
        self.REthreshold = 0.9
        x = self.golden_points
        AE_line1 = [i + self.AEthreshold for i in x]
        AE_line2 = [i - self.AEthreshold for i in x]
        RE_line1 = [i * (1 - self.REthreshold) for i in x]
        RE_line2 = [i * (1 + self.REthreshold) for i in x]

        self.app = Dash('BTD Dash', )
        self.app.layout = html.Div(
            children=[
                html.H1('BTD，Dash'),
                html.Div('''Dash: General Comparison Utility'''),
                dcc.Graph(
                    id='example-graph',
                    figure=dict(
                        data=[{'x': x, 'y': x, 'type': 'lines', 'name': 'y=x'},
                              {'x': x, 'y': AE_line1, 'type': 'lines', 'name': '+AE'},
                              {'x': x, 'y': AE_line2, 'type': 'lines', 'name': '-AE'},
                              {'x': x, 'y': RE_line1, 'type': 'lines', 'name': '-RE'},
                              {'x': x, 'y': RE_line2, 'type': 'lines', 'name': '+RE'},
                              go.Scatter(
                                  x=self.silver_points,
                                  y=self.golden_points,
                                  mode='markers',
                                  name='data',

                              )
                              ],
                        layout=dict(title='Dash数据可视化')
                    )
                )
            ]
        )



if __name__ == '__main__':

    #数据预处理
    btd_data = pd.read_csv("btdsim_gummel_pmos_btdsim6_ids_vg0_data.csv", skiprows=1, names=['vd', 'ids'])

    spec_data = pd.read_csv("spectre_gummel_pmos_btdsim6_ids_vg0_data.csv", skiprows=1, names=['vd', 'ids'])

    # def General Comparison Utility
    silver_points = [d * 1e7 for d in btd_data['ids'].values.tolist()]
    golden_points = [d * 1e7 for d in spec_data['ids'].values.tolist()]

    #传入类的参数
    inputs = {
        'silver_points': silver_points,
        'golden_points': golden_points,
        'AEthreshold': 0.3,
        'REthreshold': 0.05,
    }

    #类初始化
    gcc = GeneralComparsionCls(data=inputs)
    #调用成员函数
    gcc.run_comparsion()

    #返回比较结果
    print("comp_resut:", gcc.get_comp_resut())
    print("reports_AE:", gcc.get_reports_AE())
    print("reports_RE:", gcc.get_reports_RE())
    gcc.app.run_server(port=7777)


    #TODO  图像优化 ， 保存为HTML文件
