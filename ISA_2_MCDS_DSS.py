'''
ISA_2_MCDS_DSS.py
Input:
    Folder containing 3 ISA Files corresponding to 1 Digital Snapshot

Output:
    1 Digital Snapshot .XML file:
    <DSS-root-filename>_converted.xml


Author: Corey Chitwood
Date:
    v1.0 - June 2021
'''

import os
from lxml import etree
import pandas as pd
import sys
import numpy as np
import csv
from tqdm import tqdm



os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))
cwd = os.getcwd()

#DSS Template and ISA File Folder should be located in same folder as script
template = os.path.join(cwd,'Current_Clean_DSS.xml')
ISA_folder = os.path.join(cwd,'ISATabOutput')
ISA_folder_list = os.listdir(ISA_folder)
DSS_output_folder = os.path.join(cwd,'MCDS Conversion Output')

#makes output folder if it does not already exist
try:
    os.mkdir(DSS_output_folder)
except:
    pass

#script takes ~3 min/file
#leave only ':' within ISA_folder_list brackets if all files in folder to be converted
#else, insert number following : to do first n files, or change to a range of files
conv_list = ISA_folder_list[:]

for ISA_filebase in tqdm(conv_list, desc='Converting ISA-Tab Files to MCDS DSS Files', total=len(conv_list), mininterval=1):

    parser = etree.XMLParser(remove_comments=True)
    tree = etree.parse(template)
    root = tree.getroot()

    #standard for all MCDS DSS
    root.set('type','snapshot/clinical')
    root.set('version','1.0.0')

    #path of folder corresponding to a snapshot to ISA file conversion (within ISA_folder)
    ISA_files_folder = os.path.join(ISA_folder,ISA_filebase)

    #path of each individual ISA file
    i_filename = os.path.join(ISA_files_folder,'i_' + ISA_filebase + '.txt')
    s_filename = os.path.join(ISA_files_folder,'s_' + ISA_filebase + '.txt')
    a_filename = os.path.join(ISA_files_folder,'a_geo_props_' + ISA_filebase + '.txt')

    #path of output DSS file
    conv_DSS = os.path.join(DSS_output_folder, ISA_filebase + '_converted.xml')



    #imports data from i_ file to array using csv.reader
    with open(i_filename) as f_i:
        reader = csv.reader(f_i, delimiter = '\t')
        i = 0
        width_list = []
        for row in reader:
            i += 1
            width_list.append(len(row))
        i_len = i
        i_width = max(width_list)
        i_data = np.empty([i_len, i_width], dtype='U1000')
        i = -1
        #after determining width and length of i_data, must return to beginning of reader to iterate thru again using seek(0)
        f_i.seek(0)
        for row in reader:
            i += 1
            for input in range(len(row)):
                i_data[i,input] = row[input]
    # imports data from s_ file to array using csv.reader
    with open(s_filename, 'r', newline = '') as f_s:
        reader = csv.reader(f_s, delimiter = '\t')
        width_list = []
        i = 0
        for row in reader:
            i += 1
            width_list.append(len(row))
        s_len = i
        s_width = max(width_list)
        s_data = np.empty([s_len, s_width], dtype='U1000')
        i = -1
        f_s.seek(0)
        for row in reader:
            i += 1
            for input in range(len(row)):
                s_data[i,input] = row[input]
    # imports data from a_ file to array using csv.reader
    with open(a_filename, 'r', newline = '') as f_a:
        reader = csv.reader(f_a, delimiter = '\t')
        width_list = []
        reader_list = list(reader)
        a_len = len(reader_list)
        f_a.seek(0)
        for row in reader:
            width_list.append(len(row))
        a_width = max(width_list)
        a_data = np.empty([a_len, a_width], dtype='U1000')
        i = -1
        f_a.seek(0)
        for row in reader:
            i += 1
            for input in range(len(row)):
                a_data[i,input] = row[input]

    #data from each file has now been assigned to a corresponding array
    #now iterate through each array, assigning data to the tags/attributes in the clean DSS template root
    #then write root to new .xml file, with the name of the original + 'converted'


    #path of excel DB
    db = os.path.join(cwd, 'MCDS_DSS_2_ISA_Relationships.xlsx')

    #reading columns of excel DB to a pandas dataframe
    df_i = pd.read_excel(rF'{db}', sheet_name='Reverse', usecols=['Investigation Header', 'Investigation Entity', 'Investigation xPath'])
    df_s = pd.read_excel(rf'{db}', sheet_name='Reverse', usecols=['Study Header', 'Study Entity', 'Study xPath'])
    df_a = pd.read_excel(rf'{db}', sheet_name='Reverse', usecols=['Assay Header', 'Assay Entity', 'Assay xPath'])


    #reading i_file data and assigning to template

    for array_row_index in range(i_len):
        array_header = str(i_data[array_row_index,0])
        df_index = df_i[df_i['Investigation Header'] == array_header].index.tolist()[0]
        xpath = df_i.at[df_index,'Investigation xPath']
        header = df_i.at[df_index,'Investigation Header']
        entity = df_i.at[df_index,'Investigation Entity']

        #in current ISA files, there is a maximum of 3 columns of data that should be transferred to MCDS DSS
        #if in the future more rows need transferring, update this section
        data = i_data[array_row_index,1]
        data2 = i_data[array_row_index,2]
        data3 = i_data[array_row_index,3]

        #accouting for additional data that is required for an ISA file but does not correspond to a tag in MCDS DSS
        if xpath == 'none':
            continue

        # '*' indicates study contact data which has multiple columns in i_ file and multiple xpaths in MCDS DSS
        elif '*' in entity:
            xpath_list = xpath.split(', ')
            try:
                root.find(xpath_list[0]).text = data
                root.find(xpath_list[1]).text = data2
                root.find(xpath_list[2]).text = data3
            except:
                print('Issue with: ', header, data, array_row_index)

        # '&' indicates that that data originally came from 2 separate MCDS entities that were merged for the i_file
        #reverse script needs to separate that data back to its original MCDS entities
        elif '&' in entity:
            data_list = data.split('-')
            xpath_list = xpath.split(',')
            try:
                root.find(xpath_list[0]).text = data_list[0]
                root.find(xpath_list[1]).text = data_list[1]
            except:
                print('Issue with :', header, data, array_row_index)

        #tag data assigned to corresponding tag
        elif '@' not in xpath:
            # ' ;; ' replaced '\n' in MCDS to ISA script to keep data on one line, in accordance with ISA standard
            # this section of code reverses that change
            if ' ;; ' in data:
                data_list = [x.strip() for x in data.split(' ;; ')]
                new_ln_tab = '\n' + '\t' * (xpath.count('/') + 2)
                end_ln_tab = '\n' + '\t' * (xpath.count('/') + 1)
                data = new_ln_tab.join(data_list)
                data = new_ln_tab + data + end_ln_tab
            try:
                root.find(xpath).text = data
            except:
                print('Issue with: ',header,data,array_row_index)

        #attribute data assigned to corresponding attribute
        else:
            elem_path = xpath.rsplit('[',1)[0]
            attr = xpath.split('@')[1].strip(']').strip()
            try:
                root.find(elem_path).set(attr, data)
            except:
                print('Issue with: ', header, data, array_row_index)

    #reading s_ file data and assigning to template

    for col_index in range(s_width):
        array_header = s_data[0,col_index]
        df_index = df_s[df_s['Study Header'] == array_header].index.tolist()[0]
        xpath = df_s.at[df_index, 'Study xPath']
        header = df_s.at[df_index, 'Study Header']
        entity = df_s.at[df_index, 'Study Entity']
        data = s_data[1,col_index]
        #while s_ file has many rows, the only information that changes from row to row is the source/sample name
        #all other data remains the same, so only the first row is needed for transferring data to MCDS DSS file

        #if this changes in the future, update this section of code to iterate for row_index, just like section
        #that iterates thru the a_ file data

        if array_header == 'Characteristic[Primary Diagnosis]':
            if data == 'None':
                continue
            else:
                xpath_list = root.findall(xpath)
                xpath_list[0].text = data
        elif array_header == 'Characteristic[Secondary Diagnosis]':
            if data == 'None':
                continue
            else:
                xpath_list = root.findall(xpath)
                xpath_list[1].text = data
        elif array_header == 'Characteristic[Tertiary Diagnosis]':
            if data == 'None':
                continue
            else:
                xpath_list = root.findall(xpath)
                xpath_list[2].text = data
        elif array_header == 'Characteristic[Final Diagnosis]':
            xpath_list = root.findall(xpath)
            xpath_list[3].text = data
        elif xpath == 'none':
            continue
        elif '@' not in xpath:
            try:
                root.find(xpath).text = data
            except:
                print('Issue with: ', header, data, col_index)
        else:
            elem_path = xpath.rsplit('[',1)[0]
            attr = xpath.split('@')[1].strip(']').strip()
            try:
                root.find(elem_path).set(attr, data)
            except:
                print('Issue with: ', header, data, col_index)

    #reading a_ file data and assigning to template

    #counter for 'Units' header
    z = -1



    for col_index in range(a_width):

        array_header = a_data[0,col_index]

        #'units' header appears multiple times in ISA file, so need to count the occurences to make sure we are assigning
        #unit data to the correct location in the MCDS DSS using counter 'z'

        #section below finds df_a index corresponding to correct 'units' occurence
        if array_header == 'Units':
            z = z + 1
            df_index = df_a[df_a['Assay Header'] == array_header].index.tolist()[z]
        #else finds first occurence of header in DB
        else:
            df_index = df_a[df_a['Assay Header'] == array_header].index.tolist()[0]


        xpath = df_a.at[df_index, 'Assay xPath']


        if xpath == 'none':
            continue

        header = df_a.at[df_index, 'Assay Header']
        entity = df_a.at[df_index, 'Assay Entity']

        #iterate thru column, iterate thru row/root.findall(xpath)

        for row_index in range(a_len):
            if row_index == 0:
                continue
            i = row_index - 1
            data = a_data[row_index,col_index]
            if array_header == 'Characteristic[Population Type]':
                elem_path = xpath.rsplit('[',1)[0]
                attr = xpath.split('@')[1].strip(']').strip()
                try:
                    root.find(elem_path).set(attr,data)
                except:
                    print('Issue with population type')
            #assign data to corresponding occurence of corresponding tag
            elif '@' not in xpath:
                root.findall(xpath)[i].text = data
            #assign data to corresponding occurence of corresponding attribute
            else:
                elem_path = xpath.rsplit('[',1)[0]
                attr = xpath.split('@')[1].strip(']').strip()
                try:
                    root.findall(elem_path)[i].set(attr, data)
                except:
                    print('Issue with: ', header, data, col_index)



    #did not define citation URL in i_ file so need to manually define it in converted file
    root.find('metadata/citation/URL').text = '\n\t\t\t\thttp://MultiCellDS.org\n\t\t\t'


    #remove empty tags at end of template
    #cell is the parent tag of all reapeated elements that need to be removed
    #if in the future additional tags are empty, update this section to remove those tags
    cell_list = root.findall('cellular_information/cell_populations/cell_population/cell')
    for i in range(len(cell_list)):
        elem = cell_list[i]
        cell_id = elem.get('ID')
        if cell_id == '':
            elem.getparent().remove(elem)
        else:
            continue

    #remove receptor tag in files that have no receptor data
    #receptor tag only occurs once
    elem = root.find('metadata/cell_origin/custom/receptor')
    if elem.get('CHEBI_ID') == '':
        elem.getparent().remove(elem)

    #corrects indentations


    def indent(elem, level=0):
        i = '\n' + level * '\t'
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + '\t'
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                indent(elem, level + 1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i

    indent(root)


    #writes tree to XML file
    with open(conv_DSS, 'wb') as f_xml:
        tree.write(f_xml, pretty_print=True, xml_declaration=True, encoding="utf-8")

#end of script