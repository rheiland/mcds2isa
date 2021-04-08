'''Script to validate a set of converted MCDS-DCL .xml files and compare them to the original file


Input:
  Folder containing converted DCL.xml files
  Folder containing original DCL.xml files
Output:
  1 .xlsx file:
   Converted_DCL_eval.xlsx

Author: Connor Burns
Date:
  v0.1 - Apr 2021

'''
import os
from lxml import etree
import xmlschema
import pandas as pd
from xmldiff import main as diff_main
from xmldiff import formatting
#Make two sheets in PD dataframe : summary (eval true or false, total elements, num issues (whitespace stuff removed))
#second sheet - issues: write issue type

cwd = os.getcwd()
conv_folder = os.path.join(cwd, 'MCDS Conversion Output')
conv_file_list = os.listdir(conv_folder)
og_DCL_dir = os.path.join(os.path.dirname(os.path.dirname(cwd)), 'All_Digital_Cell_Lines')
og_DCL_list = os.listdir(og_DCL_dir)
parser = etree.XMLParser(remove_comments=True)

#New DCL .xml validation
schema_file_path = os.path.join(os.path.dirname(cwd), 'DCL Validation Schemas', 'MultiCellDS-transitions-v1.0.0','MultiCellDS.xsd')
schema = xmlschema.XMLSchema(schema_file_path)

ErrorCount_dict = {'DCL Filename' : [], 'Passed Validation' : [], 'Total Entities in New File' : [], 'Num of Issues in New File' : []}
BadLines_dict = {'DCL Filename' : [], 'Action Needed': [], 'Issue location and correction' : []}

def clean_closedtags(root):
    '''

    :param root: root element of original xml to remove closed tags
    :return: None
    '''
    num_children_list = []
    level_ind = 0
    while 0 <= level_ind < 15:
        # print('Level: ',level_ind)
        num_children = 0
        for child in root.iter():
            num_children += 1
            if ((type(child.text) != str) or (len(child.text.strip()) == 0)) & (len(child.attrib) == 0) & (
                    len(child) == 0):
                child.getparent().remove(child)
        #print('Children: ', num_children)
        if num_children in num_children_list:
            break
        else:
            num_children_list.append(num_children)
            level_ind += 1

def count_ents(root):
    '''
    :param root: root of new XML to count elements in
    :return:
    '''
    ent_count = 0
    ent_count += (len(root.attrib))
    for child in root.iter():
        ent_count += 1
        ent_count += len(child.attrib)
        if (child.text) == str:
            if len(child.text) > 0:
                ent_count += 1
    return(ent_count)


for conv_DCL_file in conv_file_list:
    mcds_base = conv_DCL_file.split('_converted')[0]
    full_conv_path = os.path.join(conv_folder, conv_DCL_file)
    ErrorCount_dict['DCL Filename'].append(mcds_base)

    #Validate xml file against schema
    valid = schema.is_valid(full_conv_path)
    ErrorCount_dict['Passed Validation'].append(valid)

    conv_tree = etree.parse(full_conv_path, parser=parser)

    diff_form_xml = formatting.XMLFormatter(normalize = formatting.WS_BOTH, pretty_print = True)
    diff_form_txt = formatting.DiffFormatter(normalize = formatting.WS_TAGS, pretty_print = True)

    og_file_name = mcds_base + '.xml'

    #If there is no associated original MCDS-DCL found
    if og_file_name not in og_DCL_list:
        ErrorCount_dict['Total Entities in New File'].append('No original DCL found')
        ErrorCount_dict['Num of Issues in New File'].append('No original DCL found')
    else:
        full_og_path = os.path.join(og_DCL_dir, og_file_name)
        #parse to clean original DCL so that only non-whitespace characters of element text/attribute and location
        #of element are compared

        # parse to remove closed tags
        old_tree = etree.parse(full_og_path, parser=parser)
        old_root = old_tree.getroot()
        clean_closedtags(old_root)
        for child in old_root.iter():
            if type(child.text) == str:
                child.text = child.text.replace('\n', ' ').replace('\t','').strip()

        new_tree = etree.parse(full_conv_path, parser=parser)
        new_root = new_tree.getroot()
        for child in new_root.iter():
            if type(child.text) == str:
                child.text = child.text.replace('\n', ' ').replace('\t','').strip()

        ErrorCount_dict['Total Entities in New File'].append(count_ents(new_root))

        print(mcds_base + " valid = ",valid, '\n')
        txt_issue_out = diff_main.diff_trees(new_tree, old_tree, formatter=diff_form_txt)
        #Append issues (besides whitespace after node) to dictionary
        issue_cnt = 0
        for x in txt_issue_out.split('\n'):
            x = x.lstrip('[',1).rstrip(']',1)
            if 'update-text-after' in x:
                #remove new line, tab and space from 'tail to add' of issue line. If there is still content, add line to
                tail = x.rsplit(',', 1)[1].replace(r'\n','').replace(r'\t','').replace('"','').strip()
                if len(tail) > 0:
                    BadLines_dict['DCL Filename'].append(mcds_base)
                    BadLines_dict['Action Needed'].append(x.split(',',1)[0])
                    BadLines_dict['Issue location and correction'].append(x.split(',',1)[1])
                    issue_cnt += 1
            else:
                BadLines_dict['DCL Filename'].append(mcds_base)
                BadLines_dict['Action Needed'].append(x.split(',', 1)[0])
                BadLines_dict['Issue location and correction'].append(x.split(',', 1)[1])
                issue_cnt +=1

        ErrorCount_dict['Num of Issues in New File'].append(issue_cnt)

#Write data to excel file
writer = pd.ExcelWriter('DCLConversionEval.xlsx', engine='xlsxwriter')

df1 = pd.DataFrame(data=ErrorCount_dict)
df2 = pd.DataFrame(data = BadLines_dict)

df1.to_excel(writer, sheet_name='Evaluation Metrics')
df2.to_excel(writer, sheet_name='File Lines with diff')
writer.save()
