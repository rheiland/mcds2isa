
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
db = os.path.join(cwd, 'ISA_MCDS_Relationships_Py_CB.xlsx')
#Define Master database directory path - assumes that database is in same directory as script

DCL_xml_dir = os.path.join(cwd[:-32], 'All_Digital_Cell_Lines')
#TODO - Change once merged into directory
DCL_list = os.listdir(DCL_xml_dir)
DCL_file = DCL_list[63]
DCL_in = os.path.join(DCL_xml_dir, DCL_file)
print('Input file: ', DCL_file)
file_base = 'test.txt'
#TODO update file base name
#DSS_in = os.path.join(cwd, 'All_Snapshots_MCDS_S_0000000001.xml')
# txt_in = os.path.join(cwd, 'DCL File List, Indexed.txt')
#TODO - Change to allow for multiple file input or create GUI to select folder/files
#Find and define DCL input file path
parser = etree.XMLParser(remove_comments=True)
tree = etree.parse(DCL_in, parser=parser)
root = tree.getroot()
#TODO - comment explanation, raise error (value errors or things of that nature)
if root.get('type') != 'cell_line':
    sys.exit("\n\033[1;31;40m Error: Input .xml is not a Digital Cell Line")
#TODO - Update to work with list of files
#TODO - is a check for xml needed? Is it better to skip over non XML files and non cell_line XML's rather than throw error? Allow user to decide?
#Intialize XML parser, check file type

df = pd.read_excel(rF'{db}', sheet_name='MCDS-DCL to ISA-Tab', usecols=['ISA-Tab Entity', 'ISA File Location', 'ISA Entity Type',
                                      'MCDS-DCL Correlate Entity', 'MCDS-DCL Correlate X-Path', 'Multiples for xPath'])


def match_mult(x_in):
    '''

    :param x_in: One xPath that is marked in the relationship xlsx to be able to contain multiple values
    :return: One list containing existing elements at xPath and blanks in order of appearance in DCL xml input file
    '''
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

def entity_concat(path,i):
    '''
    :param path: 2 or more xPaths with a separation variable in " ", signifying concatenation with the separation variable
    :param i: index of xPaths
    :return: list of concatenated strings generated from the 2 or more xPaths
    Operation: initialize variables, split xPaths to be concatenated, store values in array, concatenate by j counter
    '''
    concat_out = []
    matched_list = []
    concat_list = []
    concat_paths = path.split('"')[::2]
    sep_vars = path.split('"')[1::2]
    #TODO give error if len (concat_paths) is not = len(sep_vars)?
    j = len(concat_paths)
    k = 1
    # j = number of elements to concat, k = number of multiples, default 1 for single
    for concat in concat_paths:
        concat = concat.strip()
        if 'Single' in str(df.at[i, 'Multiples for xPath']):
            try:
                concat_list.append(root.find(concat).text.strip().replace('\n', ' ').replace('\t', ''))
            except:
                concat_list.append('')
                #print('Text Does Not Exist')
        elif 'Multiple' in str(df.at[i, 'Multiples for xPath']):
            mult_list = match_mult(concat)
            for mult_elem in mult_list:
                try:
                    concat_list.append(mult_elem.text.strip().replace('\n', ' ').replace('\t', ''))
                except:
                    concat_list.append('')
                    #print('Text Does Not Exist')
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
        concat_out.append(sep_vars[0].join(matched_list[num_mult]))
    return concat_out

def mcds_match(i):
    # For each index value, go to that row of the relationship xlsx file
    # Pull xPath's in list, separate by commas into different values
    # Go to each xPath in input xml - if there is value, write to f_I
    # If there is no value from input xml, put appropriate quotes for blank

    # Initialize string with spacing from entered ISA entity name
    str_list = []
    I_str = ''
    I_sep = '\t'
    I_blank = '""'
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
                path = path.strip()
                if '"' in path:
                    str_list.extend(entity_concat(path,i))
                #'&' in xPath signifies that the xPaths should be concatenated to a single ISA value "text1 - text2..."
                else:
                    if '@' in path:
                    # '@' in xPath signifies this is an attribute
                    #Lines below: split input xPath into element xPath and attribute name
                    #Write value of attribute to str_list with appropriate "" if no result
                        result = re.split(r"@", path)
                        attr = result[1].replace(']', '')
                        if 'Single' in str(df.at[i,'Multiples for xPath']):
                            try:
                                str_list.append(root.find(path).attrib[attr])
                                break
                            except:
                                print('Attr Does Not Exist')
                        elif 'Multiple' in str(df.at[i,'Multiples for xPath']):
                            mult_list = match_mult(path)
                            for mult_elem in mult_list:
                                try:
                                   str_list.append(mult_elem.attrib[attr])
                                except:
                                    str_list.append(I_blank)
                                    print('Attr Does Not Exist')
                        else:
                            f_E.write('Issue in XLSX at I-Line: ' + str(i+1) + '\t\t Issue: No multiple/single\n')

                    elif '*' in path:
                        # '*' in xPath signifies this is a tag
                        # Lines below: remove '*' from xPath
                        # Write value of tag to str_list with appropriate "" if no result
                        gen_count = path.count('*')
                        result = path.replace('*', '')
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
                                str_list.append(root.find(path).text.strip().replace('\n', ' ').replace('\t', ''))
                                break
                            except:
                                print('Text Does Not Exist')
                        elif 'Multiple' in str(df.at[i,'Multiples for xPath']):
                            mult_list = match_mult(path)
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
        I_str += I_sep + '""'
        if pd.isnull(df.at[i,'Multiples for xPath']):
            f_E.write('\t\t\t (No xPath) Issue in XLSX at I-Line: ' + str(i + 1) + '\t\t Issue: No multiple/single\n')

    f_I.write(I_str + '\n')

error_file = "ErrorLog_DCL2ISA.txt"
f_E = open(error_file, 'w')


I_filename = 'i_' + file_base
f_I = open(I_filename, 'w')
for ind in df.index[:102]:
    if df.at[ind,'ISA File Location'] == 'I' or 'I-S':
        #print("I file line: ", ind + 1)
        if df.at[ind,'ISA Entity Type'] == 'Header':
            f_I.write(df.at[ind,'ISA-Tab Entity'].upper() + '\n')
        else:
            f_I.write(df.at[ind,'ISA-Tab Entity'] + '\t\t')
            mcds_match(ind)
    #If type is I file, then write newline with I file. If header, write in all caps and go to next line. If type data,
    # write then /t, parse through xml with correlate xpath. If no data exists, "" then /n. If data exists, write in file. Continue for all x paths.
    # After doing for all xpaths in list, /n
