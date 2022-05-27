#!/usr/bin/python
# -*- coding: UTF-8 -*-
import os 
import sys 
import math

def as_num(x):
	y='{:.18f}'.format(float(x))
	return(y)

def is_equal(a,b,pos):
	if float(a)<1e-18 and float(b)<1e-18:
		return True,0
	
	if float(a)<1e-18:
		return False,1
		
	return abs(float(a) - float(b))/float(a) <= math.pow(10,-pos),abs(float(a) - float(b))/float(a) 

def readOut(line_data,extname):
	fi = open("result"+extname, "w")
	ids_list = []  
	for i in range(0,len(line_data)):              
		line = line_data[i].strip().replace('\n', '').replace('\r', '')
	  
		if line!="Values:":
			continue
		line = line_data[i+1].strip().replace('\n', '').replace('\r', '')
		if line.find("btd_begin_sweep")!=-1:
			continue
		i+=2
		for j in range(0,101):
			line =line_data[i+j*2].strip().replace('\n', '').replace('\r', '')
			ids_list.append(as_num(line))
			fi.writelines(str(as_num(line))+"\n")
	 				
		i+=101*2
	fi.close()
	return ids_list
	
def readRaw(line_data,extname):
	fi = open("result"+extname, "w")
	ids_list = []  
	for i in range(0,len(line_data)):              
		line = line_data[i].strip().replace('\n', '').replace('\r', '')
	  
		if line!="Values:":
			continue
		line = line_data[i+1].strip().replace('\n', '').replace('\r', '').split("\t")

		if len(line)!=4:
			continue
		for j in range(0,101):
			line = line_data[i+1+j].strip().replace('\n', '').replace('\r', '').split("\t")
			data=0
			if line[3]!="-0":
				data=line[3]

			ids_list.append(as_num(data))
			fi.write(str(as_num(data))+"\n")
	 				
		i+=101
	fi.close()
	return ids_list		
	
if len(sys.argv)<3:
	print("usage:test-tool.py filepath1 filepath2")
	sys.exit()

pos=3
if len(sys.argv)>3:
	pos=int(sys.argv[3])
	
path1=sys.argv[1]
path2=sys.argv[2]
extname1=os.path.splitext(path1)[-1]
extname2=os.path.splitext(path2)[-1]
print("filepath1:{0},filepath2:{1}".format(path1,path2))

if extname1!=".out" and extname1!=".raw":
	print("file type must be .out or .raw")
	sys.exit()

if extname2!=".out" and extname2!=".raw":
	print("file type must be .out or .raw")
	sys.exit()
		
fo = open(path1, "r")
line_data1=fo.readlines()
fo.close()
fo = open(path2, "r")
line_data2=fo.readlines()
fo.close()

if extname1==".out":
	ids1=readOut(line_data1,extname1)
else:
	ids1=readRaw(line_data1,extname1)
	
	
if extname2==".raw":
	ids2=readRaw(line_data2,extname2)
else:
	ids2=readOut(line_data2,extname2)

print("filepath1 ids array len is: {0},filepath2 ids array len is: {1}".format(len(ids1),len(ids2))) 	 	
if len(ids1)!=len(ids2):
	print("not equal")
else:
	num=0
	for i in range(0,len(ids1)):
		bEqual,percent=is_equal(ids1[i],ids2[i],pos)
		if bEqual:
			continue
		num+=1	
		print("not equal on index:{0},{1},{2},{3}".format(i,ids1[i],ids2[i],percent))
print("there are {0} diff".format(num))

