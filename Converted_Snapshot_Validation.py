'''Script to validate a set of converted MCDS-DSS .xml files and compare them to the original file
Input:
  Folder containing converted DSS.xml files
  Folder containing original DSS.xml files
Output:
  1 .xlsx file:
   Converted_DSS_eval.xlsx
Author: Corey Chitwood
Date:
  v0.1 - July 2021
'''
import os
import sys
from tqdm import tqdm
from lxml import etree
import xmlschema
import pandas as pd


os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))
cwd = os.getcwd()
conv_DSS_folder = os.path.join(cwd, 'MCDS Conversion Output')
conv_DSS_dir = os.listdir(conv_DSS_folder)

orig_DSS_folder = os.path.join(cwd, 'All_Digital_Snapshots')
orig_DSS_dir = os.listdir(orig_DSS_folder)

parser = etree.XMLParser(remove_comments=True)

schema_folder_path = os.path.join(cwd, 'MultiCellDS-transitions-v1.0-v1.0.0', 'v1.0', 'v1.0.0')
schema_file_path = os.path.join(schema_folder_path, 'MultiCellDS.xsd')
try:
    schema = xmlschema.XMLSchema(schema_file_path)
except:
    # TODO update schema link to master branch once transitions update is pushed in GitLab
    sys.exit(f"\n\033[1;31;40mError: Could not find Schema .xsd files for MCDS validation\n"
             f"MCDS Schema files can be downloaded from https://gitlab.com/MultiCellDS/MultiCellDS/-/tree/transitions/v1.0/v1.0.0\n"
             f"Download directory as zip and extract all to 'ISA to MCDS' folder\n"
             f"If issue persists, check that schema_folder_path matches the location of the local folder containing the MultiCellDS.xsd file")

ErrorCount_dict = {'DSS Filename': [], 'Passed MCDS Validation': [], 'Total Data Entities in Original File': [],
                   'Total Data Entities in Converted File': [], 'Entitity Count Equal?': [],
                   'Num of Issues in Converted File': []}
BadLines_dict = {'DSS Filename': [], 'Entity with issue': [], 'Original File Location': [],
                 'Converted File Location': [], 'Issue': []}





eval_list = conv_DSS_dir[:]