f_I.close()
def fix_multi_blanks(I_filename):
    '''
    :param I_filename: Input file to modify
    :return: Modified input file with correct number of quotes for ISA entities with no associated xPath,
            based on number of entities on a separate line in the file
    '''
    f_I = open(I_filename, 'r')
    file_data = f_I.readlines()
    multi_dict = {}
    multi_quantity = {}
    for i in range(len(df['Multiples for xPath'])):
        if 'Multiple' in str(df.at[i,'Multiples for xPath']):
            dep_str = df.at[i, 'Multiples for xPath'].replace('Multiple', '').replace('-', '').strip()
            if dep_str:
                if dep_str in multi_dict:
                    multi_dict[dep_str].append(str(df.at[i,'ISA-Tab Entity']))
                else:
                    multi_dict[dep_str] = str(df.at[i, 'ISA-Tab Entity'])
                    multi_dict[dep_str] = [multi_dict[dep_str]]

    for key in multi_dict.keys():
        f_I.seek(0)
        for line in f_I:
            if key in line:
                multi_quantity[key] = int(line.count('"') / 2)
        if multi_quantity[key] > 1:
            for edit_line in multi_dict[key]:
                f_I.seek(0)
                for (line_num, line) in enumerate(f_I):
                    if edit_line in line:
                        quote_str = ''
                        for i in range(multi_quantity[key]):
                            quote_str += '\t""'
                        file_data[line_num] = edit_line + '\t\t' + quote_str + '\n'
    f_I = open(I_filename, 'w')
    f_I.writelines(file_data)
    f_I.close()

fix_multi_blanks(I_filename)


f_I = open(I_filename, 'r')
file_data = f_I.readlines()
f_I.seek(0)
contact_info_list = []
line_nums = []
dup_ind_list = []
for (line_num,line) in enumerate(f_I):
    if 'Study Person' in line:
        contact_info_list.append(line.replace('\n', '').split('\t'))
        line_nums.append(line_num)
for b in range(len(contact_info_list)):
    contact_info_list[b] = list(filter(None, contact_info_list[b]))
df_s = pd.DataFrame.transpose(pd.DataFrame(contact_info_list))
df_s.columns=['A','B','C','D','E', 'F', 'G', 'H', 'I', 'J', 'K']
#Last name and email columns
for (index,dup) in enumerate(df_s.duplicated(subset = ['A','B'])):
    if dup:
        dup_ind_list.append(index)
#Get list of rows with duplicates

#Get string from dup, find row which it is a duplicate of, go to
for j in dup_ind_list:
    last = df_s.at[j,'A']
    first = df_s.at[j,'B']
    first_ind = df_s[(df_s.A == last) & (df_s.B == first)].index[0]
    role = str(df_s.at[first_ind,'I']).strip('"')
    new_role = str(df_s.at[j,'I']).strip('"')
    df_s.at[first_ind,'I'] = '"' + role + ';' + new_role + '"'

df_s = df_s.drop(dup_ind_list).transpose()
col_list = df_s.values.tolist()
updated_contact_list = []
for (j,items) in enumerate(col_list):
    temp_str = []
    for k in range(len(items)):
         if k == 0:
             temp_str.append((items[k].title() + '\t\t'))
         elif k == len(items) - 1:
             temp_str.append(items[k] + '\n')
         else:
             temp_str.append(items[k])
    updated_contact_list.append('\t'.join(temp_str))

for z in range(len(updated_contact_list)):
    file_data[line_nums[z]] = updated_contact_list[z]
f_I = open(I_filename, 'w')
f_I.writelines(file_data)
f_I.close()

print('\n Assays \n')

#Assay files:
sample_name_base = root.find('cell_line/metadata/MultiCellDB/ID').text +'.' + root.find('cell_line[@ID]').attrib['ID']
a_file_list = []

