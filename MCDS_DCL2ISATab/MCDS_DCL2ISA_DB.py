'''
MCDS_DCL2ISA_DB.py - using a MultiCellDS digital cell line XML file, generate associated ISA-Tab files

Input:
  1 MultiCellDS digital cell line file  <DCL-root-filename>.xml
Output:
  3 ISA files types:
   i_<DCL-root-filename>.txt
   s_<DCL-root-filename>.txt
   a_<DCL-root-filename>.txt
        up to 10 assay files

Author: Connor Burns
Date:
  v0.1 - Feb 2021
  v0.2 - Apr 2021
          Passes CSSI ISA-Tab validation, all existing xPaths are placed, added command line run ability
  v1.0 - Apr 2021
'''

import os
import sys
import re
import pandas as pd
from lxml import etree
from tqdm import tqdm
import argparse

os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))
#change current working directory to script location
cwd = os.getcwd()
db = os.path.join(cwd, 'ISA_MCDS_Relationships_Py_CB.xlsx')
DCL_folder = os.path.join(os.path.dirname(cwd), 'All_Digital_Cell_Lines')
ISA_out = os.path.join(cwd, 'ISATabOutput')

#All optional arguments, with default to convert all DCL's in All_Digital_Cell_Lines folder except 'obsolete' files
#File input '-i' can be folder containing DCL's, full file path of DCL, or file name within All_Digital_Cell_Lines folder
my_parser = argparse.ArgumentParser(description='Convert MCDS-DCL to ISATab.txt files \nInput "infile" folder path containing DCLs or file path for single DCL file')
my_parser.add_argument('-i' ,'--infile_or_dir', type=str, action ='store', help = 'Input file path or folder path', default = DCL_folder)
my_parser.add_argument('-o','--outfolder', type=str, action ='store', help = 'Desired ISATab Output Directory', default = ISA_out)
my_parser.add_argument('--keep_obs_DCL', help = 'T/F Certain files may not be supported for conversion. By default, they are removed from the input folder. Call "--print_obs_DCL" to see list' , action='store_true')
my_parser.add_argument('--print_obs_DCL', help = 'T/F Option to print list of obsolete DCL files', action='store_true')
my_parser.add_argument('--check_elems', help = 'T/F Check to see if there are unsupported conversion elems in DCL.xml', action='store_true')
args = my_parser.parse_args()
in_file_path = args.infile_or_dir
output_dir = args.outfolder
keep_obs_DCL = args.keep_obs_DCL
print_obs_DCL = args.print_obs_DCL

check_elems = args.check_elems

try:
    os.mkdir(output_dir)
except FileExistsError:
    pass

Obsolete_DCL = ['MCDS_L_0000000001.xml','MCDS_L_0000000002.xml','MCDS_L_0000000043.xml'
                ,'MCDS_L_0000000045.xml','MCDS_L_0000000046.xml']
if print_obs_DCL == True:
    print(Obsolete_DCL)

#for directory input
if os.path.isdir(in_file_path):
    DCL_f_list = os.listdir(in_file_path)
    if keep_obs_DCL == False:
        DCL_f_list = [DCL for DCL in DCL_f_list if DCL not in Obsolete_DCL]
        # These files are removed because they have been updated to cell lines 238-242, in same order as original
    DCL_list = [os.path.join(in_file_path, x) for x in DCL_f_list]

    #for file input with absolute path
elif os.path.isfile(in_file_path):
    DCL_list = [in_file_path]
else:
    #for file name only inputs: assume in All_Digital_CellLines
    DCL_list = [os.path.join(DCL_folder, in_file_path)]


#Use this to limit input by index if desired
input_list = DCL_list[:]

