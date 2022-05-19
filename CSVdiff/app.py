# -*- coding: utf-8 -*-
# @Time    : 2021/8/25 14:18
# @Author  : Wayne
# @File    : app.py.py
# @Software: PyCharm


import sys
from Pydiff import Ui_MainWindow
from PyQt5.QtWidgets import QApplication, QDialog, QMainWindow, QFileDialog, QSizePolicy, QMessageBox
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from tool_utils import get_rmse, get_mape, AlignDataLen, mean_absolute_percentage_error, mape_vectorized_v2

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class PlotCanvas(FigureCanvas):

  def __init__(self, parent=None):
    fig = Figure(figsize=(6, 4), dpi=100)
    FigureCanvas.__init__(self, fig)
    self.setParent(parent)
    FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
    FigureCanvas.updateGeometry(self)

  def plot(self, data, title):
    print(data.head())
    ax = self.figure.add_subplot(1, 1, 1)
    ax.set_title(title)
    ax.plot(data)
    # ax.plot(data.index, data.dstvalue)
    ax.legend(['src', 'dst'])
    self.show()





class DiffCSVFile(QMainWindow, Ui_MainWindow):
  def __init__(self, parent=None):
    super(DiffCSVFile, self).__init__(parent)
    self.setupUi(self)
    self.srcFile = None
    self.dstFile = None
    self.segstring = None
    self.srcdata = None
    self.dstdata = None
    fig = Figure(figsize=(100, 100), dpi=100)
    self.axes = fig.add_subplot(111)
    self.slot_init()
    self.setWindowTitle("CSV文件对比")


  def slot_init(self):
    self.pushButton.clicked.connect(self.selectsrcCSVFile)
    self.pushButton_2.clicked.connect(self.selectdstCSVFile)
    self.pushButton_3.clicked.connect(self.diffCSVFile)

  def readSecondLine(self, readfile):
    f = open(readfile, 'r', encoding='utf-8')
    strtext = ""
    for i in range(2):
      strtext = strtext + "\n" +f.readline()

    return strtext

  def selectsrcCSVFile(self):
    self.srcFile, filetype = QFileDialog.getOpenFileName(self,
                                                      "选取文件",
                                                      "./",
                                                      "CSV Files (*.csv)")  # 设置文件扩展名过滤,注意用双分号间隔
    # self.srcFile = r"E:/WORKSPACE/localpythonproject/matplotProject/btdsim_hao_test35.csv"
    self.label.setText('Done')
    valuedata = self.readSecondLine(self.srcFile)
    self.label_4.setText(valuedata)




  def selectdstCSVFile(self):
    self.dstFile, filetype = QFileDialog.getOpenFileName(self,
                                                      "选取文件",
                                                      "./",
                                                      "CSV Files (*.csv)")  # 设置文件扩展名过滤,注意用双分号间隔
    # self.dstFile = r"E:/WORKSPACE/localpythonproject/matplotProject/hao_test35.csv"
    self.label_2.setText('Done')
    valuedata = self.readSecondLine(self.dstFile)
    self.label_5.setText(valuedata)


  def diffCSVFile(self):
    self.srcdata = pd.read_csv(self.srcFile, skiprows=1, names=['time', 'srcvalue'])

    self.dstdata = pd.read_csv(self.dstFile, skiprows=1, names=['time', 'dstvalue'])
    # print(len(self.srcdata.srcvalue))
    # print(len(self.dstdata.dstvalue))
    # print(type(self.srcdata.srcvalue[0]))
    # if len(self.dstdata.dstvalue) != len(self.srcdata.srcvalue):
    #   QMessageBox.about(self, "警告", "数据长度不一致，请重新选择！")
    #   self.label.setText(' ')
    #   self.label_2.setText(' ')
    #   return

    #处理复数
    if isinstance(self.srcdata.srcvalue[0], str):
      str_data1 = self.srcdata.srcvalue.values.tolist()
      # test = np.absolute(complex(str_data1[0]))
      self.srcdata['srcvalue'] = [np.absolute(complex(i)) for i in str_data1]
    if isinstance(self.dstdata.dstvalue[0], str):
      str_data2 = self.dstdata.dstvalue.values.tolist()
      self.dstdata['dstvalue'] = [np.absolute(complex(j)) for j in str_data2]


    # print(self.srcdata.head())
    # print(self.dstdata.head())


    title = str(pd.read_csv(self.srcFile).columns.values).split('|')[-2]

    self.srcdata['dstvalue'] = self.dstdata["dstvalue"]
    print(self.srcdata)

    refdata = self.srcdata.srcvalue
    outdata = self.srcdata.dstvalue
    # 对齐数据
    if len(self.srcdata.srcvalue) != len(self.srcdata.dstvalue):
      _, outdata, refdata = AlignDataLen(self.srcdata.time, self.srcdata.time, self.srcdata.srcvalue, self.srcdata.dstvalue)

    assert len(refdata) == len(outdata)

    del self.srcdata["time"]

    # 计算mape
    # mape = get_mape(outdata, refdata)
    # mape = mean_absolute_percentage_error(outdata, refdata)
    mape = mape_vectorized_v2(outdata, refdata)
    title = title + "\n" + "mape:" + str(mape)

    # rmse = ((self.srcdata.srcvalue - self.srcdata.dstvalue) ** 2).mean() ** .5
    # title = title + "\n" + "RMSE:" + str(rmse)
    print(title)

    # self.textBrowser.setText("RMSE:" + str(rmse))
    self.textBrowser.setText("mape:" + str(mape))

    m = PlotCanvas(self)
    m.plot(self.srcdata, title)
    m.move(270, 30)
    self.show()


if __name__ == '__main__':
  app = QApplication(sys.argv)
  ex = DiffCSVFile()
  ex.show()
  sys.exit(app.exec_())