def a_microenvironment(micro_elems):
    '''
    :param micro_elems: List of all microenvironment elements found with root.findall(.//microenvironment)
    :return: microenvironment assay filename, to be appended to assay file list
        Operation:
            1) Using A_microenvironment sheet in relationship xlsx, load xPaths for searching variables
            2) For each existing microenvironment element, find phenotype_dataset @ID and @keywords for writing
            3) For each existing microenvironment element, create a dictionary with all discrete variable names as keys
                and the xPaths at which the variable names occur as values
            4) Using the xPaths loaded for searching variables, create a nested dictionary. There will be a dictionary
                for each discrete variable name. At the xPaths of the discrete variable names, each variable element
                in the Microenvironment Variable xPaths column from the loaded xlsx will be searched for. Each dictionary
                will contain the discrete variable elements found from this search as keys and the xPaths at which they
                were found as keys
            5) Write variable content to data_out dictionary with dictionary xPaths for existing elements
                Content is written in the following order: "Variable name" + measurements, then all other variable
                elements and values for that variable name. Repeat for each discrete variable name.
            6) Search for condition content based on relationship xlsx. This is done separately from the variable content
                because it does not appear under the /variables/variable xPath. If the condition content exists,
                generate dictionary for values and xPaths then write content to data_out dictionary. ISA Headers are
                dictated by the xlsx relationship file
            7) Write data_out dictionary to pandas dataframe, then write pandas dataframe to output text file
    '''
    df_micro_in = pd.read_excel(rF'{db}', sheet_name='A_Microenvironment',keep_default_na=False,
        usecols=['Microenvironment Variable xPaths', 'Microenvironment Condition xPaths', 'ISA Condition Entities'])
    micro_var_names = {}
    micro_var = {}
    pheno_keywords = []
    #Initialize dictionary for writing to pandas dataframe, with ISA headers as keys and list of content to write down
    #the column as values
    data_out = {'Sample Name': []}
    micro_var_pathend = [str(i) for i in df_micro_in['Microenvironment Variable xPaths'].tolist() if i]
    #import variable xPaths as a list of strings from excel relationship file, remove NaN values
    for micro in micro_elems:
        pheno_keywords.append('"' + micro.getparent().attrib['keywords'].strip().strip(',') + '"')
        try:
            data_out['Sample Name'].append('"' + sample_name_base + '.' + micro.getparent().attrib['ID'] + '"')
        except:
            data_out['Sample Name'].append('"' + sample_name_base + '0' + '"')
        variable_elems = root.findall(tree.getelementpath(micro) + '/domain/variables/variable[@name]')
        #make dictionary of distinct variable names as keys and the xpaths at which the names occur as values
        #TODO - check for matching type and change name of variable to name + type?
        for elem in variable_elems:
            if elem.attrib['name'] in micro_var_names:
                micro_var_names[elem.attrib['name']].append(tree.getelementpath(elem))
            else:
                micro_var_names[elem.attrib['name']] = tree.getelementpath(elem)
                micro_var_names[elem.attrib['name']] = [micro_var_names[elem.attrib['name']]]

    #Make dictionary of dictionaries: one dictionary per variable name in micro_var_names. Each nested dictionary contains
    #the other variable elements (ex. units, ChEBI_ID, etc) that occur for each variable name and the associated xPaths
    #for these variable elements
    for var_name in micro_var_names:
        for var_name_paths in micro_var_names[var_name]:
            for path_ends in micro_var_pathend:
                if '@' in path_ends:
                    result = re.split(r"@", path_ends)
                    attr = result[1].replace(']', '')
                    try:
                        root.find(var_name_paths + path_ends).attrib[attr]
                        if var_name in micro_var:
                            if attr in micro_var[var_name]:
                                micro_var[var_name][attr].append(var_name_paths + path_ends)
                            else:
                                micro_var[var_name][attr] = var_name_paths + path_ends
                                micro_var[var_name][attr] = [micro_var[var_name][attr]]
                        else:
                            micro_var[var_name] = {attr: [var_name_paths + path_ends]}
                    except:
                        None

    #Write content to data out dictionary in order of "Variable name" then other found variable elements
    #Find content based on the xPaths for variable names and variable elements in the created dictionaries
    for var_name,all_var in micro_var.items():
        #Create data_out dictionary key for variable name, then write variable /material_amount.text to values
        data_out['Parameter Value[' + var_name + ']'] = []
        if len(data_out['Sample Name']) > 1:
            #Loop through each phenotype_dataset
            for j in range(len(data_out['Sample Name'])):
                data_str = '"'
                #If element value exists for the phenotype_dataset number, write value to data_out dictionary
                #otherwise, write "" for a blank
                for name_path in micro_var_names[var_name]:
                    result = re.search("phenotype_dataset\[(\d+)\]", name_path)
                    if int(result.group(1)) == j+1:
                        data_str += root.find(name_path + '/material_amount').text.replace('\n','').replace('\t','').strip()
                        break
                data_out['Parameter Value[' + var_name + ']'].append(data_str + '"')
        else:
            #If there is only one phenotype dataset, there will be no numbering in the xPath
            #Name path is joined because the xPath within the dictionary is not accesible by index
            name_path = ''.join(micro_var_names[var_name])
            data_out['Parameter Value[' + var_name + ']'].append('"'+ root.find(name_path + '/material_amount')
                    .text.replace('\n','').replace('\t','').strip() + '"')
        #After adding variable name and its measurement values to data_out dictionary, repeat process with other
        #variable elements
        for var in all_var:
            if "units" in var:
                var_key = var_name + ' measurement ' + var
            elif "ID" in var:
                var_key = 'Characteristic[' + var_name +' ' + var.replace('_',' ') + ']'
            else:
                var_key = 'Parameter Value[' + var_name +' ' + var.replace('_',' ') + ']'
            data_out[var_key] = []
            if len(data_out['Sample Name']) > 1:
                for j in range(len(data_out['Sample Name'])):
                    data_str = '"'
                    for var_path in all_var[var]:
                        result = re.search("phenotype_dataset\[(\d+)\]", var_path)
                        if int(result.group(1)) == j + 1:
                            data_str += root.find(var_path).attrib[var].replace('\n', '').replace('\t','').strip()
                            break
                    data_out[var_key].append(data_str + '"')
            else:
                var_path = ''.join(all_var[var])
                data_out[var_key].append('"' + root.find(var_path).attrib[var]
                            .replace('\n', '').replace('\t', '').strip() + '"')

    #load lists of condition xPaths and their associated ISA Header from xlsx relationship file
    condition_xpath_list = [str(i) for i in df_micro_in['Microenvironment Condition xPaths'].tolist() if i]
    condition_values = [str(i) for i in df_micro_in['ISA Condition Entities'].tolist() if i]
    condition_dict = {}
    j = 0
    #similar to process for variables above, create dictionary of discrete condition elements and their xPaths
    for condition_xpath in condition_xpath_list:
        for elem in root.findall('.//' + condition_xpath):
            path_tail = ''
            if '@' in condition_xpath:
                path_tail += re.search('\[@.*?\]', condition_xpath).group()
            if condition_values[j] in condition_dict:
                condition_dict[condition_values[j]].append(tree.getelementpath(elem) + path_tail)
            else:
                condition_dict[condition_values[j]] = tree.getelementpath(elem) + path_tail
                condition_dict[condition_values[j]] = [condition_dict[condition_values[j]]]
        j += 1

    #similar to process for variables above, find values from xPaths in dictionary and write to output_data dictionary
    for condition in condition_dict:
        data_out[condition] = []
        if len(data_out['Sample Name']) > 1:
            for j in range(len(data_out['Sample Name'])):
                data_str = '"'
                for cond_path in condition_dict[condition]:
                    result = re.search("phenotype_dataset\[(\d+)\]", cond_path)
                    if int(result.group(1)) == j + 1:
                        if '@' in cond_path:
                            result = re.split(r"@", cond_path)
                            attr = result[1].replace(']', '')
                            data_str += root.find(cond_path).attrib[attr].replace('\n', '').replace('\t', '').strip()
                        else:
                            data_str += root.find(cond_path).text.replace('\n', '').replace('\t', '').strip()
                        break
                data_out[condition].append(data_str + '"')
        else:
            data_str = '"'
            cond_path = ''.join(condition_dict[condition])
            if '@' in cond_path:
                result = re.split(r"@", cond_path)
                attr = result[1].replace(']', '')
                data_str += root.find(cond_path).attrib[attr].replace('\n', '').replace('\t', '').strip()
            else:
                data_str += root.find(cond_path).text.replace('\n', '').replace('\t', '').strip()
            data_out[condition].append(data_str + '"')
    #add phenotype_dataset[@keywords] value for each phenotype dataset to the output file under 'Assay Name' column
    data_out['Assay Name'] = pheno_keywords
    df_micro = pd.DataFrame(data = data_out)
    micro_filename = 'a_Microenvironment_' + file_base
    f_a_micro = open(micro_filename, 'w')
    f_a_micro.write(df_micro.to_string(header=True, index=False))
    f_a_micro.close
    return(micro_filename)

