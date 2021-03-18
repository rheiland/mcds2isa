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
import linecache

os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))
#change current working directory to script location
cwd = os.getcwd()
db = os.path.join(cwd, 'ISA_MCDS_Relationships_Py_CB.xlsx')
#Define Master database directory path - assumes that database is in same directory as script

DCL_xml_dir = os.path.join(cwd[:-32], 'All_Digital_Cell_Lines')
#TODO - Change once merged into directory
DCL_list = os.listdir(DCL_xml_dir)
DCL_in = os.path.join(DCL_xml_dir, DCL_list[40])
print('Input file: ', DCL_list[40] )
#DSS_in = os.path.join(cwd, 'All_Snapshots_MCDS_S_0000000001.xml')
# txt_in = os.path.join(cwd, 'DCL File List, Indexed.txt')
#TODO - Change to allow for multiple file input or create GUI to select folder/files
#Find and define DCL input file path
parser = etree.XMLParser(remove_comments=True)
tree = etree.parse(DCL_in, parser=parser)
root = tree.getroot()
if root.get('type') != 'cell_line':
    print("\n\033[1;31;40m Error: Input .xml is not a Digital Cell Line")
    sys.exit()
#TODO - Update to work with list of files
#TODO - is a check for xml needed? Is it better to skip over non XML files and non cell_line XML's rather than throw error? Allow user to decide?

#Intialize XML parser, check file type

#Input: List of DCL files
#Output: .txt file with file name and index in DCL list
def dcl_input_indexed_list(DCL_list):
    f_l = open("DCL File List, Indexed.txt", 'w')
    dcl_ind = 0
    for DCL in DCL_list:
        f_l.write('List Index: ' + str(dcl_ind) + '\t\tFilename: ' + str(DCL) + '\t\tFile type: ' + str(root.get('type')) + '\n' )
        dcl_ind +=1
    f_l.close()
# dcl_input_indexed_list(DCL_list)

df = pd.read_excel(rF'{db}', usecols=['ISA-Tab Entity', 'ISA File Location', 'ISA Entity Type',
                                      'MCDS-DCL Correlate Entity', 'MCDS-DCL Correlate X-Path', 'Multiples for xPath'])

#Importing master database as df


#Input:
#   One xPath that is marked in xlsx to be able to contain multiple values
#   The xPath should have the root removed along with extra characters such as attribute value
#Output:
#   One list that contains existing elements at xPath and blanks, in order of appearance in DCL xml input file
def match_mult(x_in):
    x_in = x_in.replace('/' + root.tag + '/','',1).strip()
    x_list = root.findall(x_in)
    #gives list of xPaths with existing elements
    x_elem_out = []
    par_len = len(root.findall(x_in.rsplit('/',1)[0]))
    #if number of existing elements is less than iterations of parent tag, appropriately place elements and blanks in ordered list
    if len(x_list) < par_len:
        val_dict = {}
        for x in x_list:
            val_dict[int(tree.getpath(x).rsplit('[')[-1].rsplit(']')[0]) - 1] = x
            #x is xpath for element that exists
        for j in range(par_len):
            if not j in val_dict:
                val_dict[j] = ""
            x_elem_out.append(val_dict[j])
            #add in "" blanks for elements which do not exist and append to list in order
    else:
        x_elem_out = x_list
    return(x_elem_out)


#Inputs: 2 or more xPath's that are separated by +, signifying they should be concatenated, along with the index
#Output: List of concatenated strings from the 2 or more xPaths that have been appended together
#Operation: initialize variables, split xPaths to be concatenated, store values in array, concatenate by j counter
def entity_concat(path,i):
    concat_out = []
    matched_list = []
    concat_list = []
    concat_paths = path.split('&')
    j = len(concat_paths)
    k = 1
    # j = number of elements to concat, k = number of multiples, default 1 for single
    for concat in concat_paths:
        rootless_concat = concat.replace('/' + root.tag + '/', '', 1).strip()
        # remove root and "/" from beginning of xPath
        if 'Single' in str(df.at[i, 'Multiples for xPath']):
            try:
                concat_list.append(root.find(rootless_concat).text.strip().replace('\n', ' ').replace('\t', ''))
            except:
                concat_list.append('')
                print('Text Does Not Exist')
        elif 'Multiple' in str(df.at[i, 'Multiples for xPath']):
            mult_list = match_mult(rootless_concat)
            for mult_elem in mult_list:
                try:
                    concat_list.append(mult_elem.text.strip().replace('\n', ' ').replace('\t', ''))
                except:
                    concat_list.append('')
                    print('Text Does Not Exist')
            k = len(mult_list)
        else:
            f_E.write('Issue in XLSX at I-Line: ' + str(i + 1) + '\t\t Issue: No multiple/single\n')
   #determine which indices from generated list to concatenate
    for num_mult in range(k):
        ind_list = []
        join_list = []
        for num_concat in range(j):
            ind_list.append(num_mult + num_concat * (k))
        for c_list_ind in ind_list:
            if concat_list[c_list_ind]:
                join_list.append(concat_list[c_list_ind])
        matched_list.append(join_list)
    #Matched_list has nested lists of each item to be joined
    for num_mult in range(k):
        concat_out.append(' - '.join(matched_list[num_mult]))
    return concat_out

