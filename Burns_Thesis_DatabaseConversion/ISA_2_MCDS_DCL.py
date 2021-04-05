
#Author - Connor Burns
#v0.1 - April 2021

import os
from lxml import etree
import shutil
import copy
import pandas as pd

cwd = os.getcwd()
DCL_xml_dir = os.path.join(cwd,'ISA to MCDS')

DCL_list = [os.path.join(DCL_xml_dir,DCL) for DCL in os.listdir(DCL_xml_dir)]

parser = etree.XMLParser(remove_comments=True)

# Parse XML tree and remove comments
i = 1
'''
# Loop through all XML files in All_Digital_Cell_Lines folder, get tag + xPath of each element, classify element
for XML_FileName in DCL_list[2:-1]:
    tree = etree.parse(os.path.join(DCL_xml_dir, XML_FileName), parser=parser)
    root = tree.getroot()
    root.text = None
    for attr in root.keys():
        root.attrib[attr] = ""
    for child in root.iter():
        child.text = None
        for attr in child.keys():
            child.attrib[attr] = ""
    tree.write(os.path.join(DCL_xml_dir,str(i) + "_clear.xml"))
    i+= 1
'''
#
new_DCL = os.path.join(DCL_xml_dir,"newDCL.xml")

tree = etree.parse(new_DCL, parser=parser)
root = tree.getroot()
root.set('type',"cell_line")
root.set('version', "1.0.0")

ISA_inputs = os.path.join(cwd,'ISATabOutput')
ISA_file_base = os.listdir(ISA_inputs)[os.listdir(ISA_inputs).index('MCDS_L_0000000240')]
print('MCDS File: ', ISA_file_base)
ISA_file_folder = os.path.join(ISA_inputs,ISA_file_base)
I_filename = os.path.join(ISA_file_folder, 'i_' + ISA_file_base + '.txt')
f_I = open(I_filename, 'r')
#Make dictionaries of sections with ISA entity as key and text as list?
I_data = {}

#Issue importing as dataframe. Read lines and add lines with content to dictionary with ISA entity as dictionary key
#and list of text that has been separated by tab. Do not include section headers (ex. INVESTIGATION) or lines that
#only have blank comment (ex. Investigation Submission Date     ""  )
for line in f_I.readlines():
    line = line.replace('\n','')
    line_list = [x for x in line.split('\t') if x]
    if len(line_list) > 1:
        line_content = [x.replace('"','') for x in line_list[1:]]
        if len([x for x in line_content if x]) > 0:
            I_data[line_list[0]] = [x.replace('"','') for x in line_list[1:]]

all_assay_paths = ['cell_line/phenotype_dataset/phenotype/cell_cycle',
                   'cell_line/phenotype_dataset/phenotype/cell_death',
                   'cell_line/metadata/custom/clinical/diagnosis/pathology/pathology_definitions/stain',
                   'cell_line/metadata/custom/clinical/diagnosis/pathology/stain',
                   'cell_line/phenotype_dataset/phenotype/geometrical_properties',
                    'cell_line/phenotype_dataset/cell_part/phenotype/geometrical_properties',
                    'cell_line/phenotype_dataset/cell_part/cell_part/phenotype/geometrical_properties',
                    'cell_line/phenotype_dataset/phenotype/mechanics',
                    'cell_line/phenotype_dataset/cell_part/phenotype/mechanics',
                    'cell_line/phenotype_dataset/cell_part/cell_part/phenotype/mechanics',
                    'cell_line/phenotype_dataset/microenvironment',
                    'cell_line/phenotype_dataset/phenotype/motility',
                    'cell_line/phenotype_dataset/phenotype/PKPD/pharmacodynamics',
                    'cell_line/transitions',
                    'cell_line/phenotype_dataset/phenotype/transport_processes']
exist_assay_path = []


#default is first match
#TODO - remove except clause? Throw error instead if there is no match (need to update xml template)