microenvironment = root.findall('.//microenvironment')
if len(microenvironment) > 0:
    a_file_list.append(a_microenvironment(microenvironment))
else:
    print('No Microenvironment Assay')
def a_cellcycle(cell_cycle_elems,cell_phase_elems):
    '''
    :param cell_phase_elems: List of cell_cycle_phase elements
    :return: a_CellCycle.txt file name to be appended to assay file list
    '''
    #Import cell cycle phase xPaths, correlate phase ISA headers, cell cycle summary xPaths, and correlate summary ISA headers
    #from excel file and write each entity as string to list
    df_cycle_in = pd.read_excel(rF'{db}', sheet_name='A_CellCycle', keep_default_na= False, usecols=
    ['Cell Cycle Phase ISA Entities', 'Cell Cycle Phase xPaths', 'Cell Cycle Summary ISA Entities', 'Cell Cycle Summary xPaths'])
    phase_paths = [str(i) for i in df_cycle_in['Cell Cycle Phase xPaths'].tolist() if i]
    phase_headers = [str(i) for i in df_cycle_in['Cell Cycle Phase ISA Entities'].tolist() if i]
    summary_paths = [str(i) for i in df_cycle_in['Cell Cycle Summary xPaths'].tolist() if i]
    summary_headers = [str(i) for i in df_cycle_in['Cell Cycle Summary ISA Entities'].tolist() if i]
    if len(phase_paths) != len(phase_headers):
        print('Cell Cycle - Issue in Excel File')
        #TODO change to error logging
    #Initialize dictionary for writing to pandas dataframe
    data_out = {'Sample Name': [], 'Characteristic [Cell Cycle Model]': [], 'Characteristic [Cell Cycle Phase]': []}
    pheno_keywords = []
    ent_in_file = []
    summary_in_file = []
    #Loop through each potential cell_cycle_phase element for each cell_cycle_phase occurance
    #If the element exists and if the correlate ISA entity is not in the ent_in_file list, append it
    #Output is a list of all ISA entities that are found in the xml file
    for elem in cell_phase_elems:
        for num in range(len(phase_paths)):
            if root.find(tree.getelementpath(elem) + phase_paths[num]) is not None:
                if phase_headers[num] not in ent_in_file:
                    ent_in_file.append(phase_headers[num])

    #If header is not in entity list (not in file), replace the header and the associated xPath with a '' to maintain
    #correct indexing, then remove blank '' from list
    for num in range(len(phase_headers)):
        if phase_headers[num] not in ent_in_file:
            phase_headers[num] = ''
            phase_paths[num] = ''
    phase_headers = [i for i in phase_headers if i]
    phase_paths = [i for i in phase_paths if i]

    #Add headers to dictionary keys with an empty list as value
    for header in phase_headers:
        data_out[header] = []

    #Repeat process with summary elements (within /cell_cycle, not contianed in /cell_cycle/cell_cycle_phase/
    for elem in cell_cycle_elems:
        for num in range(len(summary_paths)):
            if root.find(tree.getelementpath(elem) + summary_paths[num]) is not None:
                if summary_headers[num] not in summary_in_file:
                    summary_in_file.append(summary_headers[num])
    for num in range(len(summary_headers)):
        if summary_headers[num] not in summary_in_file:
            summary_headers[num] = ''
            summary_paths[num] = ''
    summary_headers = [i for i in summary_headers if i]
    summary_paths = [i for i in summary_paths if i]
    for header in summary_headers:
        data_out[header] = []

    #Loop through cell cycle phase element and cell cycle summary elements and write content to dictionary
    for elem in cell_phase_elems:
        data_out['Sample Name'].append('"' + sample_name_base + '.' + elem.getparent().getparent().getparent().attrib['ID'] + '"')
        pheno_keywords.append('"' + elem.getparent().getparent().getparent().attrib['keywords'].strip().strip(',') + '"')
        data_out['Characteristic [Cell Cycle Model]'].append('"' + elem.getparent().attrib['model'].strip() + '"')
        data_out['Characteristic [Cell Cycle Phase]'].append('"' + elem.attrib['name'].strip() + '"')
        for num in range(len(phase_paths)):
            if root.find(tree.getelementpath(elem) + phase_paths[num]) is not None:
                if '@' in phase_paths[num]:
                    result = re.split(r"@", phase_paths[num])
                    attr = result[1].replace(']', '')
                    try:
                        data_out[phase_headers[num]].append\
                            ('"' + (root.find(tree.getelementpath(elem) + phase_paths[num]).attrib[attr]).strip() + '"')
                    except:
                        data_out[phase_headers[num]].append('""')
                else:
                    try:
                        data_out[phase_headers[num]].append\
                            ('"' + (root.find(tree.getelementpath(elem) + phase_paths[num]).text).strip() + '"')
                    except:
                        data_out[phase_headers[num]].append('""')
            else:
                data_out[phase_headers[num]].append('""')

        summary_base_path = tree.getelementpath(elem).rsplit('/', 1)[0]
        for num in range(len(summary_paths)):
            if root.find(summary_base_path + summary_paths[num]) is not None:
                if '@' in summary_paths[num]:
                    result = re.split(r"@", summary_paths[num])
                    attr = result[1].replace(']', '')
                    try:
                        data_out[summary_headers[num]].append\
                            ('"' + (root.find(summary_base_path + summary_paths[num]).attrib[attr]).strip() + '"')
                    except:
                        data_out[summary_headers[num]].append('""')
                else:
                    try:
                        data_out[summary_headers[num]].append\
                            ('"' + (root.find(summary_base_path + summary_paths[num]).text).strip() + '"')
                    except:
                        data_out[summary_headers[num]].append('""')
            else:
                data_out[summary_headers[num]].append('""')
    #Write dictionary to dataframe, then dataframe to text file
    data_out['Assay Name'] = pheno_keywords
    df_cycle = pd.DataFrame(data=data_out)
    cycle_filename = 'a_CellCycle_' + file_base
    f_a_cycle = open(cycle_filename, 'w')
    f_a_cycle.write(df_cycle.to_string(header=True, index=False))
    f_a_cycle.close
    return (cycle_filename)