for DCL_in in tqdm(input_list, desc= 'DCL.xml to ISA.txt file conversion', total=len(input_list), mininterval=5):
    DCL_file = os.path.basename(DCL_in)
    #Check file type, skip file if not xml
    if DCL_file[-4:] != '.xml':
        print(f"\n\033[1;31;40m Error: File Input {DCL_file} is not an .xml file and will be skipped")
        continue

   #initialize parse, check .xml file type. If not cell_line, skip
    parser = etree.XMLParser(remove_comments=True)
    tree = etree.parse(DCL_in, parser=parser)
    root = tree.getroot()
    if root.get('type') != 'cell_line':
        print(f"\n\033[1;31;40m Error: File Input {DCL_file} is not a Digital Cell Line and will be skipped")
        continue
    if root.get('version') != '1.0.0':
        print('Warning - MCDS version ' + str(root.get('version')) + ' may not be supported for this conversion script')

    #performs root iter and compares results against supported MCDS element conversion list
    if check_elems == True:
        exist_elem_series = pd.read_excel(f'{db}', sheet_name='Supported MCDS Elems', usecols=['xPath - Index Removed'])
        exist_list = exist_elem_series['xPath - Index Removed'].tolist()
        nonexist_list = []
        check_tree = etree.parse(DCL_in, parser=parser)
        check_root = check_tree.getroot()
        for child in check_root.iter():
            # Entity type will be text if it has text and attributes
            if (type(child.text) == str and len(child.text.strip()) > 0):
                check_path = re.sub(r"\[[0-9]]", "", check_tree.getelementpath(child))
                if check_path not in exist_list:
                    nonexist_list.append(check_path)
            if len(child.keys()) > 0:
                for attr in child.keys():
                    check_path =  "".join([re.sub(r"\[[0-9]]", "", check_tree.getelementpath(child)), "[@", attr, "]"])
                    if check_path not in exist_list:
                        nonexist_list.append(check_path)
        if len(nonexist_list) > 0:
            print(f'\nThe following XML elements may not be supported:\n File Name: {DCL_file}  \tElements:\n', nonexist_list)

    # Find and define DCL input file path
    DCL_name = DCL_file.replace('.xml','')
    file_base = DCL_name + '.txt'
    output_folder = os.path.join(output_dir,DCL_name)

    try:
        os.mkdir(output_folder)
    except FileExistsError:
        pass

    #print('Input file: ', DCL_file)

    df = pd.read_excel(rF'{db}', sheet_name='MCDS-DCL to ISA-Tab', usecols=['ISA-Tab Entity', 'ISA File Location', 'ISA Entity Type',
                                          'MCDS-DCL Correlate Entity', 'MCDS-DCL Correlate X-Path', 'Multiples for xPath'])

    #Assay files:
    sample_name_base = root.find('cell_line/metadata/MultiCellDB/ID').text +'.' + root.find('cell_line[@ID]').attrib['ID']
    a_file_list = []
    assay_type_list = []
    study_prot_list = []
    study_prot_types = []
    assay_parameters = []
    assay_param_components = []


    def a_header_fix(a_filename, df_a, protocol_ref, ref_col_num):
        '''

        :param a_filename: string of desired assay filename
        :param df_a: pd dataframe of the assay file contents
        :param protocol_ref: string of protocol name for the assay
        :param ref_col_num: index at which the protocol ref column should be added
        :return:
        '''
        # change unit columns to 'Units" - had to keep separate above for dictionary
        # remove " from parameters (will be added back on when writing to file), could fix this by rewriting assay functions
        # df_a = df_a.replace('"','', regex=True)
        df_a.columns = ['Units' if 'units' in x.lower() else x for x in df_a.columns]
        param_list = (
        [x.replace('Parameter Value[', '').replace(']', '').strip() for x in df_a.columns if 'Parameter Value' in x])
        params = ';'.join(param_list)
        bad_cols = ['Sample Name', 'Parameter Value', 'MCDS-DCL File', 'Units', 'Assay Name', 'Source Name', 'Phenotype Dataset Collection']

        # If column does not have string from bad_cols, remove characteristic[ and add to list
        comps = [x.replace('Characteristic[', '').strip(']').strip() for x in df_a.columns if
                 not any(y in x for y in bad_cols)]
        # if component has parameter from param_list in name, remove
        for j, comp in enumerate(comps):
            if 'pkpd' in a_filename.lower():
                if 'Drug #' in comp:
                    comp = comp.split(':',1)[1]
            for param in param_list:
                if param in comp:
                    comp = comp.replace(param, '').replace('-','').strip()
            comps[j] = comp
        param_comps = ';'.join(list(set(comps)))
        df_a.insert(ref_col_num, 'Protocol REF', [protocol_ref] * len(df_a['Sample Name']))
        a_rows = [df_a.columns.values.tolist()] + df_a.values.tolist()

        # Initialize assay file
        a_path = os.path.join(output_folder, a_filename)
        f_a = open(a_path, 'w')
        # write content to assay file
        for j, row in enumerate(a_rows):
            if j > 0:
                f_a.write('\n')
            row = [('"' + str(x) + '"') for x in row]
            f_a.write('\t'.join(row))

        f_a.close()
        return (params, param_comps)

    def write_dict_to_txt(file_name, data_dict, data_dict_col):
        '''
        :param file_name: Assay or study text file name for writing
        :param data_dict: name of dictionary in which the assay or study data is stored
        :param data_dict_col: known column of data_dict to establish number of values for looping
        :return: Tab delimited txt output file, written "vertically" by dictionary key and values
        '''
        f_dict = open(os.path.join(output_folder, file_name), 'w')
        str_list = []
        for keys in data_dict.keys():
            str_list.append(keys)
        str_out = '\t'.join(str_list)
        f_dict.write(str_out + '\n')
        for j in range(len(data_dict[data_dict_col])):
            str_list = []
            str_out = ''
            for keys in data_dict.keys():
                str_list.append(data_dict[keys][j])
            str_out = '\t'.join(str_list)
            f_dict.write(str_out + '\n')
        f_dict.close()


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
        assay_variables = [x.strip() for x in micro_var_names.keys()]
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
                            pass
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
                    var_key = var_name + ' - ' + var
                elif "ID" in var or "measurement_type" in var:
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
        data_out['MCDS-DCL File'] = ['"' + DCL_file + '"']*len(data_out['Sample Name'])

        micro_filename = 'a_Microenvironment_' + file_base
        micro_protocol = 'Microenvironment Characterization'
        #Remove " from dictionary values. They'll be added in later when writing to file
        for data in data_out:
            data_out[data] = [x.replace('"','') for x in data_out[data]]
        df_micro = pd.DataFrame(data=data_out)

        for variable in assay_variables:
            if ('Parameter Value['+variable+' type]') in df_micro.columns:
                var_type = list(set([x for x in df_micro['Parameter Value['+variable+' type]'] if x]))
                if len(var_type) == 1:
                    var_type = var_type[0]
                    df_micro = df_micro.drop(labels = ['Parameter Value['+variable+' type]'], axis = 1)
                    for col in df_micro.columns:
                        if variable in col:
                            var_name_type = '.'.join([variable.strip(), var_type.strip()])
                            new_col = col.replace(variable, var_name_type)
                            df_micro.rename({col: new_col}, axis=1, inplace=True)
        params, param_comps = a_header_fix(micro_filename,df_micro,micro_protocol,1)

        return(micro_filename, micro_protocol, params,param_comps)


    microenvironment = root.findall('.//microenvironment')
    if len(microenvironment) > 0:
        micro_results = a_microenvironment(microenvironment)
        a_file_list.append(micro_results[0])
        assay_type_list.append('Microenvironment')
        study_prot_types.append('Characterization')
        study_prot_list.append(micro_results[1])
        assay_parameters.append(micro_results[2])
        assay_param_components.append(micro_results[3])

    else:
        pass
        #print('No Microenvironment Assay')

    def a_cellcycle(cell_cycle_elems,cell_phase_elems):
        '''
        :param cell_phase_elems: List of cell_cycle_phase elements
        :return: a_CellCycle.txt file name to be appended to assay file list
        '''
        #Import cell cycle phase xPaths, correlate phase ISA headers, cell cycle summary xPaths, and correlate summary ISA headers
        #from excel file and write each entity as string to list
        df_cycle_in = pd.read_excel(rF'{db}', sheet_name='A_CellCycle', keep_default_na= False, usecols=
            ['Cell Cycle Phase ISA Entities', 'Cell Cycle Phase xPaths', 'Cell Cycle Summary ISA Entities',
             'Cell Cycle Summary xPaths'])
        phase_paths = [str(i) for i in df_cycle_in['Cell Cycle Phase xPaths'].tolist() if i]
        phase_headers = [str(i) for i in df_cycle_in['Cell Cycle Phase ISA Entities'].tolist() if i]
        summary_paths = [str(i) for i in df_cycle_in['Cell Cycle Summary xPaths'].tolist() if i]
        summary_headers = [str(i) for i in df_cycle_in['Cell Cycle Summary ISA Entities'].tolist() if i]
        if len(phase_paths) != len(phase_headers):
            print('Cell Cycle - Issue in Excel File')
            # TODO change to error logging
        # Initialize dictionary for writing to pandas dataframe
        data_out = {'Sample Name': [], 'Characteristic[Phenotype Type]': [], 'Characteristic[Cell Cycle Model]': [],
                    'Characteristic[Cell Cycle Phase]': []}

        pheno_keywords = []
        ent_in_file = []
        summary_in_file = []
        # Loop through each potential cell_cycle_phase element for each cell_cycle_phase occurance
        # If the element exists and if the correlate ISA entity is not in the ent_in_file list, append it
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
            try:
                data_out['Characteristic[Phenotype Type]'].append('"' + elem.getparent().getparent().attrib['type'] + '"')
            except:
                data_out['Characteristic[Phenotype Type]'].append('""')
            data_out['Characteristic[Cell Cycle Model]'].append('"' + elem.getparent().attrib['model'].strip() + '"')
            data_out['Characteristic[Cell Cycle Phase]'].append('"' + elem.attrib['name'].strip() + '"')
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
        data_out['MCDS-DCL File'] = ['"' + DCL_file + '"']*len(data_out['Sample Name'])
        cycle_filename = 'a_CellCycle_' + file_base

        cycle_protocol = 'Cell Cycle Characterization'
        for data in data_out:
            data_out[data] = [x.replace('"', '') for x in data_out[data]]
        df_cycle = pd.DataFrame(data=data_out)

        params, param_comps = a_header_fix(cycle_filename, df_cycle, cycle_protocol, 4)

        return (cycle_filename, cycle_protocol,params,param_comps)
    cell_phase = root.findall('.//cell_cycle/cell_cycle_phase')
    cell_cycle = root.findall('.//cell_cycle')
    if len(cell_cycle) > 0:
        cellcycle_results = a_cellcycle(cell_cycle,cell_phase)
        a_file_list.append(cellcycle_results[0])
        assay_type_list.append('Cell Cycle')
        study_prot_types.append('Characterization')
        study_prot_list.append(cellcycle_results[1])
        assay_parameters.append(cellcycle_results[2])
        assay_param_components.append(cellcycle_results[3])
    else:
        pass
        #print('No Cell Cycle Assay')

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

        #Initialize dictionary for writing to pandas dataframe
        data_out = {'Sample Name': [], 'Characteristic[Phenotype Type]': []}
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
            try:
                data_out['Characteristic[Phenotype Type]'].append('"' + elem.getparent().attrib['type'] + '"')
            except:
                data_out['Characteristic[Phenotype Type]'].append('""')
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
        data_out['MCDS-DCL File'] = ['"' + DCL_file + '"']*len(data_out['Sample Name'])
        death_filename = 'a_CellDeath_' + file_base
        death_protocol = 'Cell Death Characterization'
        for data in data_out:
            data_out[data] = [x.replace('"', '') for x in data_out[data]]
        df_death = pd.DataFrame(data=data_out)

        params, param_comps = a_header_fix(death_filename, df_death, death_protocol, 3)

        return (death_filename, death_protocol,params,param_comps)

    cell_death = root.findall('.//cell_death')
    if len(cell_death) > 0:
        results = a_celldeath(cell_death)
        a_file_list.append(results[0])
        assay_type_list.append('Cell Death')
        study_prot_list.append(results[1])
        study_prot_types.append('Characterization')
        assay_parameters.append(results[2])
        assay_param_components.append(results[3])
    else:
        pass
        #print('No Cell Death Assay')

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

        data_out = {'Sample Name' : [], 'Characteristic[Phenotype Type]': [], 'Characteristic[Cell Part]' : []}
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
                try:
                    data_out['Characteristic[Phenotype Type]'].append('"' + root.find(elem_path).getparent().attrib['type'] + '"')
                except:
                    data_out['Characteristic[Phenotype Type]'].append('""')
                pheno_keywords.append('"' + root.find(elem_path).getparent().getparent().attrib['keywords'].strip() + '"')
                data_out['Characteristic[Cell Part]'].append('"Entire Cell"')
            elif lvl_tracking[elem_path] == 1:
                data_out['Sample Name'].append('"' + sample_name_base + '.' + root.find(elem_path).getparent().getparent()
                                               .getparent().attrib['ID'].strip() + '"')
                try:
                    data_out['Characteristic[Phenotype Type]'].append('"' + root.find(elem_path).getparent().attrib['type'] + '"')
                except:
                    data_out['Characteristic[Phenotype Type]'].append('""')
                pheno_keywords.append('"' + root.find(elem_path).getparent().getparent().getparent()
                                      .attrib['keywords'].strip() + '"')
                data_out['Characteristic[Cell Part]'].append('"' + root.find(elem_path).getparent().getparent()
                                                             .attrib['name'].strip() + '"')
            elif lvl_tracking[elem_path] == 2:
                data_out['Sample Name'].append('"' + sample_name_base + '.' + root.find(elem_path).getparent()
                                               .getparent().getparent().getparent().attrib['ID'].strip() + '"')
                try:
                    data_out['Characteristic[Phenotype Type]'].append('"' + root.find(elem_path).getparent().attrib['type'] + '"')
                except:
                    data_out['Characteristic[Phenotype Type]'].append('""')
                pheno_keywords.append('"' + root.find(elem_path).getparent().getparent().getparent().getparent()
                                      .attrib['keywords'].strip() + '"')
                data_out['Characteristic[Cell Part]'].append('"' + root.find(elem_path).getparent().getparent().attrib['name']
                    .strip()+ " of " + root.find(elem_path).getparent().getparent().getparent().attrib['name'].strip() + '"')
            else:
                print("Issue - cell_part/cell_part/cell_part structure is not supported by current version")


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
        data_out['MCDS-DCL File'] = ['"' + DCL_file + '"']*len(data_out['Sample Name'])
        mech_filename = 'a_Mechanics_' + file_base
        mech_protocol = 'Cell Mechanics Measurements'
        for data in data_out:
            data_out[data] = [x.replace('"', '') for x in data_out[data]]
        df_mech = pd.DataFrame(data=data_out)

        params, param_comps = a_header_fix(mech_filename, df_mech, mech_protocol, 3)

        return (mech_filename, mech_protocol, params, param_comps)


    #Encapsulates cell_part elements too
    cell_mechanics = root.findall('.//mechanics')
    if len(cell_mechanics) > 0:
        results = a_mechanics(cell_mechanics)
        a_file_list.append(results[0])
        assay_type_list.append('Cell Mechanics')
        study_prot_list.append(results[1])
        study_prot_types.append('Measurement')
        assay_parameters.append(results[2])
        assay_param_components.append(results[3])

    else:
        pass
        #print('No Cell Mechanics Assay')

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

        if not (len(geo_attr) == len(geo_header_begin) == len(geo_header_tail)):
            print('Cell Geometrical Properties - Issue in Excel File, Attribute Section')


        data_out = {'Sample Name': [], 'Characteristic[Phenotype Type]' : [] ,'Characteristic[Cell Part]': []}
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
                try:
                    data_out['Characteristic[Phenotype Type]'].append('"' + root.find(elem_path).getparent().attrib['type'] + '"')
                except:
                    data_out['Characteristic[Phenotype Type]'].append('""')
                pheno_keywords.append('"' + root.find(elem_path).getparent().getparent().attrib['keywords'].strip() + '"')
                data_out['Characteristic[Cell Part]'].append('"Entire Cell"')
            elif lvl_tracking[elem_path] == 1:
                data_out['Sample Name'].append('"' + sample_name_base + '.' + root.find(elem_path).getparent().getparent()
                                               .getparent().attrib['ID'].strip() + '"')
                try:
                    data_out['Characteristic[Phenotype Type]'].append('"' + root.find(elem_path).getparent().attrib['type'] + '"')
                except:
                    data_out['Characteristic[Phenotype Type]'].append('""')
                pheno_keywords.append('"' + root.find(elem_path).getparent().getparent().getparent()
                                      .attrib['keywords'].strip() + '"')
                data_out['Characteristic[Cell Part]'].append('"' + root.find(elem_path).getparent().getparent()
                                                             .attrib['name'].strip() + '"')
            elif lvl_tracking[elem_path] == 2:
                data_out['Sample Name'].append('"' + sample_name_base + '.' + root.find(elem_path).getparent()
                                               .getparent().getparent().getparent().attrib['ID'].strip() + '"')
                try:
                    data_out['Characteristic[Phenotype Type]'].append('"' + root.find(elem_path).getparent().attrib['type'] + '"')
                except:
                    data_out['Characteristic[Phenotype Type]'].append('""')
                pheno_keywords.append('"' + root.find(elem_path).getparent().getparent().getparent().getparent()
                                      .attrib['keywords'].strip() + '"')
                data_out['Characteristic[Cell Part]'].append('"' + root.find(elem_path).getparent().getparent().attrib['name']
                        .strip() + " of " + root.find(elem_path).getparent().getparent().getparent().attrib['name'].strip() + '"')
            else:
                print("Issue - cell_part/cell_part/cell_part structure is not supported by current version")

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
        params = []
        for path in measure_in_file:
            measure_index = geo_measure_paths.index(path)
            ISA_head_path['Parameter Value[' + geo_measure[measure_index] + ']'] = [path]
            params.append(geo_measure[measure_index])
            for attr in measure_in_file[path]:
                attr_index = geo_attr.index(attr)
                ISA_head = geo_header_begin[attr_index] + geo_measure[measure_index] + geo_header_tail[attr_index]
                ISA_head_path[ISA_head] = [path, attr]
        #separate measurements by semicolon to write to I file
        assay_params = ';'.join(params)
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
        data_out['MCDS-DCL File'] = ['"' + DCL_file + '"']*len(data_out['Sample Name'])
        geo_filename = 'a_GeometricalProperties_' + file_base
        geo_protocol = 'Cell Geometrical Property Measurements'
        for data in data_out:
            data_out[data] = [x.replace('"', '') for x in data_out[data]]
        df_geo = pd.DataFrame(data=data_out)

        params, param_comps = a_header_fix(geo_filename, df_geo, geo_protocol, 3)

        return (geo_filename, geo_protocol, params, param_comps)


    cell_geo_props = root.findall('.//geometrical_properties')
    if len(cell_geo_props) > 0:
        results = a_geo_props(cell_geo_props)
        a_file_list.append(results[0])
        assay_type_list.append('Cell Geometrical Properties')
        study_prot_list.append(results[1])
        study_prot_types.append('Measurement')
        assay_parameters.append(results[2])
        assay_param_components.append(results[3])


    else:
        pass
        #print('No Cell Geometrical Properties Assay')

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

        if not (len(motility_attr) == len(motility_header_begin) == len(motility_header_tail)):
            print('Cell Motility - Issue in Excel File, Attribute Section')


        data_out = {'Sample Name': [], 'Characteristic[Phenotype Type]': [],'Characteristic[Motility Type]': []}
        pheno_keywords = []
        ent_in_file = {}
        ISA_head_path = {}
        #For elems in list of found motility elements, append info that characterizes the element to data_out
        #If restriction/surface_variables, add to ISA_head_path for finding data from xml
        for elem in cell_motility_elems:
            data_out['Sample Name'].append('"' + sample_name_base + '.' + elem.getparent().getparent()
                                           .getparent().attrib['ID'].strip() + '"')
            try:
                data_out['Characteristic[Phenotype Type]'].append('"' + elem.getparent().getparent().attrib['type'] + '"')
            except:
                data_out['Characteristic[Phenotype Type]'].append('""')
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
        params = []

        for path in measure_in_file:
            measure_index = motility_measure_paths.index(path)
            ISA_head_path['Parameter Value[' + motility_measure[measure_index] + ']'] = [path]
            params.append(motility_measure[measure_index])
            for attr in measure_in_file[path]:
                attr_index = motility_attr.index(attr)
                ISA_head = motility_header_begin[attr_index] + motility_measure[measure_index] + motility_header_tail[attr_index]
                ISA_head_path[ISA_head] = [path, attr]

        #join parameter measurements with ; for I file
        assay_params = ';'.join(params)
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
        data_out['MCDS-DCL File'] = ['"' + DCL_file + '"']*len(data_out['Sample Name'])
        motility_filename = 'a_Motility_' + file_base
        motility_protocol = 'Cell Motility Characterization'
        for data in data_out:
            data_out[data] = [x.replace('"', '') for x in data_out[data]]
        df_motility = pd.DataFrame(data=data_out)

        params, param_comps = a_header_fix(motility_filename, df_motility, motility_protocol, 2)

        return (motility_filename, motility_protocol, params, param_comps)


    cell_motility = root.findall('.//motility/restricted')
    cell_motility.extend(root.findall('.//motility/unrestricted'))
    if len(cell_motility) > 0:
        results = a_motility(cell_motility)
        a_file_list.append(results[0])
        assay_type_list.append('Cell Motility')
        study_prot_list.append(results[1])
        study_prot_types.append('Characterization')
        assay_parameters.append(results[2])
        assay_param_components.append(results[3])
    else:
        pass
        #print('No Cell Motility Assay')

    pkpd_s_data = {}
    def a_s_PKPD(PKPD_drug, PKPD_pd_meas):
        '''
        :param PKPD_drug: list of xml elements found under PKPD/drug xPath
        :param PKPD_pd_meas: list of xml elements found under PKPD/pharmacodynamics xPath
        :return: list of PKPD file names to be appended to study file list and assay file list, respectively
        '''
        df_PKPD_drug_in = pd.read_excel(rF'{db}', sheet_name='A_S_PKPD', keep_default_na=False, usecols=
        ['PKPD Drug ISA Headers', 'PKPD Drug Attributes'])
        df_PKPD_pd_in = pd.read_excel(rF'{db}', sheet_name='A_S_PKPD', keep_default_na=False, usecols=
        ['PKPD PD Headers', 'PKPD PD xPaths'])
        drug_header = [str(i) for i in df_PKPD_drug_in['PKPD Drug ISA Headers'].tolist() if i]
        drug_attr = [str(i) for i in df_PKPD_drug_in['PKPD Drug Attributes'].tolist() if i]
        pd_header = [str(i) for i in df_PKPD_pd_in['PKPD PD Headers'].tolist() if i]
        pd_paths = [str(i) for i in df_PKPD_pd_in['PKPD PD xPaths'].tolist() if i]

        if len(drug_attr) != len(drug_header):
            print('PKPD - Issue in Excel File, Drug Section')

        if len(pd_paths) != len(pd_header):
            print('PKPD - Issue in Excel File, Pharmacodynamics')

        #TODO - Is drug ID global (will it match drug ID of other phenotype datasets, or is it only a local ID?)
        drug_ID_name = {}
        s_data_out = {}
        drug_out = {}
        exist_drug_attr = []
        #Drug elements - Study
        #Check to see which attributes exist, make list of existing attributes and reorder to match xlsx relationship file

        for attr in drug_attr:
            for elem in PKPD_drug:
                if root.find(tree.getelementpath(elem)).attrib[attr] is not None:
                    exist_drug_attr.append(attr)
                    break
        exist_drug_attr = [x for x in drug_attr if x in exist_drug_attr]
        #initialize headers and save to dictionary with paired attribute
        for attr in exist_drug_attr:
            header = drug_header[drug_attr.index(attr)]
            s_data_out[header] = []
            drug_out[header] = attr
        #loop through existing, ordered headers and write content to appropriate header in s_data_put
        #save drug ID number as key and name as value in dictionary
        for header in drug_out:
            for elem in PKPD_drug:
                if drug_out[header] == 'name':
                    drug_ID_name[root.find(tree.getelementpath(elem)).attrib['ID']] = root.find(tree.getelementpath(elem)).attrib['name'].strip()
                try:
                    s_data_out[header].append('"' + root.find(tree.getelementpath(elem)).attrib[drug_out[header]].strip() + '"')
                except:
                    s_data_out[header].append('""')

        #TODO - may need to update in future for cases if there are different drugs under different phenotype_datasets
        #section below commented out because we are writing data to study file instead of PKPD_study
        # df_s_PKPD = pd.DataFrame(data=s_data_out)
        # s_PKPD_filename = 's_PKPD_' + file_base
        # f_s_PKPD = open(os.path.join(output_folder,s_PKPD_filename), 'w')
        # f_s_PKPD.write(df_s_PKPD.to_string(header=True, index=False, col_space=0, justify='center'))
        # f_s_PKPD.close

        pheno_keywords = []
        therapy_drugs = {}
        #make dictionary of drugs under each measurement set, append sample name and measurement set ID to a_data_out
        a_data_out = {'Sample Name': [], 'Characteristic[Phenotype Type]': [], 'Measurement Set ID#': []}
        for elem in pkpd_pd_meas:
            a_data_out['Sample Name'].append('"' + sample_name_base + '.' + elem.getparent().getparent().getparent()
                                           .getparent().attrib['ID'].strip() + '"')
            try:
                a_data_out['Characteristic[Phenotype Type]'].append('"' + elem.getparent().getparent().getparent().attrib['type'] + '"')
            except:
                a_data_out['Characteristic[Phenotype Type]'].append('""')
            pheno_keywords.append('"' + elem.getparent().getparent().getparent().getparent().attrib['keywords'].strip() + '"')
            try:
                a_data_out['Measurement Set ID#'].append('"' + elem.attrib['ID'].strip() +'"')
            except:
                a_data_out['Measurement Set ID#'].append('""')
            therapy_drugs[elem] = root.findall(tree.getelementpath(elem) + '/therapy/drug')
        #make dictionary of existing drug measurement headers and xPaths using list index
        exist_drug_measurements = {}
        for path in pd_paths:
            if '/dose' in path:
                for drug_elem_list in therapy_drugs.values():
                    for drug_elem in drug_elem_list:
                        if '@' not in path:
                            if root.find(tree.getelementpath(drug_elem) + path).text is not None:
                                exist_drug_measurements[pd_header[pd_paths.index(path)]] = [path]
                                break
                        else:
                            result = re.split(r"@", path)
                            new_path = result[0].replace('[','')
                            attr = result[1].replace(']', '')
                            if root.find(tree.getelementpath(drug_elem) + new_path).attrib[attr] is not None:
                                exist_drug_measurements[pd_header[pd_paths.index(path)]] = [new_path, attr]

        pre_params = [x for x in exist_drug_measurements.keys() if "Parameter Value" in x]
        params = set([x.split('[')[1].split('-')[0].strip(']').strip() for x in pre_params])
        assay_params = ';'.join(list(params))

        #Find max number of drugs in measurement set
        max_drug_len = len(therapy_drugs[max(therapy_drugs, key=lambda x: len(set(therapy_drugs[x])))])
        #initialize headers
        if max_drug_len > 0:
            for i in range(max_drug_len):
                num_name = 'Drug #' + str(i + 1) + ': ' + 'Drug Name'
                a_data_out[num_name] = []
                for meas in exist_drug_measurements:
                    num_head = 'Drug #' + str(i+1) + ': ' + meas
                    a_data_out[num_head] = []
        #write drug content: loop through drug elements and write content for each drug in drug list
        for elem_list in therapy_drugs.values():
            for j,elem in enumerate(elem_list):
                num_name = 'Drug #' + str(j + 1) + ': ' + 'Drug Name'
                try:
                   a_data_out[num_name].append('"' + drug_ID_name[elem.attrib['ID']].strip() + '"')
                except:
                   a_data_out[num_name].append('""')
                for meas in exist_drug_measurements:
                    num_head = 'Drug #' + str(j + 1) + ': ' + meas
                    drug_path = exist_drug_measurements[meas][0]
                    if len(exist_drug_measurements[meas]) == 1:
                        try:
                            a_data_out[num_head].append('"' + root.find(tree.getelementpath(elem) + drug_path).text + '"')
                        except:
                            a_data_out[num_head].append('""')
                    else:
                        drug_attrib = exist_drug_measurements[meas][1]
                        try:
                            a_data_out[num_head].append('"' + root.find(tree.getelementpath(elem) + drug_path).attrib[drug_attrib] + '"')
                        except:
                            a_data_out[num_head].append('""')

        exist_response_measurements = {}
        #Loop through non dose paths from excel relationship sheet, search for existence in measurement set elements
        for path in pd_paths:
            if '/dose' not in path:
                for elem in PKPD_pd_meas:
                    if '@' not in path:
                            if root.find(tree.getelementpath(elem) + path).text is not None:
                                exist_response_measurements[pd_header[pd_paths.index(path)]] = [path]
                                break
                    else:
                            result = re.split(r"@", path)
                            new_path = result[0].replace('[', '')
                            attr = result[1].replace(']', '')
                            if root.find(tree.getelementpath(elem) + new_path).attrib[attr] is not None:
                                exist_response_measurements[pd_header[pd_paths.index(path)]] = [new_path, attr]
        #initalize existing ISA headers for measurement_set/responses
        for header in exist_response_measurements:
            a_data_out[header] = []
            if 'Parameter Value' in header:
                pre_params.append(header)
        #loop through measurement elements, write response content to a_data_out
        for elem in PKPD_pd_meas:
            for header in exist_response_measurements:
                response_path = exist_response_measurements[header][0]
                if len(exist_response_measurements[header]) == 1:
                    try:
                        a_data_out[header].append('"' + root.find(tree.getelementpath(elem) + response_path).text + '"')
                    except:
                        a_data_out[header].append('""')
                else:
                    response_attrib = exist_response_measurements[header][1]
                    try:
                        a_data_out[header].append('"' + root.find(tree.getelementpath(elem) + response_path).attrib[response_attrib] + '"')
                    except:
                        a_data_out[header].append('""')

        a_data_out['Assay Name'] = pheno_keywords
        a_data_out['MCDS-DCL File'] = ['"' + DCL_file + '"']*len(a_data_out['Sample Name'])

        a_PKPD_filename = 'a_PKPD_' + file_base
        PKPD_protocol = 'Drug Pharmacodynamic Measurements'
        for data in a_data_out:
            a_data_out[data] = [x.replace('"', '') for x in a_data_out[data]]
        df_PKPD_a = pd.DataFrame(data=a_data_out)

        params, param_comps = a_header_fix(a_PKPD_filename, df_PKPD_a, PKPD_protocol, 2)

        return (s_data_out,a_PKPD_filename, PKPD_protocol, params, param_comps)

    pkpd_drug = root.findall('.//PKPD/drug')
    pkpd_pd_meas = root.findall('.//PKPD/pharmacodynamics/therapy_measurement_set')
    if (len(pkpd_drug) > 0) or (len(pkpd_pd_meas) > 0):
        results = a_s_PKPD(pkpd_drug,pkpd_pd_meas)
        pkpd_s_data = results[0]
        a_file_list.append(results[1])
        assay_type_list.append('PKPD')
        study_prot_list.append(results[2])
        study_prot_types.append('Measurement')
        assay_parameters.append(results[3])
        assay_param_components.append(results[4])

    else:
        pass
        #print('No PKPD Assay')

    def a_trans_processes(trans_processes_elems):
        '''

        :param trans_processes_elems: List of transport processes / variable xml elements, from root.findall()
        :return: transport processes file name, to be appended to list of assay file names
        Operation:
            1) Import data from xlsx relationship file
            2) Loop through each variable element, determine attributes that exist for variables
            3) Write headers and content for variables to data_out dictionary
            4) Determine which measurements exist in file, determine which atributes exist for the measurements
            5) Write existing measurements and associated attributes to data_out
        '''
        # Import transport process variable attributes, correlate ISA value name, potential variable measurements,
        # potential measurement attributes, and ISA header information for writing headers from excel file
        # Write each entity as string to list
        # trans_meas_attr_in: remove NaN from rows with no content, then replace NaN within dataframe with "" blank
        df_trans_var_in = pd.read_excel(rF'{db}', sheet_name='A_TransportProcesses', keep_default_na=False, usecols=
        ['Transport Processes ISA Variable Headers', 'Transport Processes Variable Attributes'])
        df_trans_meas_in = pd.read_excel(rF'{db}', sheet_name='A_TransportProcesses', keep_default_na=False, usecols=
        ['Transport Processes ISA Measurement Name', 'Transport Processes Variable Measurements'])
        df_trans_meas_attr_in = pd.read_excel(rF'{db}', sheet_name='A_TransportProcesses', keep_default_na=True, usecols=
        ['Transport Processes Variable Measurement Attributes', 'Transport Processes ISA Entity Beginning',
         'Transport Processes ISA Entity Tail']).dropna(how='all').fillna("")
        # remove blanks from transport processes variable and measurements dataframes
        # Don't remove blanks measurement attribute dataframe(ISA entity beginning + tail lists blanks may be valid)
        trans_var_attr = [str(i) for i in df_trans_var_in['Transport Processes Variable Attributes'].tolist() if i]
        trans_var = [str(i) for i in df_trans_var_in['Transport Processes ISA Variable Headers'].tolist() if i]
        trans_meas_path = [str(i) for i in df_trans_meas_in['Transport Processes Variable Measurements'].tolist() if i]
        trans_meas = [str(i) for i in df_trans_meas_in['Transport Processes ISA Measurement Name'].tolist() if i]
        meas_attr = [str(i) for i in df_trans_meas_attr_in['Transport Processes Variable Measurement Attributes'].tolist() if i]
        meas_header_begin = [str(i) for i in df_trans_meas_attr_in['Transport Processes ISA Entity Beginning'].tolist()]
        meas_header_tail = [str(i) for i in df_trans_meas_attr_in['Transport Processes ISA Entity Tail'].tolist()]
        if len(trans_var_attr) != len(trans_var):
            print('Transport Processes - Issue in Excel File, Variable Section')

        if len(trans_meas_path) != len(trans_meas):
            print('Transport Processes - Issue in Excel File, Measurement Section')

        if not (len(meas_attr) == len(meas_header_begin) == len(meas_header_tail)):
            print('Transport Processes - Issue in Excel File, Measurement Attribute Section')


        data_out = {'Sample Name': [], 'Characteristic[Phenotype Type]': []}
        pheno_keywords = []
        var_attr_in_file = []
        ISA_head_path = {}

        # For elems in list of found transport_processes/variable elements, append info that characterizes the element to data_out
        for elem in trans_processes_elems:
            data_out['Sample Name'].append('"' + sample_name_base + '.' + elem.getparent().getparent()
                                           .getparent().attrib['ID'].strip() + '"')
            try:
                data_out['Characteristic[Phenotype Type]'].append('"' + elem.getparent().getparent().attrib['type'] + '"')
            except:
                data_out['Characteristic[Phenotype Type]'].append('""')
            pheno_keywords.append('"' + elem.getparent().getparent().getparent().attrib['keywords'].strip() + '"')

        for attr in trans_var_attr:
            for elem in trans_processes_elems:
                # Check to see if variable attribute exists, if so add to list of variables
                if (root.find(tree.getelementpath(elem)).attrib[attr]) is not None:
                    var_attr_in_file.append(attr)
                    break
        #Reorder list to match order attributes appear in xlsx relationship file
        var_attr_in_file = [x for x in trans_var_attr if x in var_attr_in_file]
        #Initialize headers with list of attributes in file, make properly indexed list of headers for attributes in file
        attr_headers = []
        for attr in var_attr_in_file:
            header = trans_var[trans_var_attr.index(attr)]
            data_out[header] = []
            attr_headers.append(header)

        #Write information for variables to data out
        for elem in trans_processes_elems:
            for ind, header in enumerate(attr_headers):
                try:
                    data_out[header].append('"' + root.find(tree.getelementpath(elem)).attrib[var_attr_in_file[ind]] + '"')
                except:
                    data_out[header].append('""')

        measure_in_file = {}
        for path in trans_meas_path:
            for elem in trans_processes_elems:
                # Check to see if measurement elem exists, if so check to see if value exists for measurement elem
                if (root.find(tree.getelementpath(elem) + path) is not None) and \
                        (root.find(tree.getelementpath(elem) + path).text is not None):
                    measure_in_file[path] = []
                    break
        # add occurances of attribute under each path header in measure_in_file dictionary created above
        # break after attribute confirmed for path (need to write ISA header)
        # attributes added in order of list from xlsx sheet
        for path in measure_in_file:
            for attr in meas_attr:
                for elem in trans_processes_elems:
                    if (root.find(tree.getelementpath(elem) + path) is not None):
                        if attr in root.find(tree.getelementpath(elem) + path).attrib:
                            measure_in_file[path].append(attr)
                            break
        # for existing path/attribute combination, find index within their respective list from xlsx file
        # Use index to concatenate ISA entity beginning + ISA measurement + ISA entity tail to form ISA header, which will
        # be the header within the data file. Use the header as a key within the ISA_head_path dict, which will contain values
        # of the xpath and attr to use to get the appropriate data from the xml file
        params = []

        for path in measure_in_file:
            measure_index = trans_meas_path.index(path)
            ISA_head_path['Parameter Value[' + trans_meas[measure_index] + ']'] = [path]
            params.append(trans_meas[measure_index])
            for attr in measure_in_file[path]:
                attr_index = meas_attr.index(attr)
                ISA_head = meas_header_begin[attr_index] + trans_meas[measure_index] + meas_header_tail[
                    attr_index]
                ISA_head_path[ISA_head] = [path, attr]
        assay_params = ';'.join(params)
        # initialize data_out by writing headers
        for header in ISA_head_path:
            data_out[header] = []

        # text elements (measurement values) have dictionary value len == 1, attributes have len == 2
        # Iterate through list of elems
        # Iterate through list of headers
        # write data_out[header].append(find data in xml)
        for elem in trans_processes_elems:
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
        data_out['MCDS-DCL File'] = ['"' + DCL_file + '"']*len(data_out['Sample Name'])
        trans_filename = 'a_TransportProcesses_' + file_base
        trans_protocol = 'Cell Transport Processes Measurements'
        for data in data_out:
            data_out[data] = [x.replace('"', '') for x in data_out[data]]
        df_trans = pd.DataFrame(data=data_out)

        params, param_comps = a_header_fix(trans_filename, df_trans, trans_protocol, 3)

        return (trans_filename, trans_protocol, params, param_comps)


    trans_process = root.findall('.//transport_processes/variable')
    if len(trans_process) > 0:
        results = a_trans_processes(trans_process)
        a_file_list.append(results[0])
        assay_type_list.append('Cell Transport Processes')
        study_prot_list.append(results[1])
        study_prot_types.append('Measurement')
        assay_parameters.append(results[2])
        assay_param_components.append(results[3])
    else:
        pass
        #print('No Transport Processes Assay')

    def transitions(cell_transitions):
        '''

        :param cell_transitions: list of transition elements found with root.findall
        :return: cell_transitions assay file name and assay parameters
        '''

        df_pheno_in = pd.read_excel(rF'{db}', sheet_name='A_StateTransition', keep_default_na=False, usecols=
        ['Transition Phenotype ISA Headers', 'Transition Phenotype xPaths'])
        df_transition_in = pd.read_excel(rF'{db}', sheet_name='A_StateTransition', keep_default_na=False, usecols=
        ['Transition ISA Headers', 'Transition xPaths'])
        pheno_header = [str(i) for i in df_pheno_in['Transition Phenotype ISA Headers'].tolist() if i]
        pheno_path = [str(i) for i in df_pheno_in['Transition Phenotype xPaths'].tolist() if i]
        trans_header = [str(i) for i in df_transition_in['Transition ISA Headers'].tolist() if i]
        trans_paths = [str(i) for i in df_transition_in['Transition xPaths'].tolist() if i]

        phenotype_child = []
        phenotype_elems = root.findall('.//transitions/phenotype_dataset_collection')
        params = []

        for path in pheno_path:
            for elem in phenotype_elems:
                if root.find(tree.getelementpath(elem) + path) is not None:
                    phenotype_child.append(path)
                    break

        transition_elems = root.findall('.//transitions/transition')
        j = len(transition_elems)

        data_out = {'Sample Name': [sample_name_base]*j}
        for elem in phenotype_elems:
            for path in phenotype_child:
                try:
                    data_out[pheno_header[pheno_path.index(path)] + elem.attrib['ID']] = [root.find(tree.getelementpath(elem) + path).text.replace('\n','').replace('\t','')]*j
                except:
                    data_out[pheno_header[pheno_path.index(path)] + elem.attrib['ID']] = ['']*j

        #Find existing transition xPaths and initialize headers
        #Add parameter values to params to append to I file
        exist_trans_paths = {}
        for path in trans_paths:
            for elem in transition_elems:
                if root.find(tree.getelementpath(elem) + path) is not None:
                    head = trans_header[trans_paths.index(path)]
                    data_out[head] = []
                    exist_trans_paths[path] = head
                    if 'Parameter Value' in head:
                        params.append(head.split('[')[1].split(']')[0])

        for elem in transition_elems:
            for path in exist_trans_paths:
                if '@' not in path:
                    try:
                        data_out[exist_trans_paths[path]].append(root.find(tree.getelementpath(elem) + path).text.replace('\n','').replace('\t',''))
                    except:
                        data_out[exist_trans_paths[path]].append('')
                else:
                    new_path = path.split('[')[0]
                    attr = path.split('@')[1].strip(']')
                    try:
                        data_out[exist_trans_paths[path]].append(root.find(tree.getelementpath(elem) + new_path).attrib[attr])
                    except:
                        data_out[exist_trans_paths[path]].append('')
        #TODO This section will need updating if multiple transitions are in a digital cell line
        for condition in root.findall('.//transitions/transition/conditions/variable/condition'):
            cond_name = condition.attrib['condition_type']
            params.append(cond_name)
            data_out['Parameter Value[' + cond_name + ']'] = condition.text.replace('\n','').replace('\t','')
            data_out[cond_name + ' - Units'] = condition.attrib['units']
            data_out['Parameter Value[' + cond_name + ' - Uncertainty]'] = condition.attrib['uncertainty']

        data_out['MCDS-DCL File'] = [ DCL_file ]*len(data_out['Sample Name'])
        transition_filename = 'a_StateTransition_' + file_base
        transition_protocol = 'Cell State Transition Characterization'
        df_transition = pd.DataFrame(data=data_out)

        params, param_comps = a_header_fix(transition_filename, df_transition, transition_protocol, 1)

        return (transition_filename, transition_protocol, params, param_comps)

    #This is used for HUVEC Cell Line
    cell_transitions = root.findall('.//transitions')
    if len(cell_transitions) > 0:
        results = transitions(cell_transitions)
        a_file_list.append(results[0])
        assay_type_list.append('Cell State Transitions')
        study_prot_list.append(results[1])
        study_prot_types.append('Characterization')
        assay_parameters.append(results[2])
        assay_param_components.append(results[3])

    def a_clinical_stain(stain_properties, stain_measurements):
        '''
        :param stain_properties: list of xml elements found under pathology_definitions/stain
        :param stain_measurements: list of xml elements found under pathology/stain
        :return: name of clinical stain assay to be appended to assay file list
        '''
        #Import ISA headers and paired xPaths from xlsx relationship file
        df_clin_stain_prop = pd.read_excel(rF'{db}', sheet_name='A_ClinicalStain', keep_default_na=False, usecols=
        ['Clinical Stain Properties ISA Headers', 'Clinical Stain Properties xPaths'])
        df_clin_stain_meas = pd.read_excel(rF'{db}', sheet_name='A_ClinicalStain', keep_default_na=False, usecols=
        ['Clinical Stain Measurements ISA Header', 'Clinical Stain Measurements xPaths'])
        # remove blanks from dataframes
        stain_prop_path = [str(i) for i in df_clin_stain_prop['Clinical Stain Properties xPaths'].tolist() if i]
        stain_prop_head = [str(i) for i in df_clin_stain_prop['Clinical Stain Properties ISA Headers'].tolist() if i]
        stain_meas_path = [str(i) for i in df_clin_stain_meas['Clinical Stain Measurements xPaths'].tolist() if i]
        stain_meas_head = [str(i) for i in df_clin_stain_meas['Clinical Stain Measurements ISA Header'].tolist() if i]

        if len(stain_prop_path) != len(stain_prop_head):
            print('Clinical Stain - Issue in Excel File, Properties Section')

        if len(stain_meas_path) != len(stain_meas_head):
            print('Clinical Stain - Issue in Excel File, Measurement Section')


        #Append the sample name base to data_out one time per different stain
        data_out = {'Sample Name': []}
        for i in range(max(len(stain_properties),len(stain_measurements))):
            data_out['Sample Name'].append('"' + sample_name_base + '"')

        #If ID's of stain elements match (they should be correctly ordered), add the element pair to dictionary
        matched_prop_meas = {}

        for prop_elem in stain_properties:
            for meas_elem in stain_measurements:
                if (prop_elem.attrib['ID'].strip() == meas_elem.attrib['ID'].strip()):
                    matched_prop_meas[prop_elem] = meas_elem
                    break

        #make list of unmatched measurement elements if there are any
        unmatched_meas_elems = [x for x in stain_measurements if x not in matched_prop_meas.values()]
        #determine existing stain property xPaths, write matched ISA header to dictionary as key and xPath to dictionary as value
        #If xPath is for an attribute, save the element path as key[0] and the attribute name as key[1]
        exist_properties = {}
        for path in stain_prop_path:
            header = stain_prop_head[stain_prop_path.index(path)]
            for elem in stain_properties:
                if '@' not in path:
                    if root.find(tree.getelementpath(elem) + path).text is not None:
                        exist_properties[header] = [path]
                else:
                    result = re.split(r"@", path)
                    new_path = result[0].replace('[', '')
                    attr = result[1].replace(']', '')
                    if (root.find(tree.getelementpath(elem) + path) is not None and
                    root.find(tree.getelementpath(elem) + path).attrib[attr] is not None):
                        exist_properties[header] = [new_path, attr]

            # determine existing stain measurement xPaths, write matched ISA header to dictionary as key and xPath to dictionary as value
            # If xPath is for an attribute, save the element path as key[0] and the attribute name as key[1]
        exist_measurements = {}
        for path in stain_meas_path:
            header = stain_meas_head[stain_meas_path.index(path)]

            for elem in stain_measurements:
                if '@' not in path:
                    if root.find(tree.getelementpath(elem) + path).text is not None:
                        exist_measurements[header] = [path]
                else:
                    result = re.split(r"@", path)
                    new_path = result[0].replace('[', '')
                    attr = result[1].replace(']', '')
                    if (root.find(tree.getelementpath(elem) + path) is not None and
                    root.find(tree.getelementpath(elem) + path).attrib[attr] is not None):
                        exist_measurements[header] = [new_path, attr]

        #Initialize existing headers for data_out
        pre_params = []

        data_out['Stain Name'] = []
        data_out['Study Stain ID#'] = []
        for header in exist_properties:
            data_out[header] = []
        for header in exist_measurements:
            data_out[header] = []
            if 'Parameter Value' in header:
                pre_params.append(header)

        #Write content for existing ISA headers and xPaths to data_out
        #If no ID, write '""' to data_out
        #If not in matched_prop_meas, does not have a matched measurement element. Therefore, make meas_elem '""' to trigger
        #except statement and put "" blank in measurement headers
        #If there are any measurement elements which are not matched, their content will be written to the file in
        #the following loop
        for prop_elem in stain_properties:
            try:
                data_out['Study Stain ID#'].append('"' + prop_elem.attrib['ID'] + '"')
            except:
                data_out['Study Stain ID#'].append('""')
            try:
                meas_elem = (matched_prop_meas[prop_elem])
            except KeyError:
                meas_elem = ""
            if prop_elem.attrib['name'] is not None:
                data_out['Stain Name'].append('"' + prop_elem.attrib['name'].strip() + '"')
            elif meas_elem.attrib['name'] is not None:
                data_out['Stain Name'].append('"' + meas_elem.attrib['name'].strip() + '"')
            else:
                prop_elem.attrib['name'].append('""')
            for header in exist_properties:
                prop_path = exist_properties[header][0]
                if len(exist_properties[header]) == 1:
                    try:
                        data_out[header].append(
                            '"' + root.find(tree.getelementpath(prop_elem) + prop_path).text +'"')
                    except:
                        data_out[header].append('""')
                elif len(exist_properties[header]) == 2:
                    prop_attr = exist_properties[header][1]
                    try:
                        data_out[header].append(
                            '"' + root.find(tree.getelementpath(prop_elem) + prop_path).attrib[prop_attr]+ '"')
                    except:
                        data_out[header].append('""')
            for header in exist_measurements:
                meas_path = exist_measurements[header][0]
                if len(exist_measurements[header]) == 1:
                    try:
                        data_out[header].append(
                            '"' + root.find(tree.getelementpath(meas_elem) + meas_path).text + '"')
                    except:
                        data_out[header].append('""')
                elif len(exist_measurements[header]) == 2:
                    meas_attr = exist_measurements[header][1]
                    try:
                        data_out[header].append(
                            '"' + root.find(tree.getelementpath(meas_elem) + meas_path).attrib[meas_attr] + '"')
                    except:
                        data_out[header].append('""')

        #append data to data_out for any unmatched measurements
        #Since there is no matched stain property, write "" to data_out for all property headers that exist in the file
        if len(unmatched_meas_elems) > 0:
            for unmatched_elem in unmatched_meas_elems:
                try:
                    data_out['Stain Name'].append('"' + unmatched_elem.attrib['name'] + '"')
                except:
                    data_out['Stain Name'].append('""')
                try:
                    data_out['Study Stain ID#'].append('"' + unmatched_elem.attrib['ID'] + '"')
                except:
                    data_out['Study Stain ID#'].append('""')
                for header in exist_properties:
                    data_out[header].append('""')

                for header in exist_measurements:
                    meas_path = exist_measurements[header][0]
                    if len(exist_measurements[header]) == 1:
                        try:
                            data_out[header].append(
                                '"' + root.find(tree.getelementpath(unmatched_elem) + meas_path).text + '"')
                        except:
                            data_out[header].append('""')
                    elif len(exist_measurements[header]) == 2:
                        meas_attr = exist_measurements[header][1]
                        try:
                            data_out[header].append(
                                '"' + root.find(tree.getelementpath(unmatched_elem) + meas_path).attrib[meas_attr] + '"')
                        except:
                            data_out[header].append('""')

        data_out['MCDS-DCL File'] = ['"' + DCL_file + '"']*len(data_out['Sample Name'])
        df_clin_stain = pd.DataFrame(data=data_out)
        clin_stain_filename = 'a_ClinicalStain_' + file_base
        stain_protocol = 'Cell Clinical Stain Characterization'
        for data in data_out:
            data_out[data] = [x.replace('"', '') for x in data_out[data]]
        df_stain = pd.DataFrame(data=data_out)

        params, param_comps = a_header_fix(clin_stain_filename, df_stain, stain_protocol, 3)

        return (clin_stain_filename, stain_protocol, params, param_comps)
    stain_properties = root.findall('.//clinical/diagnosis/pathology/pathology_definitions/stain')
    stain_measurements = root.findall('.//clinical/diagnosis/pathology/stain')
    if (len(stain_measurements) > 0) or (len(stain_properties) > 0):
        results = a_clinical_stain(stain_properties, stain_measurements)
        a_file_list.append(results[0])
        assay_type_list.append('Cell Stains')
        study_prot_list.append(results[1])
        study_prot_types.append('Characterization')
        assay_parameters.append(results[2])
        assay_param_components.append(results[3])

    else:
        pass
        #print('No Clinical Stain Assay')

    #print('Assay file list:', a_file_list)



    s_file_list = []
    phenotype_factors = []
    phenotype_factor_type = []
    def study_write():
        '''

        :return:
        '''
        df_study_in = pd.read_excel(rF'{db}', sheet_name='Study', keep_default_na=False, usecols=
        ['Study ISA Header', 'Study xPath'])
        study_paths = [str(i) for i in df_study_in['Study xPath'].tolist() if i]
        study_headers = [str(i) for i in df_study_in['Study ISA Header'].tolist() if i]
        #Initalize data_out dictionary
        data_out = {'Source Name': []}
        assay_samples = []
        if len(study_paths) != len(study_headers):
            print('Study File - Issue in Excel File')

        #If content exists in xml, write header and content
        #Only 1 row of "content" : can write header then content, then move to next
        phenos = root.findall('cell_line/phenotype_dataset')
        for elem in phenos:
            data_out['Source Name'].append('"' + sample_name_base + '"')
            assay_samples.append('"' + sample_name_base + '.' + elem.attrib['ID'] + '"')
            phenotype_factors.append(elem.attrib['keywords'])
            phenotype_factor_type.append('Cell conditions')
        for path in study_paths:
            if root.find(path) is not None:
                #Write header to dictionary as key with empty list as value
                header = study_headers[study_paths.index(path)]
                data_out[header] = []
                if '@' not in path:
                    data_out[header].extend(('"' + root.find(path).text.strip() + '"') for j in range(len(phenos)))
                else:
                    result = re.split(r"@", path)
                    new_path = result[0].replace('[', '')
                    attr = result[1].replace(']', '')
                    data_out[header].extend(('"' + root.find(path).attrib[attr].strip() + '"') for j in range(len(phenos)))

        #append PKPD drug information from a_s_pkpd if it exists to end of study file, before sample names
        if pkpd_s_data:
            for PKPD in pkpd_s_data:
                data_out[PKPD] = pkpd_s_data[PKPD]
        data_out['Sample Name'] = assay_samples
        study_filename = 's_' + file_base
        study_protocol = 'Digital Cell Line Creation'
        for data in data_out:
            data_out[data] = [x.replace('"', '') for x in data_out[data]]
        df_study = pd.DataFrame(data=data_out)

        params, param_comps = a_header_fix(study_filename, df_study, study_protocol, 1)

        return (study_filename, study_protocol, params, param_comps)

    #call study_write function and append file name to file list
    results = study_write()
    s_file_list.append(results[0])
    study_prot_list.insert(0,results[1])
    study_prot_types.insert(0,'sample collection')
    assay_parameters.insert(0,results[2])
    assay_param_components.insert(0,results[3])

    # I file

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
        #TODO - only accept one separation variable (first used in xlsx cell) to join strings right now
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
                pass
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
        '''

        :param i: Index of xPath
        :return: Writes line to investigation text file
        '''
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
                str_list = [x.strip() for x in df.at[i,'MCDS-DCL Correlate Entity'].split(';') if x]
            elif df.at[i,'MCDS-DCL Correlate X-Path'] == "Script Variable":
                var_in = ISAfromScript[df.at[i,'ISA-Tab Entity'].strip()]
                if type(var_in) == list and type(var_in[0]) == str:
                    str_list = var_in
                elif type(var_in) == str:
                    str_list.append(var_in)
            elif df.at[i,'Multiples for xPath'] == 'Mult-join':
                path = df.at[i, 'MCDS-DCL Correlate X-Path']
                par_path, child = path.rsplit('/',1)
                parnt = root.findall(par_path)
                for par in parnt:
                    par_child = root.findall(tree.getelementpath(par) + '/' + child)
                    join_list = []
                    for elem in par_child:
                        try:
                            join_list.append(elem.text)
                        except:
                            pass
                    if len(join_list) > 0:
                        str_list.append(' ; '.join(join_list))
                    else:
                        str_list.append('""')
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
                                    pass
                                    #print('Attr Does Not Exist')
                            elif 'Multiple' in str(df.at[i,'Multiples for xPath']):
                                mult_list = match_mult(path)
                                for mult_elem in mult_list:
                                    try:
                                       str_list.append(mult_elem.attrib[attr])
                                    except:
                                        str_list.append(I_blank)
                                        #print('Attr Does Not Exist')


                        elif '*' in path:
                            # '*' in xPath signifies that a parent tag is desired content
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
                                    pass
                                    #print('Tag Does Not Exist')
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
                                        #print('Tag Does Not Exist')

                        else:
                            # Default state is finding the text from the element at the specified xPath
                            # Lines below: split input xPath into element xPath and attribute name
                            # Write value of attribute to str_list with appropriate "" if no result

                            if 'Single' in str(df.at[i,'Multiples for xPath']):
                                try:
                                    str_list.append(root.find(path).text.strip().replace('\t', '').replace('   ','').replace('\n', ' ;; '))
                                    break
                                except:
                                    pass
                                    #print('Text Does Not Exist')
                            elif 'Multiple' in str(df.at[i,'Multiples for xPath']):
                                mult_list = match_mult(path)
                                for mult_elem in mult_list:
                                    try:
                                        str_list.append(mult_elem.text.strip().replace('\t', '').replace('   ','').replace('\n', ' ;; '))
                                    except:
                                        str_list.append(I_blank)
                                        #print('Text Does Not Exist')


            if df.at[i,'Multiples for xPath'] == 'Single' and len(str_list) == 0:
                I_str += '""'
            else:
                for match in str_list:
                    if match != '""':
                        I_str += I_sep + '"' + match + '"'
                    else:
                        I_str += I_sep + match
        else:
            I_str += I_sep + '""'

        f_I.write(I_str + '\n')

    I_filename = 'i_' + file_base
    f_I = open(os.path.join(output_folder,I_filename), 'w')

    if root.find('cell_line/metadata/citation/notes') is not None:
        #print("Found")
        mcds_pub = root.find('cell_line/metadata/citation/notes').text
        pub_status = mcds_pub.rsplit('(',1)[1].split(',',1)[1].strip(')').strip()
        pub_title = mcds_pub.split(',',1)[1].split('(',1)[0].strip()
        if '[' in mcds_pub:
            pub_author = mcds_pub.split(',', 1)[0].split(']', 1)[1].strip()
        else:
            pub_author = mcds_pub.split(',', 1)[0].strip()
    else:
        pub_status = ''
        pub_author = ''
        pub_title = ''
    #Set variables found from assay and study for I writing
    ISAfromScript = {'Investigation Publication Author List': pub_author,
                     'Investigation Publication Title': pub_title,
                     'Investigation Publication Status': pub_status,
                     'Study Publication Author List': pub_author,
                     'Study Publication Title': pub_title,
                     'Study Publication Status': pub_status,
                     'Study Factor Name' : phenotype_factors,
                     'Study File Name' : s_file_list,
                     'Study Assay File Name' : a_file_list,
                     'Study Assay Measurement Type' : assay_type_list,
                     'Study Protocol Name' : study_prot_list,
                     'Study Protocol Type' : study_prot_types,
                     'Study Protocol Parameters Name' : assay_parameters,
                     'Study Protocol Components Name' : assay_param_components
                     }

    for ind in df.index:
        if df.at[ind,'ISA File Location'] == 'I':
            #print("I file line: ", ind + 1)
            if df.at[ind,'ISA Entity Type'] == 'Header':
                f_I.write(str(df.at[ind,'ISA-Tab Entity']).strip().upper() + '\n')
            elif df.at[ind,'ISA Entity Type'] == 'Data':
                f_I.write(str(df.at[ind,'ISA-Tab Entity']).strip())
                mcds_match(ind)


        #If type is I file, then write newline with I file. If header, write in all caps and go to next line. If type data,
        # write then /t, parse through xml with correlate xpath. If no data exists, "" then /n. If data exists, write in file. Continue for all x paths.
        # After doing for all xpaths in list, /n
    f_I.close()


    #Make fixes for multiple blanks, joining roles of repeated study contacts, and removing unused comments in I file

    def fix_multi_blanks():
        '''
        :param
        :return: Modified input file with correct number of quotes for ISA entities with no associated xPath,
                based on number of entities on a separate line in the file
        '''
        f_I = open(os.path.join(output_folder,I_filename), 'r')
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
                            file_data[line_num] = edit_line + quote_str + '\n'
        f_I = open(os.path.join(output_folder,I_filename), 'w')
        f_I.writelines(file_data)
        f_I.close()

    fix_multi_blanks()


    def fix_study_contacts():
        f_I = open(os.path.join(output_folder,I_filename), 'r')
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
        #set ISA headers as column labels
        headers = df_s.iloc[0]
        df_s = df_s[1:]
        df_s.columns = headers
        #If the study person first name contains a middle initial in the form of "Samuel H" or "Samuel H.",
        #seprate the first name and middle initial and write to their respective ISA labels
        #Does not currently accept two middle initials or two first names
        for idx in df_s.index:
            first_middle = df_s.at[idx,'Study Person First Name'].strip('"').strip('.').split(' ')
            if len(first_middle) == 2:
                if len(first_middle[1]) == 1:
                    df_s.at[idx, 'Study Person First Name'] = '"' + first_middle[0] + '"'
                    df_s.at[idx, 'Study Person Mid Initials'] = '"' + first_middle[1] + '."'

        #Searched for duplicate rows based on Last name and First name columns
        #Return list of indices of duplicate rows
        for (index,dup) in enumerate(df_s.duplicated(subset = ['Study Person Last Name','Study Person First Name'], keep='first')):
            if dup:
                dup_ind_list.append(index+1)
        #Get string from dup, find row which it is a duplicate of, go to row, append role to first occurance
        for j in dup_ind_list:
            last = df_s.at[j,'Study Person Last Name']
            first = df_s.at[j,'Study Person First Name']
            first_ind = df_s[(df_s['Study Person Last Name'] == last) & (df_s['Study Person First Name'] == first)].index[0]
            role = str(df_s.at[first_ind,'Study Person Roles']).strip('"')
            new_role = str(df_s.at[j,'Study Person Roles']).strip('"')
            df_s.at[first_ind,'Study Person Roles'] = '"' + role + ';' + new_role + '"'

        #drop duplicate rows, transpose data to match ISA format, write to list including index labels
        df_s = df_s.drop(dup_ind_list).transpose()
        col_list = df_s.reset_index().values.tolist()
        updated_contact_list = []
        for (j,items) in enumerate(col_list):
            temp_str = []
            for k in range(len(items)):
                 if k == 0:
                     temp_str.append(items[k])
                 elif k == len(items) - 1:
                     temp_str.append(items[k] + '\n')
                 else:
                     temp_str.append(items[k])
            updated_contact_list.append('\t'.join(temp_str))

        for z in range(len(updated_contact_list)):
            file_data[line_nums[z]] = updated_contact_list[z]
        f_I = open(os.path.join(output_folder,I_filename), 'w')
        f_I.writelines(file_data)
        f_I.close()

    fix_study_contacts()

    def remove_I_empty_comment():
        '''
        :param
        :return: None
        '''
        f_I = open(os.path.join(output_folder, I_filename), 'r')
        file_data = f_I.readlines()
        f_I.seek(0)
        lines_to_remove = []
        for line in file_data:
            if 'Comment[' in line:
                line_content = line.split(']',1)
                if not line_content[1].replace('\n','').replace('\t','').replace('"','').strip():
                   lines_to_remove.append(line)
        file_data = [x for x in file_data if x not in lines_to_remove]
        f_I = open(os.path.join(output_folder, I_filename), 'w')
        f_I.writelines(file_data)
        f_I.close()

    remove_I_empty_comment()
