# MCDS_DCL2ISA_DB.py - using a MultiCellDS digital cell line XML file, generate associated ISA-Tab files
#
# Input:
#   a MultiCellDS digital cell line file  <DCL-root-filename>.xml
# Output:
#   3 ISA files:
#    i_<DCL-root-filename>.txt
#    s_<DCL-root-filename>.txt
#    a_<DCL-root-filename>.txt

# Author: Connor Burns
# Date:
#   v0.1 - Feb 2020

import os
import sys
import pandas as pd
from lxml import etree

os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))
#change current working directory to script location
cwd = os.getcwd()
db = os.path.join(cwd, 'ISA_MCDS_Relationships_Py.xlsx')
#Define Master database directory path - assumes that database is in same directory as script

DCL_xml_dir = os.path.join(cwd[:-32], 'All_Digital_Cell_Lines')
DCL_list = os.listdir(DCL_xml_dir)
DCL_in = os.path.join(DCL_xml_dir,DCL_list[0])
#Find and define DCL input file path

df = pd.read_excel (rF'{db}', usecols=['ISA-Tab Entity', 'ISA File Location', 'ISA Entity Type','MCDS Correlate Entity', 'MCDS Correlate X-Path'])
#Importing master database as df
parser = etree.XMLParser(remove_comments=True)
tree = etree.parse(DCL_in, parser=parser)
root = tree.getroot()
#Initialize XML parser

def MCDS_match(i):
    if not pd.isnull(df.at[i,'MCDS Correlate X-Path']):
        xpaths = df.at[i,'MCDS Correlate X-Path'].split(",")
        for xpath in xpaths:
            print(root.find(xpath))
        f_I.write('\t xPath Exists \n')
    else:
        f_I.write('\n')
#For index, go to column of relationship spreadsheet
    #pull xPath list, separate by commas into different values
    #Go to each xPath in input xml - if there is value, write to f_I

f_I = open('I_test.txt', 'w')
for ind in df.index:
    if df.at[ind,'ISA File Location'] == 'I':
        if df.at[ind,'ISA Entity Type'] == 'Header':
            f_I.write(df.at[ind,'ISA-Tab Entity'].upper() + '\n')
        else:
            f_I.write(df.at[ind,'ISA-Tab Entity'])
            MCDS_match(ind)
    #If type is I file, then write newline with I file. If header, write in all caps and go to next line. If type data,
# write then /t, parse through xml with correlate xpath. If no data exists, "" then /n. If data exists, write in file. Continue for all x paths.
# After doing for all xpaths in list, /n
  #      f_I.write(str(ISA) + '\n')

#For info in I location, if

#For ISA entities in db
#   If ISA entity has location: I-file
#       If ISA entity is type: Header
#           Write ISA field in all caps /n
#       Else
#           Write ISA entity /t to txt output file
#               If any MCDS entity correlate to ISA entity is in XML list:
#                 find MCDS entity(ies) in XML
#                 write "MCDS value" at end of line
#               Else: Write ""
#           /n

    #If S-file
    #If A - file
    #If I-S file
    #If I-A file