cell_phase = root.findall('.//cell_cycle/cell_cycle_phase')
cell_cycle = root.findall('.//cell_cycle')
if len(cell_cycle) > 0:
    a_file_list.append(a_cellcycle(cell_cycle,cell_phase))
else:
    print('No Cell Cycle Assay')

def a_celldeath(cell_death_elems):
    '''

    :param cell_death_elems:  List of /cell_death elements
    :return: a_CellDeath.txt file name to be appended to assay file list
    Operation: Similar to a_cellcycle function, except there are only terms within  (analogous to cell_cycle_phase)
    '''

    # Import cell death xPaths, correlate cell death ISA headers from excel file and write each entity as string to list
    df_death_in = pd.read_excel(rF'{db}', sheet_name='A_CellDeath', keep_default_na=False, usecols=
    ['Cell Death ISA Entities', 'Cell Death xPaths'])
    death_paths = [str(i) for i in df_death_in['Cell Death xPaths'].tolist() if i]
    death_headers = [str(i) for i in df_death_in['Cell Death ISA Entities'].tolist() if i]

    if len(death_paths) != len(death_headers):
        print('Cell Death - Issue in Excel File')
        #TODO change to error logging
    #Initialize dictionary for writing to pandas dataframe
    data_out = {'Sample Name': []}
    ent_in_file = []
    pheno_keywords = []
    #Loop through each potential cell_death for each cell_death occurance
    #If the element exists and if the correlate ISA entity is not in the ent_in_file list, append it
    #Output is a list of all ISA entities that are found in the xml file
    for elem in cell_death_elems:
        for num in range(len(death_paths)):
            if root.find(tree.getelementpath(elem) + death_paths[num]) is not None:
                if death_headers[num] not in ent_in_file:
                    ent_in_file.append(death_headers[num])

    #If header is not in entity list (not in file), replace the header and the associated xPath with a '' to maintain
    #correct indexing, then remove blank '' from list
    for num in range(len(death_headers)):
        if death_headers[num] not in ent_in_file:
            death_headers[num] = ''
            death_paths[num] = ''
    death_headers = [i for i in death_headers if i]
    death_paths = [i for i in death_paths if i]

    #Add headers to dictionary keys with an empty list as value
    for header in death_headers:
        data_out[header] = []

    # Loop through cell death elements and write content to dictionary
    for elem in cell_death_elems:
        data_out['Sample Name'].append('"' + sample_name_base + '.' + elem.getparent().getparent().attrib['ID'] + '"')
        pheno_keywords.append('"' + elem.getparent().getparent().attrib['keywords'].strip().strip(',') + '"')
        for num in range(len(death_paths)):
            if root.find(tree.getelementpath(elem) + death_paths[num]) is not None:
                if '@' in death_paths[num]:
                    result = re.split(r"@", death_paths[num])
                    attr = result[1].replace(']', '')
                    try:
                        data_out[death_headers[num]].append\
                            ('"' + (root.find(tree.getelementpath(elem) + death_paths[num]).attrib[attr]).strip() + '"')
                    except:
                        data_out[death_headers[num]].append('""')
                else:
                    try:
                        data_out[death_headers[num]].append\
                            ('"' + (root.find(tree.getelementpath(elem) + death_paths[num]).text).strip() + '"')
                    except:
                        data_out[death_headers[num]].append('""')
            else:
                data_out[death_headers[num]].append('""')
    #Write data_out dictionary to dataframe, then write dataframe to output text file
    data_out['Assay Name'] = pheno_keywords
    df_death = pd.DataFrame(data=data_out)
    death_filename = 'a_CellDeath_' + file_base
    f_a_death = open(death_filename, 'w')
    f_a_death.write(df_death.to_string(header=True, index=False))
    f_a_death.close
    return (death_filename)

cell_death = root.findall('.//cell_death')
if len(cell_death) > 0:
    a_file_list.append(a_celldeath(cell_death))
else:
    print('No Cell Death Assay')
