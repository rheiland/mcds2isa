# This script is used to analyze a list of MCDS-DCL files for the following issues:
#   1) Having the correct file type attribute under the MultiCellDS xml tag
#   2) ID attributes for certain xPath's (such as /phenotype_dataset and /cell_cycle) not matching the
#      order that the xPath tags appear within the xml file
# Additionally, the dcl_input_indexed_list provides an output text file containing the list index, file name, and
# MCDS file type for each file within the file input list

# Author: Connor Burns
# Date:
#   v0.1 - Mar 2020

import os
import sys
from lxml import etree

os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))
#change current working directory to script location
cwd = os.getcwd()
DCL_xml_dir = os.path.join(cwd[:-32], 'All_Digital_Cell_Lines')
DCL_list = os.listdir(DCL_xml_dir)
All_DCL_list = []
for DCL in DCL_list:
    All_DCL_list.append(os.path.join(DCL_xml_dir, DCL))

def dcl_input_indexed_list(DCL_list):
    '''
    :param DCL_list: List of DCL files
    :return: "DCL File List, Indexed.txt" file with DCL input file name, its index in DCL list, and MCDS file type
    '''
    f_l = open("DCL File List, Indexed.txt", 'w')
    dcl_ind = 0
    k = 0
    for DCL in DCL_list:
        parser = etree.XMLParser(remove_comments=True)
        tree = etree.parse(DCL, parser=parser)
        root = tree.getroot()
        f_l.write('List Index: ' + str(dcl_ind) + '\t\tFilename: ' + os.path.split(DCL)[1] + '\t\tFile type: ' + str(root.get('type')) + '\n')
        if str(root.get('type')) != "cell_line":
            k+= 1
            print('\nFilename: ' + os.path.split(DCL)[1] + ' \tis type: ' + str(root.get('type')))
        dcl_ind +=1
    f_l.close()
    if k == 0:
        print('\nAll input xml files are type: cell_line')
dcl_input_indexed_list(All_DCL_list)


def ID_order_check(DCL_list, ID_xPaths):
    '''
    :param DCL_list: List of DCL files to search through
    :param ID_xPaths: list of xPaths to search ID ordering for. The root should not be included and the [@ID] attribute
        should be included.
    :return: 'ID ordering check.txt' file, contains file name and xPath of issue
    '''
    f_p = open('ID ordering check.txt', 'w')
    for DCL in DCL_list:
        parser = etree.XMLParser(remove_comments=True)
        tree = etree.parse(DCL, parser=parser)
        root = tree.getroot()
        for xPath in ID_xPaths:
            ID_elements = root.findall(xPath)
            ID_list = []
            k = 0
            for ID in ID_elements:
                ID_list.append(ID.attrib['ID'])
                if k > 0:
                    if int(ID_list[k]) != (int(ID_list[k-1]) + 1) and int(ID_list[k]) != 0:
                        f_p.write('Incorrect order - File: ' + os.path.split(DCL)[1] + '\txPath: \t' + str(xPath) + '\n')
                k+= 1
    f_p.close()
    if os.path.getsize('ID ordering check.txt') == 0:
       print('\nNo ID ordering issues detected')
    else:
        print('\nID ordering issues detected: see ID ordering check.txt')

ID_check_list = ['cell_line/phenotype_dataset[@ID]',
                 'cell_line/phenotype_dataset/phenotype/cell_cycle[@ID]',
                 'cell_line/phenotype_dataset/phenotype/cell_cycle/cell_cycle_phase[@ID]',
                 'cell_line/phenotype_dataset/phenotype/cell_death[@ID]',
                 'cell_line/metadata/custom/clinical/diagnosis/pathology/pathology_definitions/stain[@ID]',
                 'cell_line/metadata/custom/clinical/diagnosis/pathology/stain[@ID]',
                 'cell_line/phenotype_dataset/phenotype/motility/unrestricted[@ID]']

ID_order_check(All_DCL_list, ID_check_list)