def write_by_xPath(xPath, value):
    if '@' not in xPath:
        try:
            root.find(xPath).text = value
        except:
            print('no element at ', xPath)
    else:
        elem_path = xPath.split('[')[0]
        attr = xPath.split('@')[1].strip(']')
        try:
            root.find(elem_path).set(attr, value)
        except:
            print('no attrib at ', xPath)

def remove_elem(path):
    '''
    :param path: xPath (without the root) of the element to get rid of from the ElementTree.
                All instances of the element and all children of the elements will be deleted as well
    :return: Element and children are removed from tree
    '''
    del_elem_list = root.findall(path)
    for elem in del_elem_list:
        elem.getparent().remove(elem)
#Copy elem function - no issues with 1 input, will return list regardless of one or more elements

def copy_elem(elem_path,num_elems):
    '''
    :param elem_path: The xPath of the element to be copied
    :param num_elems: The total number of elements that should exist in the xml file
    :return: A list of xPaths for the elements (original + copies)
    '''
    for i in range(num_elems - 1):
        og_elem = root.find(elem_path)
        new_elem = copy.deepcopy(og_elem)
        #find index of original element then use to insert the copy after the last occurance of the element
        og_index = og_elem.getparent().getchildren().index(og_elem)
        og_elem.getparent().insert(og_index + 1 + i, new_elem)
    return(root.findall(elem_path))

def splitDataFrameList(df, target_column, separator):
    ''' df = dataframe to split,
    target_column = the column containing the values to split
    separator = the symbol used to perform the split
    returns: a dataframe with each entry for the target column separated, with each element moved into a new row.
    The values in the other columns are duplicated across the newly divided rows.
    '''
    row_accumulator = []
    def splitListToRows(row, separator):
        split_row = row[target_column].split(separator)
        for s in split_row:
            new_row = row.to_dict()
            new_row[target_column] = s
            row_accumulator.append(new_row)

    df.apply(splitListToRows, axis=1, args=(separator,))
    new_df = pd.DataFrame(row_accumulator)
    return new_df


    new_rows = []
    df.apply(splitListToRows, axis=1, args=(new_rows, target_column, separator))
    new_df = pd.DataFrame(new_rows)
    return new_df

#Import all assay files as pandas dataframes. If the assay does not exist, remove its elements from the element tree
#TODO - Add adding of additional things here? Might be easier to supply now (will have extras for phenotype datasets)

for a_file in I_data['Study Assay File Name']:
    if "CellCycle" in a_file:
        cellcycle_df = pd.read_csv(os.path.join(ISA_file_folder, a_file), sep='\t')
        exist_assay_path.append('cell_line/phenotype_dataset/phenotype/cell_cycle')
    elif "CellDeath" in a_file:
        celldeath_df = pd.read_csv(os.path.join(ISA_file_folder, a_file), sep='\t')
        exist_assay_path.append('cell_line/phenotype_dataset/phenotype/cell_death')
    elif "ClinicalStain" in a_file:
        clinstain_df = pd.read_csv(os.path.join(ISA_file_folder, a_file), sep='\t')
        exist_assay_path.append('cell_line/metadata/custom/clinical/diagnosis/pathology/pathology_definitions/stain')
        exist_assay_path.append('cell_line/metadata/custom/clinical/diagnosis/pathology/stain')
    elif "GeometricalProperties" in a_file:
        geoprops_df = pd.read_csv(os.path.join(ISA_file_folder, a_file), sep='\t')
        exist_assay_path.append('cell_line/phenotype_dataset/phenotype/geometrical_properties')
        exist_assay_path.append('cell_line/phenotype_dataset/cell_part/phenotype/geometrical_properties')
        exist_assay_path.append('cell_line/phenotype_dataset/cell_part/cell_part/phenotype/geometrical_properties')
    elif "Mechanics" in a_file:
        mechanics_df = pd.read_csv(os.path.join(ISA_file_folder, a_file), sep='\t')
        exist_assay_path.append('cell_line/phenotype_dataset/phenotype/mechanics')
        exist_assay_path.append('cell_line/phenotype_dataset/cell_part/phenotype/mechanics')
        exist_assay_path.append('cell_line/phenotype_dataset/cell_part/cell_part/phenotype/mechanics')
    elif "Microenvironment" in a_file:
        micro_df = pd.read_csv(os.path.join(ISA_file_folder, a_file), sep='\t')
        exist_assay_path.append('cell_line/phenotype_dataset/microenvironment')
    elif "Motility" in a_file:
        motility_df = pd.read_csv(os.path.join(ISA_file_folder, a_file), sep='\t')
        exist_assay_path.append('cell_line/phenotype_dataset/phenotype/motility')
    elif "PKPD" in a_file:
        PKPD_df = pd.read_csv(os.path.join(ISA_file_folder, a_file), sep='\t')
        exist_assay_path.append('cell_line/phenotype_dataset/phenotype/PKPD/pharmacodynamics')
    elif "StateTransition" in a_file:
        statetrans_df = pd.read_csv(os.path.join(ISA_file_folder, a_file), sep='\t')
        exist_assay_path.append('cell_line/transitions')
    elif "TransportProcesses" in a_file:
        transport_df = pd.read_csv(os.path.join(ISA_file_folder, a_file), sep='\t')
        exist_assay_path.append('cell_line/phenotype_dataset/phenotype/transport_processes')