def mcds_match(i):
    # For each index value, go to that row of the relationship xlsx file
    # Pull xPath's in list, separate by commas into different values
    # Go to each xPath in input xml - if there is value, write to f_I
    # If there is no value from input xml, put appropriate quotes for blank

    # Initialize string with spacing from entered ISA entity name
    ISA_space = '\t\t'
    str_list = []
    I_str = ISA_space
    I_sep = '\t'
    I_blank = '""'
    print("I file line: ", i + 1)
    # If statement checks to see whether xPath exists in relationship excel sheet.
    # If xPath does not exist, write appropriate number of "" to line in else statement
    if not pd.isnull(df.at[i,'MCDS-DCL Correlate X-Path']):
        #If entry is written in excel sheet (i.e. not contained in input XML, same for all files), write to I_str
        if df.at[i,'MCDS-DCL Correlate X-Path'] == "Text Entry":
            I_str += df.at[i,'MCDS-DCL Correlate Entity']
        else:
            xpaths = df.at[i,'MCDS-DCL Correlate X-Path'].split(",")
            #Pull xPaths from cell in xlsx file, separate multiple values into list to use in for loop
            for path in xpaths:
                if '&' in path:
                    str_list.extend(entity_concat(path,i))
                #'&' in xPath signifies that the xPaths should be concatenated to a single ISA value "text1 - text2..."
                else:
                    rootless = path.replace('/' + root.tag + '/','',1).strip()
                    #remove root and "/" from beginning of xPath for root.find method

                    if '@' in rootless:
                    # '@' in xPath signifies this is an attribute
                    #Lines below: split input xPath into element xPath and attribute name
                    #Write value of attribute to str_list with appropriate "" if no result
                        result = re.split(r"@", rootless)
                        atPath = result[0].replace('[', '')
                        attr = result[1].replace(']', '')
                        if 'Single' in str(df.at[i,'Multiples for xPath']):
                            try:
                                str_list.append(root.find(atPath).get(attr))
                                break
                            except:
                                print('Attr Does Not Exist')
                        elif 'Multiple' in str(df.at[i,'Multiples for xPath']):
                            mult_list = match_mult(atPath)
                            for mult_elem in mult_list:
                                try:
                                   str_list.append(mult_elem.get(attr))
                                except:
                                    str_list.append(I_blank)
                                    print('Attr Does Not Exist')
                        else:
                            f_E.write('Issue in XLSX at I-Line: ' + str(i+1) + '\t\t Issue: No multiple/single\n')

                    elif '*' in rootless:
                        # '*' in xPath signifies this is a tag
                        # Lines below: remove '*' from xPath
                        # Write value of tag to str_list with appropriate "" if no result
                        gen_count = rootless.count('*')
                        result = rootless.replace('*', '')
                        if 'Single' in str(df.at[i,'Multiples for xPath']):
                            try:
                                if gen_count == 1:
                                    str_list.append(root.find(result).getparent().tag.replace('_', ' ').title())
                                if gen_count == 2:
                                    str_list.append(root.find(result).getparent().getparent().tag.replace('_', ' ').title())
                                break
                            except:
                                print('Tag Does Not Exist')
                        elif 'Multiple' in str(df.at[i,'Multiples for xPath']):
                            mult_list = match_mult(result)
                            for mult_elem in mult_list:
                                try:
                                    if gen_count == 1:
                                        str_list.append(mult_elem.getparent().tag.replace('_', ' ').title())
                                    if gen_count == 2:
                                        str_list.append(mult_elem.getparent().getparent().tag.replace('_', ' ').title())
                                except:
                                    str_list.append(I_blank)
                                    print('Tag Does Not Exist')
                        else:
                            f_E.write('Issue in XLSX at I-Line: ' + str(i+1) + '\t\t Issue: No multiple/single\n')

                    else:
                        # Default state is finding the text from the element at the specified xPath
                        # Lines below: split input xPath into element xPath and attribute name
                        # Write value of attribute to str_list with appropriate "" if no result

                        if 'Single' in str(df.at[i,'Multiples for xPath']):
                            try:
                                str_list.append(root.find(rootless).text.strip().replace('\n', ' ').replace('\t', ''))
                                break
                            except:
                                print('Text Does Not Exist')
                        elif 'Multiple' in str(df.at[i,'Multiples for xPath']):
                            mult_list = match_mult(rootless)
                            for mult_elem in mult_list:
                                try:
                                    str_list.append(mult_elem.text.strip().replace('\n', ' ').replace('\t', ''))
                                except:
                                    str_list.append(I_blank)
                                    print('Text Does Not Exist')
                        else:
                            f_E.write('Issue in XLSX at I-Line: ' + str(i+1) + '\t\t Issue: No multiple/single\n')

                        #TODO - would there be instances of the same info being contained at different xPaths, but should only be written to the ISA output once?
            if df.at[i,'Multiples for xPath'] == 'Single' and len(str_list) == 0:
                I_str += I_sep + '""'
            else:
                for match in str_list:
                    if match != '""':
                        I_str += I_sep + '"' + match + '"'
                    else:
                        I_str += I_sep + match

    else:
        if 'Multiple' in str(df.at[i, 'Multiples for xPath']):
            dep_index = int(df.at[i, 'Multiples for xPath'].replace('Multiple - ', ''))
            dep_line = linecache.getline(filename, dep_index)
            ent_count = int(dep_line.count('"') / 2)
            for k in range(ent_count):
                I_str += I_sep + I_blank
            I_str += ' - NO XPATH'
            #add a "" for each entity from dependent line in I file
        else:
        #default value is one ""
            I_str += I_sep + '""' + ' - NO XPATH'
        if pd.isnull(df.at[i,'Multiples for xPath']):
            f_E.write('\t\t\t (No xPath) Issue in XLSX at I-Line: ' + str(i + 1) + '\t\t Issue: No multiple/single\n')

    f_I.write(I_str + '\n')