def a_mechanics(cell_mechanics_elems):
    '''
    :param cell_mechanics_elems: List of all mechanics elements found in the xml file
    :return: The cell mechanics file name to be appended to the assay file list
    '''
    # Import cell mechanics xPaths, correlate cell mechanics ISA headers from excel file and write each entity as string to list
    df_mech_in = pd.read_excel(rF'{db}', sheet_name='A_Mechanics', keep_default_na=False, usecols=
    ['Cell Mechanics ISA Entities', 'Cell Mechanics xPaths'])
    mech_paths = [str(i) for i in df_mech_in['Cell Mechanics xPaths'].tolist() if i]
    mech_headers = [str(i) for i in df_mech_in['Cell Mechanics ISA Entities'].tolist() if i]

    if len(mech_paths) != len(mech_headers):
        print('Cell Mechanics - Issue in Excel File')
        # TODO change to error logging

    data_out = {'Sample Name' : [], 'Characteristic[Cell Part]' : []}
    pheno_keywords = []
    lvl_tracking = {}
    ent_in_file = []

    #Determine cell part level of each mechanics element (whole cell, cell_part, sub part of cell_part) and save to
    #dictionary as value for the mechanics element xPath as the key

    for elem in cell_mechanics_elems:
        elem_path = tree.getelementpath(elem)
        lvl = len(re.findall('(cell_part)', elem_path))
        lvl_tracking[elem_path] = lvl
    #Find sample name and cell part information with logic based on cell part level of each mechanics element, then
    #save information to appropriate key within data_out dictionary
    for elem_path in lvl_tracking:
        if lvl_tracking[elem_path] == 0:
            data_out['Sample Name'].append('"' + sample_name_base + '.' + root.find(elem_path).getparent().getparent()
                                           .attrib['ID'].strip() + '"')
            pheno_keywords.append('"' + root.find(elem_path).getparent().getparent().attrib['keywords'].strip() + '"')
            data_out['Characteristic[Cell Part]'].append('"Entire Cell"')
        elif lvl_tracking[elem_path] == 1:
            data_out['Sample Name'].append('"' + sample_name_base + '.' + root.find(elem_path).getparent().getparent()
                                           .getparent().attrib['ID'].strip() + '"')
            pheno_keywords.append('"' + root.find(elem_path).getparent().getparent().getparent()
                                  .attrib['keywords'].strip() + '"')
            data_out['Characteristic[Cell Part]'].append('"' + root.find(elem_path).getparent().getparent()
                                                         .attrib['name'].strip() + '"')
        elif lvl_tracking[elem_path] == 2:
            data_out['Sample Name'].append('"' + sample_name_base + '.' + root.find(elem_path).getparent()
                                           .getparent().getparent().getparent().attrib['ID'].strip() + '"')
            pheno_keywords.append('"' + root.find(elem_path).getparent().getparent().getparent().getparent()
                                  .attrib['keywords'].strip() + '"')
            data_out['Characteristic[Cell Part]'].append('"' + root.find(elem_path).getparent().getparent().attrib['name']
                .strip()+ " of " + root.find(elem_path).getparent().getparent().getparent().attrib['name'].strip() + '"')
        else:
            print("Issue - cell_part/cell_part/cell_part structure is not supported by current version")
            #TODO change to error logging

    # Loop through each potential mechanics/"element" for each .//mechanics element
    # If the element exists and if the correlate ISA entity is not in the ent_in_file list, append it
    # Output is a list of all ISA entities that are found in the xml file
    for elem in cell_mechanics_elems:
        for num in range(len(mech_paths)):
            if root.find(tree.getelementpath(elem) + mech_paths[num]) is not None:
                if mech_headers[num] not in ent_in_file:
                    ent_in_file.append(mech_headers[num])

    # If header is not in entity list (not in file), replace the header and the associated xPath with a '' to maintain
    # correct indexing, then remove blank '' from list
    for num in range(len(mech_headers)):
        if mech_headers[num] not in ent_in_file:
            mech_headers[num] = ''
            mech_paths[num] = ''
    mech_headers = [i for i in mech_headers if i]
    mech_paths = [i for i in mech_paths if i]

    for header in mech_headers:
        data_out[header] = []

    for elem in cell_mechanics_elems:
        for num in range(len(mech_paths)):
            if root.find(tree.getelementpath(elem) + mech_paths[num]) is not None:
                if '@' in mech_paths[num]:
                    result = re.split(r"@", mech_paths[num])
                    attr = result[1].replace(']', '')
                    try:
                        data_out[mech_headers[num]].append\
                            ('"' + (root.find(tree.getelementpath(elem) + mech_paths[num]).attrib[attr]).strip() + '"')
                    except:
                        data_out[mech_headers[num]].append('""')
                else:
                    try:
                        data_out[mech_headers[num]].append\
                            ('"' + (root.find(tree.getelementpath(elem) + mech_paths[num]).text).strip() + '"')
                    except:
                        data_out[mech_headers[num]].append('""')
            else:
                data_out[mech_headers[num]].append('""')
    #Write data_out dictionary to dataframe, then write dataframe to output text file

    data_out['Assay Name'] = pheno_keywords
    df_mech = pd.DataFrame(data=data_out)
    mech_filename = 'a_Mechanics_' + file_base
    f_a_mech = open(mech_filename, 'w')
    f_a_mech.write(df_mech.to_string(header=True, index=False))
    f_a_mech.close
    return (mech_filename)

#Encapsulates cell_part elements too
cell_mechanics = root.findall('.//mechanics')
if len(cell_mechanics) > 0:
    a_file_list.append(a_mechanics(cell_mechanics))
else:
    print('No Cell Mechanics Assay')