no_assay_path = [x for x in all_assay_paths if x not in exist_assay_path]
for path in no_assay_path:
    remove_elem(path)
#Study df na_filter = False: there is an instance in MCDS#003 where Morphology.text = 'N/A' literal
study_name = I_data['Study File Name'][0]
study_df = pd.read_csv(os.path.join(ISA_file_folder,study_name), sep='\t', na_filter = False)
study_singles_df = study_df.copy(deep=True).drop(['Source Name', 'Protocol REF', 'Cell Line Label', 'MultiCellDB Name','Sample Name'], axis = 1)

#Write basic cell line information from study file to
cell_line_ID = study_df['Source Name'][0].rsplit('.',1)[1]
write_by_xPath('cell_line[@ID]',cell_line_ID)
cell_line_label = study_df['Cell Line Label'][0]
write_by_xPath('cell_line[@label]',cell_line_label)
mcdb_name = study_df['MultiCellDB Name'][0]
write_by_xPath('cell_line/metadata/MultiCellDB/name',mcdb_name)
mcdb_ID = study_df['Source Name'][0].rsplit('.',1)[0]
write_by_xPath('cell_line/metadata/MultiCellDB/ID',mcdb_ID)
phenodataset_IDs = [x.rsplit('.',1)[1] for x in study_df['Sample Name']]

print('Phenotype IDs: ', phenodataset_IDs)

pheno_list = copy_elem('cell_line/phenotype_dataset',len(phenodataset_IDs))
for i, elem in enumerate(pheno_list):
    elem.set('ID',phenodataset_IDs[i])
    elem.set('keywords', I_data['Study Factor Name'][i])

db = 'ISA_MCDS_Relationships_Py_CB.xlsx'

#Study relationships are one to one, with the same content repeated for each sample in the study ISA file
#Import relationship study dataframe, import PKPD study dataframe, transpose and append to study dataframe
#Loop through columns in ISA study dataframe (sample name etc. removed), get data value to write
#Find associated df index in the relationship file, get xPath, then write value to file at xPath

rel_df_study = pd.read_excel(rF'{db}', sheet_name='Study', usecols=['Study ISA Header', 'Study xPath']).dropna()
rel_df_pkpd = pd.read_excel(rF'{db}', sheet_name='A_S_PKPD', usecols=['PKPD Drug ISA Headers', 'PKPD Drug Attributes']).dropna()
def mod_pkpd_string(pkpd_path):
    return 'cell_line/phenotype_dataset/phenotype/PKPD/drug[@' + str(pkpd_path) + ']'
rel_df_pkpd['PKPD Drug Attributes'] = rel_df_pkpd['PKPD Drug Attributes'].apply(mod_pkpd_string)
rel_df_pkpd.columns = ['Study ISA Header', 'Study xPath']

#Create full xPath from PKPD xlsx data, change column names to match study df, concatenate
rel_df_study = pd.concat([rel_df_study,rel_df_pkpd],axis = 0,ignore_index=True)