error_file = "ErrorLog_DCL2ISA.txt"
f_E = open(error_file, 'w')
filename = 'I_test.txt'
#f_I = open(filename, 'w')
#f_I.close()
# if os.path.exists(filename) == False:
#     f_I = open(filename, 'w')
#     f_I.close()
f_I = open(filename, 'r+')
#f_I.truncate(0)
#TODO - why does this affect the number of "" for multiples?
#Create file if it does not exist, then open in read + write mode (will overwrite). Issue: does not clear file

for ind in df.index[:104]:
    if df.at[ind,'ISA File Location'] == 'I' or 'I-S':
        if df.at[ind,'ISA Entity Type'] == 'Header':
            f_I.write(df.at[ind,'ISA-Tab Entity'].upper() + '\n')
        else:
            f_I.write(df.at[ind,'ISA-Tab Entity'])
            mcds_match(ind)
    #If type is I file, then write newline with I file. If header, write in all caps and go to next line. If type data,
    # write then /t, parse through xml with correlate xpath. If no data exists, "" then /n. If data exists, write in file. Continue for all x paths.
    # After doing for all xpaths in list, /n



#Assay file:

phenotype_dataset = match_mult('cell_line/phenotype_dataset')
pheno_paths = []
cell_part_paths = []
subcell_part_paths = []
for pheno_ind in range(len(phenotype_dataset)):
    pheno_paths.append(tree.getelementpath(phenotype_dataset[pheno_ind]))

    #print(phenotype_dataset[pheno_ind].getelementpath())
    # cell_part_list = match_mult(getpath(phenotype_dataset[pheno_ind]))
    # for
    # subcell_part_list

    #If A - file
    # If S-file
    #If I-S file
    #If I-A file
    #If there are files missing, throw error?