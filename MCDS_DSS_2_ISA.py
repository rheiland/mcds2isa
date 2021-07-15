'''
MCDS_DSS_2_ISA.py
Input:
  A folder containing MultiCellDS digital snapshot XML files
Output:
  A folder containing:
      A subfolder <DSS-root-filename> containing 3 ISA-Tab files:
          i_<DSS-root-filename>.txt
          s_<DSS-root-filename>.txt
          a_<DSS-root-filename>.txt
Author: Corey Chitwood
Date:
  v1.0 - June 2021
'''


import os
import sys
import re
import pandas as pd
from lxml import etree
import numpy as np
from tqdm import tqdm


os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))
cwd = os.getcwd()

#excel db and MCDS DSS folder should be in same folder as script
db = os.path.join(cwd, 'MCDS_DSS_2_ISA_Relationships.xlsx')
DSS_folder = os.path.join(cwd, 'All_Digital_Snapshots')

#ISA Tab output path (to contain folders with ISA files)
ISA_out = os.path.join(cwd, 'ISATabOutput')

#counter
q=0

with os.scandir(DSS_folder) as DSS_list:
    for DSS_in in DSS_list:

        #for testing with one input MCDS DSS only
        #comment out 3 lines below if converting full folder
        #q = q + 1
        #if q > 1:
        #    break

        DSS_file = os.path.basename(DSS_in)


        #check to make sure file is .xml file before continuing
        if DSS_file[-4:] != '.xml':
            print('Error: Input file ',DSS_file,' is not an .xml file and will be skipped')
            continue


        #parse .xml file
        parser = etree.XMLParser(remove_comments=True)
        tree = etree.parse(os.path.join(DSS_folder, DSS_in), parser=parser)
        root = tree.getroot()

        #check that .xml file is a MCDS DSS
        if root.get('type') != 'snapshot/clinical':
            print('Error: Input file'+ str(DSS_file) + ' is not a Digital Snapshot and will be skipped')
            continue
        if root.get('version') != '1.0.0':
            print('Warning: MCDS version' + str(root.get('version')) + ' may not be supported for conversion')


        #generates file names for i_, s_, and a_ files
        DSS_name = DSS_file.replace('.xml','')
        file_base = DSS_name + '.txt'
        i_filename = 'i_' + file_base
        s_filename = 's_' + file_base
        a_filename = 'a_geo_props_' + file_base

        # names output folder corresponding to the input DSS file name
        output_folder = os.path.join(ISA_out,DSS_name)
        try:
            os.mkdir(output_folder)
        except FileExistsError:
            pass

        #user feedback on progress, could update entire loop to use TQDM for user feedback
        print('Current input file: ', DSS_file)


        #defining dictionary that will be used to add data not contained in MCDS DSS that is required for ISA Files
        script_variables = {
            'i_pub_author_list':[],
            'i_pub_title':[],
            'i_pub_status':[],
            's_filename': [],
            's_pub_author_list':[],
            's_pub_title':[],
            's_factor_name':[],
            's_pub_status':[],
            'a_filename':[],
            'a_measurement_type':[],
            'protocol_names':[],
            'protocol_types':[],
            'MCDS_filename': []
        }


        #assigning script variables based on current support
        script_variables['s_filename'].append(s_filename)
        script_variables['s_factor_name'].append('Nuclear Morphometric Parameters')
        script_variables['a_filename'].append(a_filename)
        script_variables['a_measurement_type'].append('Geometrical Properties')
        script_variables['protocol_names'].append('Digital Snapshot Creation')
        script_variables['protocol_names'].append('Geometrical Property Characterization')
        script_variables['protocol_types'].append('Sample Collection')
        script_variables['protocol_types'].append('Characterization')
        script_variables['MCDS_filename'].append(DSS_file)

        s_factor_name = 'Nuclear Morphometric Parameters'

        #FUTURE- EXPAND _PUB SUPPORT AS THERE ARE CURRENTLY NO PUBLICATIONS ASSOCIATED WITH SNAPSHOTS IN REPOSITORY
        #COULD PROMPT INFO FROM USER AND ADD APPEND TO DICTIONARY FOR WRITING TO I_ FILE LATER IN SCRIPT

        #FUTURE- ALSO EXPAND SCRIPT TO ACCOUNT FOR DIFFERENT TYPES OF ASSAY FILES FROM SNAPSHOT
        #CURRENTLY ONLY GEOMETRICAL PROPERTIES ARE CONTAINED IN SNAPSHOTS
        #WOULD NEED A SECOND/THIRD/ETC ASSAY_WRITE FUNCTION AND A NEW SHEET IN THE EXCEL DB TO ACCOUNT FOR MORE ENTITIES
        #CONTAINED WITHIN THE SNAPSHOT .XML FILE
        #CHANGES WOULD BE SIMILAR TO MCDS2ISA SCRIPT FOR DIGITAL CELL LINE CONVERSION TO ISA STANDARD


        #defines dictionaries that will be updated with ISA parameters/components contained in MCDS DSS files

        protocol_parameters = {
            's_parameters':[],
            'a_parameters':[]
        }
        protocol_components = {
            's_components':[],
            'a_components':[]
        }

        def assay_write():
            '''assay write function requires no input
            reads a_ file data from DSS and writes to a_filename.txt using db as reference guide'''



            #importing assay dataframe
            df_a = pd.read_excel(rF'{db}', sheet_name='Assay',
                                 usecols=['Assay ISA Header', 'Assay Entity', 'Assay xPath','Investigation Parameters','Investigation Components'])
            data_col = len(df_a.index)
            #determines the number of rows of the array, which depends on the number of 'cell' elements in MCDS DSS .xml file
            data_rows_plus_headers = len(root.findall('cellular_information/cell_populations/cell_population/cell')) + 1

            #defines blank numpy array of size corresponding to amt of data in MCDS DSS
            #if assay data is being truncated, expand dtype to 'U1000' or more
            array = np.empty([data_col,data_rows_plus_headers],dtype='U100')

            #iterating through each ROW of the dataframe, which will become each COLUMN in the a_.txt file
            for df_row in df_a.index:
                array_col_index = df_row
                #assigning headers to the first row of the array/a_ file
                array[array_col_index,0] = df_a.at[df_row,'Assay ISA Header']
                entity = df_a.at[df_row,'Assay Entity']
                xpath = df_a.at[df_row,'Assay xPath']
                header = df_a.at[df_row,'Assay ISA Header']

                #if statements to account for varying conditions in Assay xPath column

                if header == 'Sample Name':
                    for row_index in range(data_rows_plus_headers - 1):

                        row = row_index + 1
                        x = str(root.find(xpath).text)
                        y = x + '.0.' + str(row_index)
                        array[array_col_index,row] = y

                elif xpath == 'Text Entry':
                    for row_index in range(data_rows_plus_headers-1):
                        row = row_index + 1
                        array[array_col_index,row] = str(entity)
                elif xpath == 'script variable':
                    if entity == 's_factor_name':
                        for row_index in range(data_rows_plus_headers - 1):
                            row = row_index + 1
                            array[array_col_index,row] = s_factor_name
                    elif entity == 'MCDS_filename':
                        for row_index in range(data_rows_plus_headers - 1):
                            row = row_index + 1
                            array[array_col_index,row] = DSS_file
                elif '@' in xpath:
                    #try:
                    attr_list = []
                    for attr in root.findall(xpath):
                        attr_list.append(attr.get(entity))
                    for row_index in range(data_rows_plus_headers-1):
                        row = row_index + 1
                        if len(attr_list) == 1:
                            array[array_col_index,row] = attr_list[0]
                        else:
                            array[array_col_index,row] = attr_list[row_index]

                #was an issue with this xpath for an unknown reason, so manually added this search in xpath
                elif xpath == 'metadata/MultiCellDB/ID':
                    data_list = []
                    for data in root.iter(entity):
                        data_list.append(data.text)
                    for row_index in range(data_rows_plus_headers-1):
                        row = row_index + 1
                        array[array_col_index,row] = data_list[0]
                else:
                    try:
                        data_list = []
                        for data in root.iter(entity):
                            data_list.append(data.text)
                        for row_index in range(data_rows_plus_headers-1):
                            row = row_index + 1
                            array[array_col_index,row] = data_list[row_index]
                    except:
                        for row_index in range(data_rows_plus_headers-1):
                            row = row_index + 1
                            array[array_col_index,row] = ''
                            pass


            #opens a_ .txt file with name a_filename
            f_a = open(os.path.join(output_folder, a_filename),'w')
            #iterates through each row of array and writes contents to file
            for row_index in range(data_rows_plus_headers):
                for array_col_index in range(data_col):
                    #checks to see if data present under given header, does not write anything to file if no data present
                    if row_index == 0:
                        data_below = array[array_col_index,row_index + 1]
                        if data_below == '':
                            f_a.write('')
                        #else writes header surrounded by "" and separated by '\t' to file (per ISA standard)
                        #also assigns component/parameter to dictionary for later use in i_ file
                        elif array[array_col_index,row_index] == 'MCDS-DSS File':
                            f_a.write('"' + str(array[array_col_index,row_index]) + '"')
                        else:
                            f_a.write('"' + str(array[array_col_index,row_index]) + '"' + '\t')
                            if not pd.isnull(df_a.at[array_col_index,'Investigation Parameters']):
                                protocol_parameters['a_parameters'].append(df_a.at[array_col_index,'Investigation Parameters'])
                            if not pd.isnull(df_a.at[array_col_index,'Investigation Components']):
                                protocol_components['a_components'].append(df_a.at[array_col_index,'Investigation Components'])
                    #writes nothing if there is no data present in array cell
                    elif array[array_col_index,row_index] == '':
                        f_a.write('')
                    #writes data if it is present in array cell
                    elif array_col_index == max(range(data_col)):
                        f_a.write('"' + str(array[array_col_index,row_index]) + '"')
                    else:
                        f_a.write('"' + str(array[array_col_index,row_index]) + '"' + '\t')
                #writes '\n' at the end of each row
                if row_index < max(range(data_rows_plus_headers)):
                    f_a.write('\n')
                else:
                    f_a.write('')
            f_a.close()
            #end of assay_write()

        assay_write()



        #study file

        def study_match(study_ind):
            '''input: index corresponding to line of Study sheet in excel file
            output: 2 strings, the ISA Header of a matching entity, and the data from the DSS .xml file at the entity's xpath'''
            header_output = []
            data_output = []
            type_list = []

            if not pd.isnull(df_s.at[study_ind, 'Study xPath']):
                xpath = df_s.at[study_ind,'Study xPath'].strip()

                if df_s.at[study_ind,'Study Entity'] == 'diagnosis':
                    if df_s.at[study_ind,'Study ISA Header'] == 'Characteristic[Primary Diagnosis]':
                        data_output.append(root.findall(xpath)[0].text)
                        header_output.append(df_s.at[study_ind, 'Study ISA Header'])
                    elif df_s.at[study_ind,'Study ISA Header'] == 'Characteristic[Secondary Diagnosis]':
                        data_output.append(root.findall(xpath)[1].text)
                        header_output.append(df_s.at[study_ind, 'Study ISA Header'])
                    elif df_s.at[study_ind,'Study ISA Header'] == 'Characteristic[Tertiary Diagnosis]':
                        data_output.append(root.findall(xpath)[2].text)
                        header_output.append(df_s.at[study_ind, 'Study ISA Header'])
                    elif df_s.at[study_ind,'Study ISA Header'] == 'Characteristic[Final Diagnosis]':
                        data_output.append(root.findall(xpath)[3].text)
                        header_output.append(df_s.at[study_ind, 'Study ISA Header'])

                elif df_s.at[study_ind, 'Study Entity'] == 'Source Name':
                    header_output.append(df_s.at[study_ind,'Study ISA Header'])
                    x = str(root.find(xpath).text)
                    y = x + str('.0')
                    data_output.append(y)

                elif df_s.at[study_ind,'Study Entity'] == 'Sample Name':
                    header_output.append(df_s.at[study_ind,'Study ISA Header'])
                    data_output.append('sample')



                else:
                    if '@' in xpath:
                        if df_s.at[study_ind,'Study Entity'] == 'type':
                            try:
                                for type in root.findall(xpath):
                                    type_list.append(type.get('type'))
                                header_output.append(df_s.at[study_ind, 'Study ISA Header'])
                                data_output.append(type_list[3])
                            except:
                                header_output.append('')
                                data_output.append('')
                                pass
                        else:
                            try:
                                result = re.split(r"@",xpath)
                                attr = result[1].replace(']','')
                                header_output.append(df_s.at[study_ind, 'Study ISA Header'])
                                data_output.append(root.find(xpath).attrib[attr])
                            except:
                                header_output.append('')
                                data_output.append('')
                                pass
                    else:
                        try:
                            header_output.append(df_s.at[study_ind,'Study ISA Header'])
                            data_output.append(root.find(xpath).text)
                        except:
                            header_output.append('')
                            data_output.append('')
            else:
                header_output.append('')
                data_output.append('')

            final_header = header_output[0]
            final_data = data_output[0]

            return(final_header,final_data)
            #end of study_match



        #writes study file


        df_s = pd.read_excel(rF'{db}', sheet_name='Study', keep_default_na=False,
                                            usecols=['Study ISA Header', 'Study Entity', 'Study xPath','Investigation Components'])
        study_headers = []
        study_data = []

        for study_ind in df_s.index:
            if df_s.at[study_ind,'Study xPath'] == 'Text Entry':
                study_headers.append(str(df_s.at[study_ind,'Study ISA Header']))
                study_data.append(str(df_s.at[study_ind,'Study Entity']))
            else:
                study_match_results = study_match(study_ind)
                study_headers.append(study_match_results[0])
                study_data.append(study_match_results[1])
                if study_data[0] != '':
                    if df_s.at[study_ind,'Investigation Components'] != '':
                        protocol_components['s_components'].append(df_s.at[study_ind,'Investigation Components'])
                    else:
                        continue
        if len(study_headers) != len(study_data):
            print('Error in Study File Writing')
            break

        f_s = open(os.path.join(output_folder, s_filename), 'w')
        x = str(root.find('metadata/MultiCellDB/ID').text)
        for a in range(len(study_headers)):
            #do not write header if there is no corresponding data
            if study_data[a] == '':
                f_s.write('')
            elif study_headers[a] == 'Sample Name':
                f_s.write('"' + str(study_headers[a] + '"'))
            else:
                f_s.write('"' + str(study_headers[a]) + '"' + '\t')
        f_s.write('\n')
        for cell in range(len(root.findall('cellular_information/cell_populations/cell_population/cell'))):
            for a in range(len(study_data)):
                if study_data[a] == '':
                    f_s.write('')
                elif study_data[a] == 'sample':
                    f_s.write('"' + str(x) + '.0.' + str(cell) + '"')
                else:
                    f_s.write('"' + str(study_data[a]) + '"' + '\t')
            if cell < max(range(len(root.findall('cellular_information/cell_populations/cell_population/cell')))):
                f_s.write('\n')
            else:
                f_s.write('')
        f_s.close()



        #investigation file

        df_i = pd.read_excel(rF'{db}', sheet_name='Investigation', usecols=['Investigation ISA Header',
                                                                              'ISA Entity Type', 'Investigation Entity',
                                                                              'Investigation xPath',
                                                                              'Search Type'])
        df_s = pd.read_excel(rF'{db}', sheet_name='Study', usecols=['Study ISA Header','Study Entity',
                                                                              'Study xPath',
                                                                              'Investigation Components'])
        df_a = pd.read_excel(rF'{db}', sheet_name='Assay', usecols=['Assay ISA Header','Assay Entity',
                                                                              'Assay xPath',
                                                                              'Investigation Parameters'])
        #current maxiumum number of columns needed
        #in future, if more columns needed, increase
        columns = 5
        rows = len(df_i.index)
        # defining empty i_array size and dtype 'U1000'
        i_array = np.empty([rows, columns], dtype='U1000')

        def investigation_match():
            '''input: no input
            output: fills i_array with data from MCDS DSS'''


            #iterating through each row of df_i
            for df_i_row in df_i.index:

                #creating variables as shortcuts so as to not retype df_i.at[...]
                xpath = df_i.at[df_i_row,'Investigation xPath']
                header = df_i.at[df_i_row,'Investigation ISA Header']
                entity = df_i.at[df_i_row,'Investigation Entity']
                entity_type = df_i.at[df_i_row,'ISA Entity Type']
                search_type = df_i.at[df_i_row,'Search Type']

                str_list = []

                #if statements to acccount for varying conditions in df_i

                if entity_type == 'Header':
                    # header is straightforard
                    i_array[df_i_row,0] = header
                    #this assigns a string that can be searched for in i_array while writing to determine number of columns
                    #in the i_.txt file for that section
                    i_array[df_i_row,1] = 'Header-' + str(entity)

                elif entity_type == 'Comment':
                    #comments can be either attributes or elements, but if they are not present in the snapshot,
                    #then they should not appear in the final i_ file, hence header changed to '' in i_array
                    if pd.isnull(xpath):
                        i_array[df_i_row,0] = ''
                        i_array[df_i_row,1] = ''
                    elif search_type == 'Contacts':
                        #if error here, check that xpath is split correctly (line below)
                        contacts_list = xpath.split(', ')
                        try:
                            for contact in contacts_list:
                                str_list.append(root.find(contact).text.strip().replace('\t','').replace('\n',' ;; ').replace('   ',''))
                            for list_ind in range(len(str_list)):
                                column = list_ind + 1
                                i_array[df_i_row,column] = str_list[list_ind]
                                i_array[df_i_row,0] = header
                        except:
                            i_array[df_i_row,0] = ''
                            i_array[df_i_row,1] = ''

                    elif '@' in xpath:
                        try:
                            for attr in root.findall(xpath):
                                str_list.append(attr.get(entity))
                            for list_ind in range(len(str_list)):
                                column = list_ind + 1
                                i_array[df_i_row,0] = header
                                i_array[df_i_row,column] = str_list[list_ind]
                        except:
                            i_array[df_i_row,0] = ''
                            i_array[df_i_row,1] = ''
                            pass
                    else:
                        try:
                            for elm in root.findall(xpath):
                                str_list.append(elm.text.strip().replace('\t', '').replace('   ', '').replace('\n',' ;; '))
                            for list_ind in range(len(root.findall(xpath))):
                                column = list_ind + 1
                                i_array[df_i_row,column] = str_list[list_ind]
                                i_array[df_i_row,0] = header
                        except:
                            i_array[df_i_row,0] = ''
                            i_array[df_i_row,1] = ''
                            pass

                else:
                    i_array[df_i_row,0] = header
                    if search_type == 'Text Entry':
                        #if text entry, data is already contained in the spreadsheet
                        str_list = [x.strip() for x in entity.split(';') if x]
                        for list_ind in range(len(str_list)):
                            column = list_ind + 1
                            i_array[df_i_row, column] = str_list[list_ind]

                    elif search_type == 'Role':
                        #if role, data is an .xml element itself rather than the data it contains
                        gen_count = xpath.count('*')
                        role_xpath = xpath.replace('*','')
                        if gen_count == 1:
                            str_list.append(root.find(role_xpath).getparent().tag.replace('_', ' ').title())
                        if gen_count == 2:
                            str_list.append(root.find(role_xpath).getparent().getparent().tag.replace('_', ' ').title())
                        for list_ind in range(len(str_list)):
                            column = list_ind + 1
                            i_array[df_i_row,column] = str_list[list_ind]

                    elif search_type == 'Combined':
                        #if combined, need to find data from 2 elements and write them as elem1.text - elem2.text
                        split_paths = xpath.split(',')
                        split_data1 = root.find(split_paths[0]).text
                        split_data2 = root.find(split_paths[1]).text
                        str_list.append(split_data1 + ' - ' + split_data2)
                        for list_ind in range(len(str_list)):
                            column = list_ind + 1
                            i_array[df_i_row,column] = str_list[list_ind]

                    elif search_type == 'Contacts':
                        contacts_list = xpath.split(', ')
                        try:
                            for contact in contacts_list:
                                x = root.find(contact).text
                                str_list.append(root.find(contact).text)
                            for list_ind in range(len(str_list)):
                                column = list_ind + 1
                                i_array[df_i_row,column] = str_list[list_ind]
                        except:
                            continue

                    elif search_type == 'Contacts Role':
                        contacts_list = xpath.split(', ')
                        try:
                            for contact in contacts_list:
                                gen_count = contact.count('*')
                                contact = contact.replace('*','')
                                if gen_count == 1:
                                    str_list.append(root.find(contact).getparent().tag.replace('_', ' ').title())
                                elif gen_count == 2:
                                    str_list.append(root.find(contact).getparent().getparent().tag.replace('_', ' ').title())
                                else:
                                    str_list.append(root.find(contact).text)
                            for list_ind in range(len(str_list)):
                                column = list_ind + 1
                                i_array[df_i_row,column] = str_list[list_ind]
                        except:
                            i_array[df_i_row,1] = ''
                            pass


                    elif search_type == 'Script Variable':
                        str_list = script_variables[entity]
                        if len(str_list) > 0:
                            for list_ind in range(len(str_list)):
                                column = list_ind + 1
                                i_array[df_i_row,column] = str_list[list_ind]
                        else:
                            i_array[df_i_row,1] = ''

                    elif search_type == 'Parameters':
                        s_parameters = ''
                        a_parameters = ''
                        for parameter in protocol_parameters['s_parameters']:
                            s_parameters += str(parameter) + ';'
                        for parameter in protocol_parameters['a_parameters']:
                            a_parameters += str(parameter) + ';'
                        str_list.append(s_parameters)
                        str_list.append(a_parameters)
                        for list_ind in range(len(str_list)):
                            column = list_ind + 1
                            i_array[df_i_row,column] = str_list[list_ind]

                    elif search_type == 'Components':
                        s_components = ''
                        a_components = ''
                        for component in protocol_components['s_components']:
                            s_components += str(component) + ';'
                        for component in protocol_components['a_components']:
                            a_components += str(component) + ';'
                        str_list.append(s_components)
                        str_list.append(a_components)
                        for list_ind in range(len(str_list)):
                            column = list_ind + 1
                            i_array[df_i_row,column] = str_list[list_ind]


                    elif search_type == 'Normal':
                        #if normal, same as if entity_type = 'Comment', but the header is not deleted from i_array
                        if pd.isnull(xpath):
                            i_array[df_i_row,1] = ''
                        elif '@' in xpath:
                            try:
                                for attr in root.findall(xpath):
                                    str_list.append(attr.get(entity))
                                for list_ind in range(len(str_list)):
                                    column = list_ind + 1
                                    i_array[df_i_row, column] = str_list[list_ind]
                            except:
                                i_array[df_i_row, 1] = ''
                                pass
                        else:
                            try:
                                for elm in root.findall(xpath):
                                    str_list.append(elm.text.strip().replace('\t','').replace('\n',' ;; ').replace('   ',''))
                                for list_ind in range(len(str_list)):
                                    column = list_ind + 1
                                    i_array[df_i_row, column] = str_list[list_ind]
                                    i_array[df_i_row,0] = header
                            except:
                                i_array[df_i_row, 1] = ''
                                pass
            #end investigation match


        investigation_match()


        def investigation_write():
            '''writes contents of i_array to i_filename.txt'''

            f_i = open(os.path.join(output_folder,i_filename),'w')
            for row in range(rows):
                if 'Header' in i_array[row,1]:
                    header_list = i_array[row,1].split('-')
                    column_breakpoint = int(header_list[1]) - 1
                    i_array[row,1] = '.'
                for column in range(columns):
                    if column == column_breakpoint:
                        if i_array[row,column] == '':
                            f_i.write('""' + '\n')
                            break
                        elif i_array[row,column] == '.':
                            f_i.write('\n')
                            break
                        else:
                            f_i.write('"' + str(i_array[row,column]) + '"' + '\n')
                            break
                    elif column == 0:
                        if i_array[row,column] == '':
                            break
                        else:
                            f_i.write(str(i_array[row,column]) + '\t')
                    else:
                        if '"' in i_array[row,column]:
                            f_i.write(str(i_array[row,column]) + '\t')
                        elif i_array[row,column] == '.':
                            f_i.write('\n')
                            break
                        else:
                            f_i.write('"' + str(i_array[row,column]) + '"' + '\t')
            f_i.close()
            #end investigation_write()

        investigation_write()

        #end of script