#fix numbering in rel df for units
unit_cnt = 0
for j,head in enumerate(rel_df_study['Study ISA Header']):
    if 'Units' in head:
        if unit_cnt > 0:
            rel_df_study.at[j,'Study ISA Header'] = str(head) + F'.{unit_cnt}'
        unit_cnt += 1

for header in study_singles_df.columns:
    val_to_write = str(study_singles_df[header][0])
    rel_ind = rel_df_study[rel_df_study['Study ISA Header'] == header].index.tolist()[0]
    val_path = str(rel_df_study.at[rel_ind,'Study xPath'])
    write_by_xPath(val_path, val_to_write)

#Import relationship xlsx I sheet, remove rows which have a blank (if xPath is blank)

rel_df_inv = pd.read_excel(rF'{db}', sheet_name='MCDS-DCL to ISA-Tab', usecols=['ISA-Tab Entity',
                                'MCDS-DCL Correlate X-Path','Multiples for xPath']).dropna()
pd.set_option("display.max_rows", None, "display.max_columns", None)
#remove rows without non xPath entry in correlate xPath column
rel_df_inv = rel_df_inv.loc[rel_df_inv['MCDS-DCL Correlate X-Path'].str.contains('/')]

#remove df rows with anything but singles in 'multiples' column, xPaths with '*' (parent tag), and Investigation Person
# in header (will add to file with study contacts)
rel_I_single = rel_df_inv.loc[(rel_df_inv['Multiples for xPath'].str.contains('Single')) &
                            (~rel_df_inv['MCDS-DCL Correlate X-Path'].str.contains('\*')) &
                              (~rel_df_inv['ISA-Tab Entity'].str.contains('Investigation Person'))]
#Write data from ISA I file for attribute and text data that is single but not Investigation Person
for header in I_data:
    if header in rel_I_single['ISA-Tab Entity'].values:
        rel_ind = rel_I_single['ISA-Tab Entity'][rel_I_single['ISA-Tab Entity'] == header].index[0]
        val_path = str(rel_I_single.at[rel_ind,'MCDS-DCL Correlate X-Path'])
        val_to_write = I_data[header][0].strip()
        write_by_xPath(val_path,val_to_write)

#Investigation file multiples
#Make dictionary for data origins elements. If content in dictionary, check max length of dictionary values.
#If URLs are separated by ; they belong under same parent data_origins/citation: if any ';' , copy URL elem
#If length >1, make max(len) - 1 copies of the data origins element
#All I_data values are lists, even if length is one: can check length of value to see number of elements needed
#Loop through found data_orig elements, write data to file

#Data Origins
data_orig_dict = {}
for key in I_data.keys():
    if 'Data Origin' in key:
        data_orig_dict[key] = I_data[key]
if len(data_orig_dict) > 0:
    if 'Comment[Data Origins URL]' in data_orig_dict.keys():
        if any(';' in url for url in data_orig_dict['Comment[Data Origins URL]']):
            URL_elems = copy_elem('cell_line/metadata/data_origins/data_origin/citation/URL', 2)
            URL_path_tail = [tree.getelementpath(x).rsplit('citation')[1] for x in URL_elems]

    num_data_orig_elem = len(max(data_orig_dict.values()))
    data_orig_elems = copy_elem('cell_line/metadata/data_origins/data_origin',num_data_orig_elem)
    rel_data_origin = rel_df_inv.loc[(rel_df_inv['ISA-Tab Entity'].str.contains('Data Origin'))]
    for dict_ind, elem in enumerate(data_orig_elems):
        orig_path = tree.getelementpath(elem)
        for header in data_orig_dict:
            #Check to see if index in elem
            #If data origins URL is the header and citations are joined under one parent, split and write to
            #separate URL elements for the same citation parent
            if dict_ind < len(data_orig_dict[header]):
                if 'Comment[Data Origins URL]' in header:
                    if ';' in data_orig_dict[header][dict_ind]:
                        split_url = data_orig_dict[header][dict_ind].split(';')
                        for j,url in enumerate(split_url):
                            write_by_xPath((orig_path + '/citation' +  URL_path_tail[j]), url.strip())
                    else:

                        write_by_xPath((orig_path + '/citation' + '/URL'),data_orig_dict[header][dict_ind].strip())
                else:
                    rel_ind = rel_data_origin['ISA-Tab Entity'][rel_data_origin['ISA-Tab Entity'] == header].index[0]
                    val_path = str(rel_data_origin.at[rel_ind, 'MCDS-DCL Correlate X-Path'])
                    val_path = orig_path + val_path.rsplit('data_origin',1)[1]
                    val_to_write = data_orig_dict[header][dict_ind]
                    write_by_xPath(val_path,val_to_write)