print('\n\n')
def a_geo_props(cell_geo_elems):
    '''

    :param cell_geo_elems: List of all cell geometric_properties elements found with
            root.findall(.//geometric_properties
    :return: geometric properties assay filename, to be appended to assay file list
    Operations:
        1) Import xPaths, values, attributes, and ISA header info from xlsx relationship file
        2) Determine cell_part "level" for each element in cell_geo_elems, use level to
            find info in xml for sample name, cell_part characteristic, and assay names in ISA file
        3) Determine measurements that exist in file and write to dictionary as keys. For each measurement key,
            determine attributes that exist in file and write to dictionary as list of values for mesurement key
        4) Loop through measurement keys and associated attribute values. Use indices within xlsx file to create
            dictionary with keys of ISA headers (ISA entity beginning + ISA measurement + ISA entity tail). Each
            key will have a two element list containing measurement xpath at key[0] and attribute at key[1].
        5) Loop through elems in cell_geo_elems and try to write info from xml file to data_out dict using dictionary
            created in step 4
        6) Append assay names to data_out, write data_out to dataframe, then write dataframe to Geometrical Properties
            assay text file
    '''
    # Import geometric properties parameter value xPaths, correlate ISA value name, potential attributes
    # for parameter values, and ISA header information for writing headers from excel file
    # Write each entity as string to list
    #geo_prop_attr: remove NaN from rows with no content, then replace NaN within dataframe with "" blank
    df_geo_val_in = pd.read_excel(rF'{db}', sheet_name='A_GeometricalProperties', keep_default_na=False, usecols=
    ['Cell Geometrical Properties ISA Measurement Name', 'Cell Geometrical Properties xPaths'])
    df_geo_attr_in = pd.read_excel(rF'{db}', sheet_name='A_GeometricalProperties', keep_default_na=True, usecols=
    ['Cell Geometrical Properties Attributes', 'Cell Geometrical Properties ISA Entity Beginning',
     'Cell Geometrical Properties ISA Entity Tail']).dropna(how='all').fillna("")
    #remove blanks from geo_measure_paths, geo_measure, and geo_attr
    #Don't remove blanks from ISA entity beginning + tail lists (blank may be valid
    geo_measure_paths = [str(i) for i in df_geo_val_in['Cell Geometrical Properties xPaths'].tolist() if i]
    geo_measure = [str(i) for i in df_geo_val_in['Cell Geometrical Properties ISA Measurement Name'].tolist() if i]
    geo_attr = [str(i) for i in df_geo_attr_in['Cell Geometrical Properties Attributes'].tolist() if i]
    geo_header_begin = [str(i) for i in df_geo_attr_in['Cell Geometrical Properties ISA Entity Beginning'].tolist()]
    geo_header_tail = [str(i) for i in df_geo_attr_in['Cell Geometrical Properties ISA Entity Tail'].tolist()]
    if len(geo_measure_paths) != len(geo_measure):
        print('Cell Geometrical Properties - Issue in Excel File, Value Section')
         # TODO change to error logging
    if not (len(geo_attr) == len(geo_header_begin) == len(geo_header_tail)):
        print('Cell Geometrical Properties - Issue in Excel File, Attribute Section')
        # TODO change to error logging

    data_out = {'Sample Name': [], 'Characteristic[Cell Part]': []}
    pheno_keywords = []
    lvl_tracking = {}
    ent_in_file = {}

    # Determine cell part level of each geometrical property element (whole cell, cell_part, sub part of cell_part) and save to
    # dictionary as value for the geometrical property element xPath as the key
    for elem in cell_geo_elems:
        elem_path = tree.getelementpath(elem)
        lvl = len(re.findall('(cell_part)', elem_path))
        lvl_tracking[elem_path] = lvl
    # Find sample name and cell part information with logic based on cell part level of each geometrical property
    # element, then save information to appropriate key within data_out dictionary
    for elem_path in lvl_tracking:
        if lvl_tracking[elem_path] == 0:
            data_out['Sample Name'].append('"' + sample_name_base + '.' + root.find(elem_path).getparent().getparent()
                                           .attrib['ID'].strip() + '"')
            pheno_keywords.append('"' + root.find(elem_path).getparent().getparent().attrib['keywords'].strip() + '"')
            data_out['Characteristic[Cell Part]'].append('"Entire Cell"')
        elif lvl_tracking[elem_path] == 1:
            data_out['Sample Name'].append('"' + sample_name_base + '.' + root.find(elem_path).getparent().getparent()
                                           .getparent().attrib['ID'].strip() + '"')
            pheno_keywords.append('"' + root.find(elem_path).getparent().getparent().getparent()
                                  .attrib['keywords'].strip() + '"')
            data_out['Characteristic[Cell Part]'].append('"' + root.find(elem_path).getparent().getparent()
                                                         .attrib['name'].strip() + '"')
        elif lvl_tracking[elem_path] == 2:
            data_out['Sample Name'].append('"' + sample_name_base + '.' + root.find(elem_path).getparent()
                                           .getparent().getparent().getparent().attrib['ID'].strip() + '"')
            pheno_keywords.append('"' + root.find(elem_path).getparent().getparent().getparent().getparent()
                                  .attrib['keywords'].strip() + '"')
            data_out['Characteristic[Cell Part]'].append('"' + root.find(elem_path).getparent().getparent().attrib['name']
                    .strip() + " of " + root.find(elem_path).getparent().getparent().getparent().attrib['name'].strip() + '"')
        else:
            print("Issue - cell_part/cell_part/cell_part structure is not supported by current version")
            # TODO change to error logging

    #Create dictionary with geo property measurements in file as keys, in order, and initialize as list
    measure_in_file = {}
    for path in geo_measure_paths:
        for elem in cell_geo_elems:
            #Check to see if measurement elem exists, if so check to see if value exists for measurement elem
            if (root.find(tree.getelementpath(elem) + path) is not None) and\
            (root.find(tree.getelementpath(elem) + path).text is not None):
                measure_in_file[path] = []
                break
    #add occurances of attribute under each path header in measure_in_file dictionary created above
    #break after attribute confirmed for path (need to write ISA header)
    #attributes added in order of list from xlsx sheet
    for path in measure_in_file:
        for attr in geo_attr:
            for elem in cell_geo_elems:
                if (root.find(tree.getelementpath(elem) + path) is not None):
                    if attr in root.find(tree.getelementpath(elem) + path).attrib:
                        measure_in_file[path].append(attr)
                        break

    ISA_head_path = {}
    #for existing path/attribute combination, find index within their respective list from xlsx file
    #Use index to concatenate ISA entity beginning + ISA measurement + ISA entity tail to form ISA header, which will
    #be the header within the data file. Use the header as a key within the ISA_head_path dict, which will contain values
    # of the xpath and attr to use to get the appropriate data from the xml file
    for path in measure_in_file:
        measure_index = geo_measure_paths.index(path)
        ISA_head_path['Parameter Value[' + geo_measure[measure_index] + ']'] = [path]
        for attr in measure_in_file[path]:
            attr_index = geo_attr.index(attr)
            ISA_head = geo_header_begin[attr_index] + geo_measure[measure_index] + geo_header_tail[attr_index]
            ISA_head_path[ISA_head] = [path, attr]

    #initialize data_out by writing headers
    for header in ISA_head_path:
        data_out[header] = []

    #text elements (measurement values) have dictionary value len == 1, attributes have len == 2
    # Iterate through list of elems
    # Iterate through list of headers
    # write data_out[header].append(find data in xml)
    for elem in cell_geo_elems:
        for header in ISA_head_path:
            path = ISA_head_path[header][0]
            if len(ISA_head_path[header]) == 1:
                try:
                    data_out[header].append('"' + root.find(tree.getelementpath(elem) + path).text.strip() + '"')
                except:
                    data_out[header].append('""')
            else:
                attr = ISA_head_path[header][1]
                try:
                    data_out[header].append('"' + (root.find(tree.getelementpath(elem) + path).attrib[attr]).strip() + '"')
                except:
                    data_out[header].append('""')

    data_out['Assay Name'] = pheno_keywords
    df_geo = pd.DataFrame(data=data_out)
    geo_filename = 'a_GeometricalProperties_' + file_base
    f_a_geo = open(geo_filename, 'w')
    f_a_geo.write(df_geo.to_string(header=True, index=False, col_space=0, justify='center'))
    f_a_geo.close
    return (geo_filename)

cell_geo_props = root.findall('.//geometrical_properties')
if len(cell_geo_props) > 0:
    a_file_list.append(a_geo_props(cell_geo_props))