for conv_DSS_file in tqdm(eval_list,
                          desc='Validating converted MCDS DSS file via MCDS schema and evaluating vs original MCDS DSS file',
                          total=len(eval_list), mininterval=1):
    mcds_base = conv_DSS_file.split('_converted')[0]
    orig_file_name = mcds_base + '.xml'
    # If there is no associated original MCDS-DSS found
    if orig_file_name not in orig_DSS_dir:
        print(orig_file_name, ' not found')

    full_orig_path = os.path.join(orig_DSS_folder, orig_file_name)
    full_conv_path = os.path.join(conv_DSS_folder, conv_DSS_file)
    orig_tree = etree.parse(full_orig_path, parser=parser)
    conv_tree = etree.parse(full_conv_path, parser=parser)
    orig_root = orig_tree.getroot()
    conv_root = conv_tree.getroot()

    orig_text = []
    orig_attrib = []
    orig_tags = []

    conv_text = []
    conv_attrib = []
    conv_tags = []



    def validate_DSS():
        valid = schema.is_valid(full_conv_path)
        ErrorCount_dict['DSS Filename'].append(mcds_base)
        ErrorCount_dict['Passed MCDS Validation'].append(valid)


    def compare_num_entities():
        conv_ent_count = 0
        orig_ent_count = 0
        conv_ent_count += (len(conv_root.attrib))
        orig_ent_count += (len(orig_root.attrib))
        for child in orig_root.iter():
            orig_ent_count += 1
            orig_ent_count += len(child.attrib)
            if (child.text) == str:
                if len(child.text) > 0:
                    orig_ent_count += 1
        for child in conv_root.iter():
            conv_ent_count += 1
            conv_ent_count += len(child.attrib)
            if child.text == str:
                if len(child.text) > 0:
                    conv_ent_count += 1
        ErrorCount_dict['Total Data Entities in Original File'].append(orig_ent_count)
        ErrorCount_dict['Total Data Entities in Converted File'].append(conv_ent_count)
        if orig_ent_count == conv_ent_count:
            ErrorCount_dict['Entitity Count Equal?'].append('yes')
        else:
            ErrorCount_dict['Entitity Count Equal?'].append('no')


    def compare_tags_data_and_attributes():
        for child in orig_root.iter():
            orig_text.append(child)
            orig_attrib.append(child)
            orig_tags.append(child.tag)
        for child in conv_root.iter():
            conv_text.append(child)
            conv_attrib.append(child)
            conv_tags.append(child.tag)

        if len(orig_tags) != len(conv_tags):
            for i in range(len(min(orig_tags, conv_tags))):
                if orig_tags[i] != conv_tags[i]:
                    BadLines_dict['DSS Filename'].append(mcds_base)
                    BadLines_dict['Issue'].append('Number of tags do not match')
                    BadLines_dict['Entity with issue'].append(
                        'Issue with tag following' + orig_tags[i - 1] + 'in orig file')
                    BadLines_dict['Converted File Location'].append('')
                    BadLines_dict['Original File Location'].append('')
        for i in range(len(min(orig_tags, conv_tags))):
            if orig_tags[i] != conv_tags[i]:
                BadLines_dict['DSS Filename'].append(mcds_base)
                BadLines_dict['Issue'].append('Name of tags do not match')
                BadLines_dict['Original File Location'].append(orig_tree.getpath(orig_tags[i]))
                BadLines_dict['Converted File Location'].append(conv_tree.getpath(conv_tags[i]))
                BadLines_dict['Entity with issue'].append(
                    'Issue with tag following ' + orig_tags[i - 1] + ' in orig or ' + conv_tags[i - 1] + ' in conv')
                break

        for i in range(len(orig_text)):
            if orig_text[i].text != conv_text[i].text:
                BadLines_dict['DSS Filename'].append(mcds_base)
                BadLines_dict['Issue'].append('Entity Text Does Not Match')
                BadLines_dict['Original File Location'].append(orig_tree.getpath(orig_text[i]))
                BadLines_dict['Converted File Location'].append(conv_tree.getpath(conv_text[i]))
                BadLines_dict['Entity with issue'].append(orig_text[i].tag)

        for i in range(len(orig_attrib)):
            if orig_attrib[i].attrib != conv_attrib[i].attrib:
                orig_attrib_keys = orig_attrib[i].keys()
                conv_attrib_keys = conv_attrib[i].keys()
                try:
                    for j in range(len(orig_attrib_keys)):
                        orig_attr = orig_attrib_keys[j]
                        conv_attr = conv_attrib_keys[j]
                        orig_attr_data = orig_attrib[i].get(orig_attr)
                        conv_attr_data = conv_attrib[i].get(conv_attr)
                        if orig_attr_data != conv_attr_data:
                            BadLines_dict['Issue'].append('Attribute data does not match')
                            BadLines_dict['Entity with issue'].append(str(orig_attrib[i]) + (orig_attr[j]))
                            BadLines_dict['Original File Location'].append(orig_tree.getpath(orig_attrib[i]))
                            BadLines_dict['Converted File Location'].append(conv_tree.getpath(conv_attrib[i]))
                            BadLines_dict['DSS Filename'].append(mcds_base)


                except:
                    BadLines_dict['Issue'].append('Element is missing an attribute')
                    BadLines_dict['Entity with issue'].append(orig_attrib[i].tag)
                    BadLines_dict['Original File Location'].append(orig_tree.getpath(orig_attrib[i]))
                    BadLines_dict['Converted File Location'].append(conv_tree.getpath(conv_attrib[i]))
                    BadLines_dict['DSS Filename'].append(mcds_base)

    def count_errors_in_each_file():
        errors = 0
        for elm in BadLines_dict['DSS Filename']:
            if elm == mcds_base:
                errors += 1
        ErrorCount_dict['Num of Issues in Converted File'].append(errors)


    def write_to_excel_file():
        writer = pd.ExcelWriter('Converted_DSS_Eval.xlsx', engine='xlsxwriter')

        df1 = pd.DataFrame(data=ErrorCount_dict)
        df2 = pd.DataFrame(data=BadLines_dict)

        df1.to_excel(writer, sheet_name='Overview')
        df2.to_excel(writer, sheet_name='Specific Issues')
        writer.save()



    validate_DSS()
    compare_num_entities()
    compare_tags_data_and_attributes()
    count_errors_in_each_file()
    write_to_excel_file()