#Data Analysis
#Operates very similarly to Data Origins loop (see above)
data_analy_dict = {}
for key in I_data.keys():
    if 'Data Analysis' in key:
        data_analy_dict[key] = I_data[key]
if len(data_analy_dict) > 0:
    if 'Comment[Data Analysis - citation URL]' in data_analy_dict.keys():
        if any(';' in url for url in data_analy_dict['Comment[Data Analysis - citation URL]']):
            URL_elems = copy_elem('cell_line/metadata/data_analysis/citation/URL', 2)
            URL_path_tail = [tree.getelementpath(x).rsplit('citation')[1] for x in URL_elems]
    num_data_analy_elem = len(max(data_analy_dict.values()))
    data_analy_elems = copy_elem('cell_line/metadata/data_analysis/citation', num_data_analy_elem)
    rel_data_analy = rel_df_inv.loc[(rel_df_inv['ISA-Tab Entity'].str.contains('Data Analysis'))]
    #loop through elements found
    for dict_ind, elem in enumerate(data_analy_elems):
        cit_elem_path = tree.getelementpath(elem)
        for header in data_analy_dict:
            #Check to see if index in elem
            #If data analysis citation is the header and citations are joined under one parent, split and write to
            #separate URL elements for the same citation parent
            if dict_ind < len(data_analy_dict[header]):
                if '[Data Analysis - citation URL]' in header:
                    if ';' in data_analy_dict[header][dict_ind]:
                        split_url = data_analy_dict[header][dict_ind].split(';')
                        for j,url in enumerate(split_url):
                            write_by_xPath((cit_elem_path + URL_path_tail[j]), url.strip())
                    else:
                        write_by_xPath((cit_elem_path + '/URL'),data_analy_dict[header][dict_ind].strip())
                else:
                    rel_ind = rel_data_analy['ISA-Tab Entity'][rel_data_analy['ISA-Tab Entity'] == header].index[0]
                    val_path = str(rel_data_analy.at[rel_ind, 'MCDS-DCL Correlate X-Path'])
                    if 'citation' in val_path:
                        val_path = cit_elem_path + '/' + val_path.rsplit('/',1)[1]
                    val_to_write = data_analy_dict[header][dict_ind]
                    write_by_xPath(val_path,val_to_write)


#Study Contacts
#For contacts with multiple rows: split
contact_dict = {}
for key in I_data.keys():
    if 'Study Person' in key:
        contact_dict[key] = I_data[key]