def a_motility(cell_motility_elems):
    '''
    :param cell_motility_elems: List of all cell motility elements found with root.findall(.//motility)
    :return: cell motility assay file name, to be appended to list of assay file names

    '''

    # Import motility parameter value xPaths, correlate ISA value name, potential attributes
    # for parameter values, and ISA header information for writing headers from excel file
    # Write each entity as string to list
    # motility_attr: remove NaN from rows with no content, then replace NaN within dataframe with "" blank
    df_motility_val_in = pd.read_excel(rF'{db}', sheet_name='A_Motility', keep_default_na=False, usecols=
    ['Cell Motility ISA Measurement Name', 'Cell Motility xPaths'])
    df_motility_attr_in = pd.read_excel(rF'{db}', sheet_name='A_Motility', keep_default_na=True, usecols=
    ['Cell Motility Attributes', 'Cell Motility ISA Entity Beginning',
     'Cell Motility ISA Entity Tail']).dropna(how='all').fillna("")
    # remove blanks from motility_measure_paths, motility_measure, and motility_attr
    # Don't remove blanks from ISA entity beginning + tail lists (blank may be valid)
    motility_measure_paths = [str(i) for i in df_motility_val_in['Cell Motility xPaths'].tolist() if i]
    motility_measure = [str(i) for i in df_motility_val_in['Cell Motility ISA Measurement Name'].tolist() if i]
    motility_attr = [str(i) for i in df_motility_attr_in['Cell Motility Attributes'].tolist() if i]
    motility_header_begin = [str(i) for i in df_motility_attr_in['Cell Motility ISA Entity Beginning'].tolist()]
    motility_header_tail = [str(i) for i in df_motility_attr_in['Cell Motility ISA Entity Tail'].tolist()]
    if len(motility_measure_paths) != len(motility_measure):
        print('Cell Motility - Issue in Excel File, Value Section')
        # TODO change to error logging
    if not (len(motility_attr) == len(motility_header_begin) == len(motility_header_tail)):
        print('Cell Motility - Issue in Excel File, Attribute Section')
        # TODO change to error logging

    data_out = {'Sample Name': [], 'Characteristic[Motility Type]': []}
    pheno_keywords = []
    ent_in_file = {}
    ISA_head_path = {}
    #For elems in list of found motility elements, append info that characterizes the element to data_out
    #If restriction/surface_variables, add to ISA_head_path for finding data from xml
    for elem in cell_motility_elems:
        data_out['Sample Name'].append('"' + sample_name_base + '.' + elem.getparent().getparent()
                                       .getparent().attrib['ID'].strip() + '"')
        pheno_keywords.append('"' + elem.getparent().getparent().getparent().attrib['keywords'].strip() + '"')
        data_out['Characteristic[Motility Type]'].append('"' + elem.tag.strip() +'"')
        if root.find(tree.getelementpath(elem) + '/restriction/surface_variable') is not None:
            if 'name' in root.find(tree.getelementpath(elem) + '/restriction/surface_variable').attrib:
                ISA_head_path['Characteristic[Restriction Surface Name]'] = ['/restriction/surface_variable','name']
            if 'MeSH_ID' in root.find(tree.getelementpath(elem) + '/restriction/surface_variable').attrib:
                ISA_head_path['Characteristic[Restriction Surface MeSH ID]'] = ['/restriction/surface_variable', 'MeSH_ID']

    measure_in_file = {}
    for path in motility_measure_paths:
        for elem in cell_motility_elems:
            # Check to see if measurement elem exists, if so check to see if value exists for measurement elem
            if (root.find(tree.getelementpath(elem) + path) is not None) and \
                    (root.find(tree.getelementpath(elem) + path).text is not None):
                measure_in_file[path] = []
                break
    # add occurances of attribute under each path header in measure_in_file dictionary created above
    # break after attribute confirmed for path (need to write ISA header)
    # attributes added in order of list from xlsx sheet
    for path in measure_in_file:
        for attr in motility_attr:
            for elem in cell_motility_elems:
                if (root.find(tree.getelementpath(elem) + path) is not None):
                    if attr in root.find(tree.getelementpath(elem) + path).attrib:
                        measure_in_file[path].append(attr)
                        break

    # for existing path/attribute combination, find index within their respective list from xlsx file
    # Use index to concatenate ISA entity beginning + ISA measurement + ISA entity tail to form ISA header, which will
    # be the header within the data file. Use the header as a key within the ISA_head_path dict, which will contain values
    # of the xpath and attr to use to get the appropriate data from the xml file
    for path in measure_in_file:
        measure_index = motility_measure_paths.index(path)
        ISA_head_path['Parameter Value[' + motility_measure[measure_index] + ']'] = [path]
        for attr in measure_in_file[path]:
            attr_index = motility_attr.index(attr)
            ISA_head = motility_header_begin[attr_index] + motility_measure[measure_index] + motility_header_tail[attr_index]
            ISA_head_path[ISA_head] = [path, attr]

    # initialize data_out by writing headers
    for header in ISA_head_path:
        data_out[header] = []

    # text elements (measurement values) have dictionary value len == 1, attributes have len == 2
    # Iterate through list of elems
    # Iterate through list of headers
    # write data_out[header].append(find data in xml)
    for elem in cell_motility_elems:
        for header in ISA_head_path:
            path = ISA_head_path[header][0]
            if len(ISA_head_path[header]) == 1:
                try:
                    data_out[header].append('"' + root.find(tree.getelementpath(elem) + path).text.strip() + '"')
                except:
                    data_out[header].append('""')
            else:
                attr = ISA_head_path[header][1]
                try:
                    data_out[header].append(
                        '"' + (root.find(tree.getelementpath(elem) + path).attrib[attr]).strip() + '"')
                except:
                    data_out[header].append('""')

    data_out['Assay Name'] = pheno_keywords
    df_motility = pd.DataFrame(data=data_out)
    motility_filename = 'a_Motility_' + file_base
    f_a_motility = open(motility_filename, 'w')
    f_a_motility.write(df_motility.to_string(header=True, index=False, col_space=0, justify='center'))
    f_a_motility.close
    return (motility_filename)

cell_motility = root.findall('.//motility/restricted')
cell_motility.extend(root.findall('.//motility/unrestricted'))
if len(cell_motility) > 0:
    a_file_list.append(a_motility(cell_motility))

#print(a_file_list)
'''
Study

Correct I File
I file - write entity then skip if ScriptVar?
'''