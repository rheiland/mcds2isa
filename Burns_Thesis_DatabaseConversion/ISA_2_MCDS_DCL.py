
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
'''
# Parse XML tree and remove comments
i = 1
# Loop through all XML files in All_Digital_Cell_Lines folder, get tag + xPath of each element, classify element
for XML_FileName in DCL_list:
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


I_filename = os.path.join(DCL_xml_dir,'ISA Input', 'i_test.txt')
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
#Match dictionary keys to ISA entities in list, write any single measurements with 1 xPath to DCL file
print(I_data)

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
def write_by_xPath(xPath, value):
    if '@' not in xPath:
        root.find(xPath).text = value
    else:
        elem_path = xPath.split('[')[0]
        attr = xPath.split('@')[1].strip(']')
        root.find(elem_path).set(attr, value)

def remove_elem(path):
    '''
    :param path: xPath (without the root) of the element to get rid of from the ElementTree.
                All instances of the element and all children of the elements will be deleted as well
    :return: Element and children are removed from tree
    '''
    del_elem_list = root.findall(path)
    for elem in del_elem_list:
        elem.getparent().remove(elem)

#Import all assay files as pandas dataframes. If the assay does not exist, remove its elements from the element tree
#TODO - Add adding of additional things now
for a_file in I_data['Study Assay File Name']:
    if "CellCycle" in a_file:
        cellcycle_df = pd.read_csv(os.path.join(input_folder ,a_file), sep='\t')
        exist_assay_path.append('cell_line/phenotype_dataset/phenotype/cell_cycle')
    elif "CellDeath" in a_file:
        celldeath_df = pd.read_csv(os.path.join(input folder,a_file), sep='\t')
        exist_assay_path.append('cell_line/phenotype_dataset/phenotype/cell_death')
    elif "ClinicalStain" in a_file:
        clinstain_df = pd.read_csv(os.path.join(DCL_xml_dir, 'ISA Input', a_file), sep='\t')
        exist_assay_path.append('cell_line/metadata/custom/clinical/diagnosis/pathology/pathology_definitions/stain')
        exist_assay_path.append('cell_line/metadata/custom/clinical/diagnosis/pathology/stain')
    elif "GeometricalProperties" in a_file:
        geoprops_df = pd.read_csv(os.path.join(DCL_xml_dir, 'ISA Input', a_file), sep='\t')
        exist_assay_path.append('cell_line/phenotype_dataset/phenotype/geometrical_properties')
        exist_assay_path.append('cell_line/phenotype_dataset/cell_part/phenotype/geometrical_properties')
        exist_assay_path.append('cell_line/phenotype_dataset/cell_part/cell_part/phenotype/geometrical_properties')
    elif "Mechanics" in a_file:
        mechanics_df = pd.read_csv(os.path.join(DCL_xml_dir, 'ISA Input', a_file), sep='\t')
        exist_assay_path.append('cell_line/phenotype_dataset/phenotype/mechanics')
        exist_assay_path.append('cell_line/phenotype_dataset/cell_part/phenotype/mechanics')
        exist_assay_path.append('cell_line/phenotype_dataset/cell_part/cell_part/phenotype/mechanics')
    elif "Microenvironment" in a_file:
        micro_df = pd.read_csv(os.path.join(DCL_xml_dir, 'ISA Input', a_file), sep='\t')
        exist_assay_path.append('cell_line/phenotype_dataset/microenvironment')
    elif "Motility" in a_file:
        motility_df = pd.read_csv(os.path.join(DCL_xml_dir, 'ISA Input', a_file), sep='\t')
        exist_assay_path.append('cell_line/phenotype_dataset/phenotype/motility')
    elif "PKPD" in a_file:
        PKPD_df = pd.read_csv(os.path.join(DCL_xml_dir, 'ISA Input', a_file), sep='\t')
        exist_assay_path.append('cell_line/phenotype_dataset/phenotype/PKPD/pharmacodynamics')
    elif "StateTransition" in a_file:
        statetrans_df = pd.read_csv(os.path.join(DCL_xml_dir, 'ISA Input', a_file), sep='\t')
        exist_assay_path.append('cell_line/transitions')
    elif "TransportProcesses" in a_file:
        transport_df = pd.read_csv(os.path.join(DCL_xml_dir, 'ISA Input', a_file), sep='\t')
        exist_assay_path.append('cell_line/phenotype_dataset/phenotype/transport_processes')

no_assay_path = [x for x in all_assay_paths if x not in exist_assay_path]
for path in no_assay_path:
    remove_elem(path)

study_name = I_data['Study File Name'][0]
study_df = pd.read_csv(os.path.join(DCL_xml_dir,'ISA Input',study_name), sep='\t')
study_singles_df = study_df.copy(deep=True).drop(['Source Name', 'Cell Line Label', 'MultiCellDB Name','Sample Name'], axis = 1)

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

db = 'ISA_MCDS_Relationships_Py_CB.xlsx'
df_rel_study = pd.read_excel(rF'{db}', sheet_name='MCDS-DCL to ISA-Tab', usecols=['ISA-Tab Entity', 'ISA File Location', 'ISA Entity Type',
                                      'MCDS-DCL Correlate Entity', 'MCDS-DCL Correlate X-Path', 'Multiples for xPath'])


#
# def copy_elem(copy_xPath):
#     elem = root.find(copy_xPath)
#     print('Pre ', tree.getelementpath(elem))
#     new_elem = copy.deepcopy(elem)
#     etree.SubElement( elem.getparent().insert(new_elem)
#     print('New ', tree.getelementpath(new_elem))
#     print('Old ', tree.getelementpath(elem))
#     return (tree.getelementpath(new_elem))
print('Phenotype IDs: ', phenodataset_IDs)
for i in range(len(phenodataset_IDs) - 1):
    og_elem = root.find('cell_line/phenotype_dataset')
    new_elem = copy.deepcopy(og_elem)
    og_elem.getparent().append(new_elem)

for i, elem in enumerate(root.findall('cell_line/phenotype_dataset')):
    elem.set('ID',phenodataset_IDs[i])
    elem.set('keywords', I_data['Study Factor Name'][i])

#TODO - complaint: copying and writing information in same loop doesn't work (original is added to end of element tree section)
#TODO - complain: xml copying writes content in correct place, but outdented


#For loop for s file elements (will miss PKPD stuff)
#For loop for I file elements (only for single and direct (can concat be built in?))
#Will probably need to use pd dataframe for study contacts



tree.write(os.path.join(DCL_xml_dir,'Conversion_output.xml'))



#Import blank xml
#save copy as MCDS_DCL_test.xml
#Import relationship xlsx
#Import ISA files from folder
#make into PD dataframes
#Determine existence of sections under phenotype dataset: if not there, delete
#Look in S file to see all samples, copy phenotype datasets, write ID# attributes to each
#Open micrenvironment assay, find names of variables