if len(contact_dict) > 0:
    pretty_role_match = {'Current Contact': 'current_contact',
                         'Curator': 'curator',
                         'Creator':'creator' ,
                         'Last Modified By': 'last_modified_by'}
    contact_elems = {}
    df_contacts = pd.DataFrame(data = contact_dict)
    #sort roles alphabetically
    df_contacts = splitDataFrameList(df_contacts,'Study Person Roles',';').sort_values(by='Study Person Roles')
    #combine first and middle initials from I file to create given-names equivalent then drop mid initials from dataframe
    df_contacts['Study Person First Name'] = df_contacts['Study Person First Name'] + ' ' + df_contacts['Study Person Mid Initials']
    df_contacts.drop(labels = 'Study Person Mid Initials', axis = 1, inplace=True)
    rel_contacts_df = rel_df_inv.loc[(rel_df_inv['ISA-Tab Entity'].str.contains('Study Person'))]
    #if role occurs more than once, count occurances, copy the orcid ID element for the role, save elements
    contact_role_series = df_contacts['Study Person Roles'].value_counts()
    for role in pretty_role_match:
        if contact_role_series[role] > 1:
            elem_path = ('cell_line/metadata/curation/' + pretty_role_match[role] + '/orcid-identifier')
            role_list = copy_elem(elem_path , contact_role_series[role])
            contact_elems[role] = [tree.getelementpath(x) for x in role_list]
        else:
            contact_elems[role] = ['cell_line/metadata/curation/' + pretty_role_match[role] + '/orcid-identifier']

    #loop through roles, divide df_contacts by role, loop through rows of contact data and write to element for each row
    for role in contact_elems:
        role_df = df_contacts[df_contacts['Study Person Roles'] == role]
        role_df = role_df.reset_index(drop = True)
        #drop roles column - already separated, only dictates element to write to not data to write
        #will throw error otherwise
        role_df.drop(labels = 'Study Person Roles', axis = 1, inplace = True)
        for row_ind in role_df.index:
            base_path = contact_elems[role][row_ind]
            for col in role_df.columns:
                rel_ind = rel_contacts_df['ISA-Tab Entity'][rel_contacts_df['ISA-Tab Entity'] == col].index[0]
                all_paths = str(rel_contacts_df.at[rel_ind, 'MCDS-DCL Correlate X-Path'])
                #get only the end of the last path in the list (i.e. family-names)
                single_path = all_paths.split(',',1)[0]
                if '"' not in single_path:
                    path_tail = single_path.rsplit('/',1)[1]
                    val_path = base_path + '/' + path_tail
                    val_to_write = str(role_df.at[row_ind,col])
                    write_by_xPath(val_path, val_to_write)
                else:
                    cat_paths = single_path.split('"')
                    org_tail = cat_paths[0].rsplit('/',1)[1]
                    sep_var = cat_paths[1]
                    dept_tail = cat_paths[2].rsplit('/', 1)[1]
                    org_dept_str = str(role_df.at[row_ind,col])
                    if sep_var in org_dept_str:
                        org_name = org_dept_str.split(sep_var)[0]
                        dept_name = org_dept_str.split(sep_var)[1]
                        write_by_xPath((base_path + '/' + org_tail), org_name)
                        write_by_xPath((base_path + '/' + dept_tail), dept_name)
                    else:
                        org_name = org_dept_str
                        write_by_xPath((base_path + '/' + org_tail), org_name)
                # val_path = base_path + '/' + path_tail
                # print(val_path)
                # val_to_write = str(role_df.at[row_ind,col])
                # print(val_to_write)
                #write_by_xPath(val_path, val_to_write)

# if '"' in val_path:
#     paths = val_path.split('"')[::2]
#     sep_char = val_path.split('"')[1::2]
#     for
# for regular entities
#If statement for *, "-"

# Doesn't work properly
# def copy_elem(copy_xPath):
#     elem = root.find(copy_xPath)
#     print('Pre ', tree.getelementpath(elem))
#     new_elem = copy.deepcopy(elem)
#     etree.SubElement( elem.getparent().insert(new_elem)
#     print('New ', tree.getelementpath(new_elem))
#     print('Old ', tree.getelementpath(elem))
#     return (tree.getelementpath(new_elem))



#TODO - complaint: copying and writing information in same loop doesn't work (original is added to end of element tree section)
#TODO - complain: xml copying writes content in correct place, but outdented


#For loop for s file elements (will miss PKPD stuff)
#For loop for I file elements (only for single and direct (can concat be built in?))
#Will probably need to use pd dataframe for study contacts



tree.write(os.path.join(DCL_xml_dir, 'MCDS Conversion Output',ISA_file_base + '_converted.xml'))



#Import blank xml
#save copy as MCDS_DCL_test.xml
#Import relationship xlsx
#Import ISA files from folder
#make into PD dataframes
#Determine existence of sections under phenotype dataset: if not there, delete
#Look in S file to see all samples, copy phenotype datasets, write ID# attributes to each
#Open micrenvironment assay, find names of variables
