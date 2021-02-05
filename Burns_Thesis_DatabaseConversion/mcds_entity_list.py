#mcds_entity_list.py - look through all DCL's in MCDS folder, generate xlsx file with all tags/xpaths
#   Used to determined semi-complete list of possible DCL unique tags.
#   User should remove duplicate rows from xslx file after generating

# Input:
#   MCDS-DCL xml files in MCDS_2_ISATab\All_Digital_Cell_Lines
#   At time of script creation, MCDS-DCL #001-237 are included (numbering is not continuous)
# Output:
#   1 Excel File containing MCDS tags:   MCDS_DCL_All_Tags.xlsx

# Author: Connor Burns
# Date:
#   v0.1 - Feb 2020

import os
import xlsxwriter
from lxml import etree

os.chdir(r'C:\Users\Connor\PycharmProjects\MCDS_2_ISATab\Burns_Thesis_DatabaseConversion')
cwd = os.getcwd()
#TODO - Only works if cwd is set to directry in line 19 - update later for other users?
DCL_xml_dir = os.path.join(cwd[:-32], 'All_Digital_Cell_Lines')
#DCL_xml_dir = (r'...<enter local path>...\MCDS_2_ISATab\All_Digital_Cell_Lines')

workbook = xlsxwriter.Workbook('MCDS_DCL_All_Tags.xlsx')
worksheet = workbook.add_worksheet()
worksheet.write('A1','MCDS Entities', workbook.add_format({'bold': True}))
worksheet.write('B1','xPath', workbook.add_format({'bold': True}))
worksheet.write('C1','File Name', workbook.add_format({'bold': True}))
#Initialize xlsx file, write column headers to workbook

i = 1;
#Row counter, used in function below

def extract_tags_xPath(XML_FileName):
    xml_test_file = os.path.join(DCL_xml_dir, XML_FileName)
    tree = etree.parse(xml_test_file)
    root = tree.getroot()

    global i
    for child in root.iter():
        worksheet.write(i, 0, str(child.tag))
        #finds all DCL tags in XML input file
        parents = []
        for parent in child.iterancestors():
            parents.insert(0,parent.tag)
        xPath = "/".join(parents)
        #finds all parents of the tag found above, appends to list in hierarchical order, joins with / to create xPath
        worksheet.write(i, 1, str(xPath))
        worksheet.write(i, 2, str(XML_FileName))
        i += 1

DCL_list = os.listdir(DCL_xml_dir)
#Create list of XML files from All Cell Lines folder

for DCL in DCL_list:
    extract_tags_xPath(DCL)

workbook.close()
