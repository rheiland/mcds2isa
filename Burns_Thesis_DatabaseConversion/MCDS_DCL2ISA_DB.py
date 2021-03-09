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
import re
import pandas as pd
from lxml import etree

os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))
#change current working directory to script location
cwd = os.getcwd()
db = os.path.join(cwd, 'ISA_MCDS_Relationships_Py.xlsx')
#Define Master database directory path - assumes that database is in same directory as script

DCL_xml_dir = os.path.join(cwd[:-32], 'All_Digital_Cell_Lines')
#TODO - Change once merged into directory
DCL_list = os.listdir(DCL_xml_dir)
DCL_in = os.path.join(DCL_xml_dir, DCL_list[0])
#TODO - Change to allow for multiple file input or create GUI to select folder/files
#Find and define DCL input file path

df = pd.read_excel(rF'{db}', usecols=['ISA-Tab Entity', 'ISA File Location', 'ISA Entity Type',
                                      'MCDS-DCL Correlate Entity', 'MCDS-DCL Correlate X-Path'])
#Importing master database as df
parser = etree.XMLParser(remove_comments=True)
tree = etree.parse(DCL_in, parser=parser)
root = tree.getroot()
#Intialize XML parser

def mcds_match(i):
    # For index, go to column of relationship spreadsheet
    # pull xPath list, separate by commas into different values
    # Go to each xPath in input xml - if there is value, write to f_I
    if not pd.isnull(df.at[i,'MCDS-DCL Correlate X-Path']):
    # 1st if: checks to see whether xPath exists in relationship excel sheet. If no xPath, write new line to file
        xpaths = df.at[i,'MCDS-DCL Correlate X-Path'].split(",")
    #get list of xpaths from excel spreadsheet
        for path in xpaths:
            print(i+2)
            rootless = path.replace(root.tag + '/','',1)
            #remove root and "/" from beginning of xPath
            if '@' in rootless:
                result = re.split(r"@", rootless)
                atPath = result[0].replace('[', '')
                attr = result[1].replace(']', '')
                try:
                    f_I.write('\t\t\t"' + tree.find(atPath).get(attr) + '"')
                except:
                    print('Attr Does Not Exist')
                #separate xPath of child and attribute, then write value of attribute to file
            else:
                try:
                    f_I.write('\t\t\t"' + root.find(rootless).text.strip().replace('\n', '') + '"')
                except:
                    print('Text Does Not Exist')
                #TODO - would there be instances where the same information is contained twice at different xPaths, but should only be written to the ISA output once?
        f_I.write('\n')

    #2nd if: checks to see whether text or attribute?
    #3rd if: checks existence of text/attribute
    #Need to check to see if data matches existing write (duplicated data)
    else:
        f_I.write('\n')


f_I = open('I_test.txt', 'w')
for ind in df.index[:]:
    if df.at[ind,'ISA File Location'] == 'I':
        if df.at[ind,'ISA Entity Type'] == 'Header':
            f_I.write(df.at[ind,'ISA-Tab Entity'].upper() + '\n')
        else:
            f_I.write(df.at[ind,'ISA-Tab Entity'])
            mcds_match(ind)
    #If type is I file, then write newline with I file. If header, write in all caps and go to next line. If type data,
    # write then /t, parse through xml with correlate xpath. If no data exists, "" then /n. If data exists, write in file. Continue for all x paths.
    # After doing for all xpaths in list, /n

    #If S-file
    #If A - file
    #If I-S file
    #If I-A file
    #If there are files missing, throw error