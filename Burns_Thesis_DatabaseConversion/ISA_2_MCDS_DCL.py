'''
ISA_2_MCDS_DCL.py - using ISA files in supported format, create analagous MultiCellDS digital cell line XML file

Input:
  Folder containing ISA files that belong to a single DCL

Output:
  1 MCDS-DCL .xml files:
   <DCL-root-filename>_converted.xml

Author: Connor Burns
Date:
  v0.1 - Apr 2021

'''
import os
from lxml import etree
import copy
import pandas as pd
from tqdm import tqdm

cwd = os.getcwd()
DCL_xml_dir = os.path.join(cwd,'ISA to MCDS')
DCL_template = os.path.join(DCL_xml_dir, 'DCL Template' ,"DCL_CleanTemplate.xml")
ISA_inputs = os.path.join(cwd,'ISATabOutput')
ISA_folder_list = os.listdir(ISA_inputs)

for ISA_file_base in tqdm(ISA_folder_list, desc= 'ISA.txt to DCL.xml', total=len(ISA_folder_list)):

    parser = etree.XMLParser(remove_comments=True)
    tree = etree.parse(DCL_template, parser=parser)
    root = tree.getroot()
    #Defaults for all current MCDS-DCL files
    root.set('type',"cell_line")
    root.set('version', "1.0.0")

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
            line_content = [x.strip('"') for x in line_list[1:]]
            if len([x for x in line_content if x]) > 0:
                I_data[line_list[0]] = [x.strip('"') for x in line_list[1:]]

    #default is first match
    #TODO - remove except clause? Throw error instead if there is no match (need to update xml template)

    def write_by_xPath(xPath, value):
        if value != 'nan':
            if '@' not in xPath:
                try:
                    root.find(xPath).text = str(value)
                except:
                    print('no element at ', xPath)
            else:
                elem_path = xPath.rsplit('[',1)[0]
                attr = xPath.split('@')[1].strip(']').strip()
                try:
                    root.find(elem_path).set(attr, str(value))
                except:
                    print('no attrib at ', xPath)
                    print(type(value))

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
        :return: A list of all elements found at the input element path (original + copies)
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

    #Study df na_filter = False: there is an instance in MCDS#003 where Morphology.text = 'N/A' literal
    study_name = I_data['Study File Name'][0]
    study_df = pd.read_csv(os.path.join(ISA_file_folder,study_name), sep='\t', dtype = str, na_filter = False)
    study_singles_df = study_df.drop(['Source Name', 'Protocol REF', 'Cell Line Label', 'MultiCellDB Name','Sample Name'], axis = 1)
    #Change "units" columns to match xlsx relationship sheet
    for col in study_singles_df.columns:
        if 'Units' in col:
            unit_ind = study_singles_df.columns.get_loc(col)
            paired_param = study_singles_df.columns[unit_ind - 1]
            param_name = paired_param.replace('Parameter Value[', '').replace(']', '').strip()
            new_col = param_name + ' - Units'
            study_singles_df.rename({col: new_col}, axis=1, inplace=True)

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
    sample_names = [x for x in study_df['Sample Name']]
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
        data_analy_elems = copy_elem('cell_line/metadata/data_analysis', num_data_analy_elem)
        rel_data_analy = rel_df_inv.loc[(rel_df_inv['ISA-Tab Entity'].str.contains('Data Analysis'))]
        #loop through elements found
        for dict_ind, elem in enumerate(data_analy_elems):
            analy_elem_path = tree.getelementpath(elem)
            for header in data_analy_dict:
                #Check to see if index in elem
                #If data analysis citation is the header and citations are joined under one parent, split and write to
                #separate URL elements for the same citation parent
                if dict_ind < len(data_analy_dict[header]):
                    if '[Data Analysis - citation URL]' in header:
                        if ';' in data_analy_dict[header][dict_ind]:
                            split_url = data_analy_dict[header][dict_ind].split(';')
                            for j,url in enumerate(split_url):
                                write_by_xPath((analy_elem_path + '/citation' + URL_path_tail[j]), url.strip())
                        else:
                            write_by_xPath((analy_elem_path + '/URL'),data_analy_dict[header][dict_ind].strip())
                    else:
                        rel_ind = rel_data_analy['ISA-Tab Entity'][rel_data_analy['ISA-Tab Entity'] == header].index[0]
                        val_path = str(rel_data_analy.at[rel_ind, 'MCDS-DCL Correlate X-Path'])
                        val_path = analy_elem_path + val_path.rsplit('data_analysis',1)[1]
                        val_to_write = data_analy_dict[header][dict_ind]
                        write_by_xPath(val_path,val_to_write)

    #Study Contacts
    #For contacts with multiple roles: split apart using splitDataFrameList function
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
            if role in contact_role_series.index:
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

    #Import all assay files as pandas dataframes. If the assay exists, copy elements where necessary before copying phenotype
    #dataset elements. If the assay does not exist, remove its elements from the element tree
    #TODO - Add adding of additional things here? Might be easier to supply now (will have extras for phenotype datasets)

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
    exist_assay_names = []
    phenotype_type_dict = {}

    for a_file in I_data['Study Assay File Name']:
        if "CellCycle" in a_file:
            exist_assay_names.append('CellCycle')
            cellcycle_df = pd.read_csv(os.path.join(ISA_file_folder, a_file), sep='\t', dtype = str)
            exist_assay_path.append('cell_line/phenotype_dataset/phenotype/cell_cycle')
            #determine structure of file rows based on phenotype dataset, cell cycle model, and cell cycle phase and save data to dict
            exist_cycle_dict = {}
            for sample_ind in cellcycle_df.index:
                sample = str(cellcycle_df.at[sample_ind,'Sample Name'])
                cycle_model = str(cellcycle_df.at[sample_ind,'Characteristic[Cell Cycle Model]'])
                phase = str(cellcycle_df.at[sample_ind,'Characteristic[Cell Cycle Phase]'])
                phenotype_type = str(cellcycle_df.at[sample_ind,'Characteristic[Phenotype Type]'])
                if exist_cycle_dict.get(sample) is None:
                    exist_cycle_dict[sample] = {}
                if exist_cycle_dict[sample].get(cycle_model) is None:
                    exist_cycle_dict[sample][cycle_model] = []
                exist_cycle_dict[sample][cycle_model].append(phase)
                phenotype_type_dict[sample] = phenotype_type
            # determine necessary elements to copy based on assay contents, make copies, and save elements
            num_models = []
            num_phase = []
            for sample in exist_cycle_dict.keys():
                num_models.append(len(exist_cycle_dict[sample].keys()))
                for model in exist_cycle_dict[sample].keys():
                    num_phase.append(len(exist_cycle_dict[sample][model]))
            num_model_elems = max(num_models)
            num_phase_elems = max(num_phase)
            #If there is an error later on, use conditional statement here
            cycle_phase_elems = copy_elem('cell_line/phenotype_dataset/phenotype/cell_cycle/cell_cycle_phase',num_phase_elems)
            cycle_model_elems = copy_elem('cell_line/phenotype_dataset/phenotype/cell_cycle', num_model_elems)

        elif "CellDeath" in a_file:
            exist_assay_names.append('CellDeath')
            celldeath_df = pd.read_csv(os.path.join(ISA_file_folder, a_file), sep='\t', dtype = str)
            exist_assay_path.append('cell_line/phenotype_dataset/phenotype/cell_death')
            exist_death_dict = {}
            for sample_ind in celldeath_df.index:
                sample = str(celldeath_df.at[sample_ind,'Sample Name'])
                death_type = str(celldeath_df.at[sample_ind,'Characteristic[Death Type]'])
                phenotype_type = str(celldeath_df.at[sample_ind,'Characteristic[Phenotype Type]'])
                if exist_death_dict.get(sample) is None:
                    exist_death_dict[sample] = []
                exist_death_dict[sample].append(death_type)
            num_death = []
            for sample in exist_death_dict.keys():
                num_death.append(len(exist_death_dict[sample]))
            num_death_elems = max(num_death)
            death_type_elems = copy_elem('cell_line/phenotype_dataset/phenotype/cell_death',num_death_elems)

        elif "ClinicalStain" in a_file:
            exist_assay_names.append('ClinicalStain')
            clinstain_df = pd.read_csv(os.path.join(ISA_file_folder, a_file), sep='\t', dtype = str)
            exist_assay_path.append('cell_line/metadata/custom/clinical/diagnosis/pathology/pathology_definitions/stain')
            exist_assay_path.append('cell_line/metadata/custom/clinical/diagnosis/pathology/stain')
            num_stains = len(list(clinstain_df['Stain Name']))
            stain_def_path = 'cell_line/metadata/custom/clinical/diagnosis/pathology/pathology_definitions/stain'
            stain_meas_path = 'cell_line/metadata/custom/clinical/diagnosis/pathology/stain'
            stain_def = [tree.getelementpath(x) for x in copy_elem(stain_def_path, num_stains)]
            stain_meas = [tree.getelementpath(x) for x in copy_elem(stain_meas_path, num_stains)]

        elif "GeometricalProperties" in a_file:
            exist_assay_names.append('GeometricalProperties')
            geoprops_df = pd.read_csv(os.path.join(ISA_file_folder, a_file), sep='\t', dtype = str)
            exist_assay_path.append('cell_line/phenotype_dataset/phenotype/geometrical_properties')
            exist_assay_path.append('cell_line/phenotype_dataset/cell_part/phenotype/geometrical_properties')
            exist_assay_path.append('cell_line/phenotype_dataset/cell_part/cell_part/phenotype/geometrical_properties')
            exist_geoprops_dict = {}
            for sample_ind in geoprops_df.index:
                sample = str(geoprops_df.at[sample_ind,'Sample Name'])
                if exist_geoprops_dict.get(sample) is None:
                    exist_geoprops_dict[sample] = {}
                cell_part = str(geoprops_df.at[sample_ind,'Characteristic[Cell Part]'])
                if cell_part != 'Entire Cell':
                    if ' of ' not in cell_part:
                        if exist_geoprops_dict[sample].get(cell_part) is None:
                            exist_geoprops_dict[sample][cell_part] = []
                    else:
                        part_name = cell_part.split(' of ')[1]
                        sub_part = cell_part.split(' of ')[0]
                        if exist_geoprops_dict[sample].get(part_name) is None:
                            exist_geoprops_dict[sample][part_name] = []
                        exist_geoprops_dict[sample][part_name].append(sub_part)

            # determine necessary elements to copy based on assay contents, make copies, and save elements
            num_parts = []
            num_subparts = []
            for sample in exist_geoprops_dict.keys():
                num_parts.append(len(exist_geoprops_dict[sample].keys()))
                for cell_part in exist_geoprops_dict[sample].keys():
                    num_subparts.append(len(exist_geoprops_dict[sample][cell_part]))

            if len(num_parts) > 0:
                num_parts = max(num_parts)
                geo_cellpart_elems = copy_elem('cell_line/phenotype_dataset/cell_part', num_parts)
            else:
                geo_cellpart_elems = []
            if len(num_subparts) > 0:
                num_subparts = max(num_subparts)
                geo_subpart_elems = copy_elem('cell_line/phenotype_dataset/cell_part/cell_part', num_subparts)
            else:
                geo_subpart_elems = []

        elif "Mechanics" in a_file:
            exist_assay_names.append('Mechanics')
            mechanics_df = pd.read_csv(os.path.join(ISA_file_folder, a_file), sep='\t', dtype = str)
            exist_assay_path.append('cell_line/phenotype_dataset/phenotype/mechanics')
            exist_assay_path.append('cell_line/phenotype_dataset/cell_part/phenotype/mechanics')
            exist_assay_path.append('cell_line/phenotype_dataset/cell_part/cell_part/phenotype/mechanics')
            #find existing mechaincs elements
            exist_mechanics_dict = {}
            for sample_ind in mechanics_df.index:
                sample = str(mechanics_df.at[sample_ind, 'Sample Name'])
                if exist_mechanics_dict.get(sample) is None:
                    exist_mechanics_dict[sample] = {}
                cell_part = str(mechanics_df.at[sample_ind, 'Characteristic[Cell Part]'])
                if cell_part != 'Entire Cell':
                    if ' of ' not in cell_part:
                        if exist_mechanics_dict[sample].get(cell_part) is None:
                            exist_mechanics_dict[sample][cell_part] = []
                    else:
                        part_name = cell_part.split(' of ')[1]
                        sub_part = cell_part.split(' of ')[0]
                        if exist_mechanics_dict[sample].get(part_name) is None:
                            exist_mechanics_dict[sample][part_name] = []
                        exist_mechanics_dict[sample][part_name].append(sub_part)

            # determine necessary elements to copy based on assay contents, make copies, and save elements
            num_parts = []
            num_subparts = []
            for sample in exist_mechanics_dict.keys():
                num_parts.append(len(exist_mechanics_dict[sample].keys()))
                for cell_part in exist_mechanics_dict[sample].keys():
                    num_subparts.append(len(exist_mechanics_dict[sample][cell_part]))

            if len(num_parts) > 0:
                num_parts = max(num_parts)
                mech_cellpart_elems = copy_elem('cell_line/phenotype_dataset/cell_part', num_parts)
            else:
                mech_cellpart_elems = []
            if len(num_subparts) > 0:
                num_subparts = max(num_subparts)
                mech_subpart_elems = copy_elem('cell_line/phenotype_dataset/cell_part/cell_part', num_subparts)
            else:
                mech_subpart_elems = []

        elif "Microenvironment" in a_file:
            exist_assay_names.append('Microenvironment')
            micro_df = pd.read_csv(os.path.join(ISA_file_folder, a_file), sep='\t', dtype = str)
            exist_assay_path.append('cell_line/phenotype_dataset/microenvironment')
            micro_var_names = []
            for col in micro_df.columns:
                if 'Parameter Value[' in col:
                    if not any(x in col for x in ['Temperature', 'Experiment Dimensionality']):
                        potential_var = col.replace('Parameter Value[','').strip(']')
                        if not any(x in potential_var for x in micro_var_names):
                            micro_var_names.append(potential_var)
            exist_micro_samples = []
            for sample_ind in micro_df.index:
                sample = str(micro_df.at[sample_ind, 'Sample Name'])
                exist_micro_samples.append(sample)
            micro_var_elems = copy_elem('cell_line/phenotype_dataset/microenvironment/domain/variables/variable',len(micro_var_names))

        elif "Motility" in a_file:
            exist_assay_names.append('Motility')
            motility_df = pd.read_csv(os.path.join(ISA_file_folder, a_file), sep='\t', dtype = str)
            exist_assay_path.append('cell_line/phenotype_dataset/phenotype/motility')
            exist_restricted_dict = {}
            exist_unrestricted_dict = {}
            all_mot_dict = {}
            #determine motility elements, make copies if necessary
            for sample_ind in motility_df.index:
                sample = str(motility_df.at[sample_ind, 'Sample Name'])
                motility_type = str(motility_df.at[sample_ind, 'Characteristic[Motility Type]'])
                phenotype_type = str(motility_df.at[sample_ind, 'Characteristic[Phenotype Type]'])
                if all_mot_dict.get(sample) is None:
                    all_mot_dict[sample] = []
                all_mot_dict[sample].append(motility_type)
                if motility_type == 'restricted':
                    if exist_restricted_dict.get(sample) is None:
                        exist_restricted_dict[sample] = []
                    exist_restricted_dict[sample].append(motility_type)
                elif motility_type == 'unrestricted':
                    if exist_unrestricted_dict.get(sample) is None:
                        exist_unrestricted_dict[sample] = []
                    exist_unrestricted_dict[sample].append(motility_type)
            num_restrict = []
            for sample in exist_restricted_dict.keys():
                num_restrict.append(len(exist_restricted_dict[sample]))
            if len(num_restrict) > 0:
                num_restrict_elems = max(num_restrict)
                restrict_elems = copy_elem('cell_line/phenotype_dataset/phenotype/motility/restricted',num_restrict_elems)
            else:
                restrict_elems = []

            num_unrestrict = []
            for sample in exist_unrestricted_dict.keys():
                num_unrestrict.append(len(exist_unrestricted_dict[sample]))
            if len(num_unrestrict) > 0:
                num_unrestrict_elems = max(num_unrestrict)
                unrestrict_elems = copy_elem('cell_line/phenotype_dataset/phenotype/motility/unrestricted',num_unrestrict_elems)
            else:
                unrestrict_elems = []

        elif "PKPD" in a_file:
            exist_assay_names.append('PKPD')
            PKPD_df = pd.read_csv(os.path.join(ISA_file_folder, a_file), sep='\t', dtype = str)
            exist_assay_path.append('cell_line/phenotype_dataset/phenotype/PKPD/pharmacodynamics')

        elif "StateTransition" in a_file:
            exist_assay_names.append('StateTransition')
            statetrans_df = pd.read_csv(os.path.join(ISA_file_folder, a_file), sep='\t', dtype = str)
            exist_assay_path.append('cell_line/transitions')
            #determine number of phenotype_dataset_collection elements and copy to elementtree
            #make list of condition_types, copy /variable/condition element to the tree for number of condition_types
            pheno_collect_IDs = []
            state_condition_types = []
            for state_col in statetrans_df.columns:
                if '#' in state_col:
                    pheno_collect_IDs.append(state_col.rsplit('#', 1)[1])
                elif 'Parameter Value[' in state_col:
                    if '-' not in state_col:
                        if 'Transition Probability' not in state_col:
                            cond_type = state_col.replace('Parameter Value[','').strip(']')
                            state_condition_types.append(cond_type)
            pheno_collect_IDs = list(set(pheno_collect_IDs))
            pheno_collect_IDs.sort()
            num_pheno_collect = len(pheno_collect_IDs)
            num_cond_types = len(state_condition_types)
            pheno_collect_elems = copy_elem('cell_line/transitions/phenotype_dataset_collection', num_pheno_collect)
            state_cond_elems = copy_elem('cell_line/transitions/transition/conditions/variable/condition', num_cond_types)
            #get xPath of elems and save to dictionaries as values for the associated ID or condition type
            pheno_collect_paths = [tree.getelementpath(x) for x in pheno_collect_elems]
            pheno_collect_dict = dict(zip(pheno_collect_IDs, pheno_collect_paths))
            state_cond_paths = [tree.getelementpath(x) for x in state_cond_elems]
            state_cond_dict = dict(zip(state_condition_types, state_cond_paths))

        elif "TransportProcesses" in a_file:
            exist_assay_names.append('TransportProcesses')
            transport_df = pd.read_csv(os.path.join(ISA_file_folder, a_file), sep='\t', dtype = str)
            exist_assay_path.append('cell_line/phenotype_dataset/phenotype/transport_processes')
            exist_transprocess_dict = {}
            for sample_ind in transport_df.index:
                sample = str(transport_df.at[sample_ind, 'Sample Name'])
                variable_name = str(transport_df.at[sample_ind, 'Variable Name'])
                phenotype_type = str(transport_df.at[sample_ind, 'Characteristic[Phenotype Type]'])
                if exist_transprocess_dict.get(sample) is None:
                    exist_transprocess_dict[sample] = []
                exist_transprocess_dict[sample].append(variable_name)
            num_vars = []
            for sample in exist_transprocess_dict.keys():
                num_vars.append(len(exist_transprocess_dict[sample]))
            num_var_elems = max(num_vars)
            transport_process_elems = copy_elem('cell_line/phenotype_dataset/phenotype/transport_processes/variable', num_var_elems)

    no_assay_path = [x for x in all_assay_paths if x not in exist_assay_path]
    for path in no_assay_path:
        remove_elem(path)
    #print(exist_assay_names)
    pheno_data_paths = {}
    pheno_data_elems = copy_elem('cell_line/phenotype_dataset',len(phenodataset_IDs))
    for i, elem in enumerate(pheno_data_elems):
        elem.set('ID',phenodataset_IDs[i])
        elem.set('keywords', I_data['Study Factor Name'][i])
        pheno_data_paths[sample_names[i]] = tree.getelementpath(elem)



    def CellCycleAssay(df, elem_dict, model_elems, phase_elems):
        '''

        :param df: pandas dataframe of assay file content
        :param elem_dict: dictionary of samples, cycle model, and cycle phase data from assay file
        :param model_elems: list of original and copied cell cycle model elements
        :param phase_elems: list of original and copied cell cycle phase elements
        :return:
        '''
        #Change dataframe Units columns to match xlsx sheet (changed to 'Units' for ISA format)
        for col in df.columns:
            if 'Units' in col:
                unit_ind = df.columns.get_loc(col)
                paired_param = df.columns[unit_ind - 1]
                param_name = paired_param.replace('Parameter Value[','').replace(']','').strip()
                new_col = param_name + ' - Units'
                df.rename({col : new_col}, axis = 1, inplace = True)

        #Remove labels from file that aren't desired for writing by looping through dataframe rows
        df.drop(labels = ['Assay Name', 'MCDS-DCL File','Characteristic[Phenotype Type]', 'Characteristic[Cell Cycle Phase]',
                          'Characteristic[Cell Cycle Model]','Protocol REF','Sample Name'],axis = 1, inplace = True)
        #import data from relationship datasheet
        rel_phase_df = pd.read_excel(rF'{db}', sheet_name='A_CellCycle', usecols=['Cell Cycle Phase ISA Entities', 'Cell Cycle Phase xPaths']).dropna()
        rel_model_df = pd.read_excel(rF'{db}', sheet_name='A_CellCycle', usecols=['Cell Cycle Summary ISA Entities','Cell Cycle Summary xPaths']).dropna()
        model_paths = [tree.getelementpath(x).split('/',2)[2] for x in model_elems]
        phase_paths = [tree.getelementpath(x).rsplit('/',1)[1] for x in phase_elems]

        #Match row index to appropriate base xPath and ID number
        model_path_base_ID = {}
        phase_path_base_ID = {}
        ind_cnt = 0
        for i,sample in enumerate(elem_dict.keys()):
            sample_base = pheno_data_paths[sample]
            for j,model in enumerate(elem_dict[sample].keys()):
                model_path_base = '/'.join([sample_base,model_paths[j]])
                model_path_base_ID[ind_cnt] = [model_path_base, model, j]
                for k,phase in enumerate(elem_dict[sample][model]):
                    phase_path_base = '/'.join([model_path_base,phase_paths[k]])
                    phase_path_base_ID[ind_cnt] = [phase_path_base, phase, k]
                    ind_cnt +=1
        #iterate through rows of dataframe and write content
        for row_ind in df.index:
            phase_base = phase_path_base_ID[row_ind][0]
            phase_name = phase_path_base_ID[row_ind][1]
            phase_ID = phase_path_base_ID[row_ind][2]
            write_by_xPath(phase_base + '[@name]', phase_name)
            write_by_xPath(phase_base + '[@ID]', phase_ID)
            #only write model for distinct model rows (since assay.txt is structured with one line per cycle phase)
            if model_path_base_ID.get(row_ind) is not None:
                model_base = model_path_base_ID[row_ind][0]
                model_name = model_path_base_ID[row_ind][1]
                model_ID = model_path_base_ID[row_ind][2]
                write_by_xPath(model_base + '[@model]',model_name)
                write_by_xPath(model_base + '[@ID]', model_ID)

            for col in df:
                #only look for summary elements (not under phase) for distinct model rows
                if ('Population Doubling' in col) or ('Velocity' in col):
                    if model_path_base_ID.get(row_ind) is not None:
                        rel_ind = rel_model_df['Cell Cycle Summary ISA Entities'][rel_model_df['Cell Cycle Summary ISA Entities'] == col].index[0]
                        model_tail = str(rel_model_df.at[rel_ind, 'Cell Cycle Summary xPaths'])
                        val_to_write = str(df.at[row_ind,col])
                        path_to_write = model_base + model_tail
                        write_by_xPath(path_to_write, val_to_write)
                else:
                    rel_ind = rel_phase_df['Cell Cycle Phase ISA Entities'][rel_phase_df['Cell Cycle Phase ISA Entities'] == col].index[0]
                    phase_tail = str(rel_phase_df.at[rel_ind,'Cell Cycle Phase xPaths'])
                    val_to_write = str(df.at[row_ind, col])
                    path_to_write = phase_base + phase_tail
                    write_by_xPath(path_to_write, val_to_write)

    def CellDeathAssay(df, elem_dict, death_type_elems):
        #Change dataframe Units columns to match xlsx sheet (changed to 'Units' for ISA format)
        for col in df.columns:
            if 'Units' in col:
                unit_ind = df.columns.get_loc(col)
                paired_param = df.columns[unit_ind - 1]
                param_name = paired_param.replace('Parameter Value[','').replace(']','').strip()
                new_col = param_name + ' - Units'
                df.rename({col : new_col}, axis = 1, inplace = True)
        #remove columns from dataframe that aren't used for writing data when looping through dataframe
        #i.e. associated header/xpath not in relationship xlsx
        df.drop(labels = ['Assay Name', 'MCDS-DCL File', 'Sample Name', 'Characteristic[Phenotype Type]',
                          'Protocol REF'],axis = 1, inplace = True)
        #import data from relationship datasheet
        rel_death_df = pd.read_excel(rF'{db}', sheet_name='A_CellDeath', usecols=['Cell Death ISA Entities', 'Cell Death xPaths']).dropna()
        death_paths = [tree.getelementpath(x).split('/',2)[2] for x in death_type_elems]
        #Match row index to appropriate base xPath and ID number
        death_path_base_ID = {}
        ind_cnt = 0
        for i,sample in enumerate(elem_dict.keys()):
            sample_base = pheno_data_paths[sample]
            for j,death in enumerate(elem_dict[sample]):
                death_path_base = '/'.join([sample_base,death_paths[j]])
                death_path_base_ID[ind_cnt] = [death_path_base, j]
                ind_cnt +=1
        #Write ID at appropriate xPath, then find headers in relationship sheet, get xPath tail, join with cell death element
        # base path, write value from input assay file to joined xPath
        for row_ind in df.index:
            death_base = death_path_base_ID[row_ind][0]
            death_ID = death_path_base_ID[row_ind][1]
            write_by_xPath(death_base + '[@ID]', death_ID)
            for col in df:
                rel_ind = rel_death_df['Cell Death ISA Entities'][rel_death_df['Cell Death ISA Entities'] == col].index[0]
                phase_tail = str(rel_death_df.at[rel_ind,'Cell Death xPaths'])
                val_to_write = str(df.at[row_ind, col])
                path_to_write = death_base + phase_tail
                write_by_xPath(path_to_write, val_to_write)

    def ClinicalStainAssay(df, stain_path_def, stain_meas_path):
        '''

        :param df: dataframe of Clinical Stain assay.txt file
        :param stain_path_def: list of generated pathology_definitions/stain xPaths
        :param stain_meas_path: list of generated pathology/stain xPaths
        :return:
        '''
        for col in df.columns:
            if 'Units' in col:
                unit_ind = df.columns.get_loc(col)
                paired_param = df.columns[unit_ind - 1]
                param_name = paired_param.replace('Parameter Value[', '').replace(']', '').strip()
                new_col = param_name + ' - Units'
                df.rename({col: new_col}, axis=1, inplace=True)

        rel_stain_props_df = pd.read_excel(rF'{db}', sheet_name='A_ClinicalStain', usecols=
            ['Clinical Stain Properties ISA Headers', 'Clinical Stain Properties xPaths']).dropna()
        rel_stain_meas_df = pd.read_excel(rF'{db}', sheet_name='A_ClinicalStain', usecols=
            ['Clinical Stain Measurements ISA Header', 'Clinical Stain Measurements xPaths']).dropna()
        #save stain ID, xPaths of elements, and

        stain_ID_paths = {}
        for j,ID in enumerate(list(df['Study Stain ID#'])):
            stain_ID_paths[ID] = [stain_path_def[j], stain_meas_path[j]]
            stain_ID_paths[ID].append(str(df.at[j,'Stain Name']))

        for row_ind in df.index:
            stain_ID = str(df.at[row_ind, 'Study Stain ID#'])
            stain_name = stain_ID_paths[stain_ID][2]
            patho_def_path = stain_ID_paths[stain_ID][0]
            patho_meas_path = stain_ID_paths[stain_ID][1]
            #write stain ID and number to each place
            write_by_xPath(patho_def_path + '[@name]', stain_name)
            write_by_xPath(patho_def_path + '[@ID]', stain_ID)
            write_by_xPath(patho_meas_path + '[@name]', stain_name)
            write_by_xPath(patho_meas_path + '[@ID]', stain_ID)
            for col in df.columns:
                val_to_write = str(df.at[row_ind,col])
                #Hypen in ###-### (em dash?) became invalid character: this replaces with em dash
                if u"\uFFFD" in val_to_write:
                    val_to_write = val_to_write.replace(u"\uFFFD", '–')
                #write measurement content
                if col in list(rel_stain_meas_df['Clinical Stain Measurements ISA Header']):
                    rel_ind = rel_stain_meas_df['Clinical Stain Measurements ISA Header'][rel_stain_meas_df['Clinical Stain Measurements ISA Header'] == col].index[0]
                    path_tail = str(rel_stain_meas_df.at[rel_ind,'Clinical Stain Measurements xPaths'])
                    val_path = patho_meas_path + path_tail
                    write_by_xPath(val_path, val_to_write)
                #write stain property content
                elif col in list(rel_stain_props_df['Clinical Stain Properties ISA Headers']):
                    rel_ind = rel_stain_props_df['Clinical Stain Properties ISA Headers'][rel_stain_props_df['Clinical Stain Properties ISA Headers'] == col].index[0]
                    path_tail = str(rel_stain_props_df.at[rel_ind, 'Clinical Stain Properties xPaths'])
                    val_path = patho_def_path + path_tail
                    write_by_xPath(val_path, val_to_write)

        # remove columns from dataframe that aren't used for writing data when looping through dataframe
        # i.e. associated header/xpath not in relationship xlsx

    def GeoPropsAssay(df, elem_dict, cellpart_elems, subpart_elems):
        '''
        :param df: dataframe of the geomtrical properties assay.txt file
        :param elem_dict: dictionary of existing geometrical property "level" names (sample, cell_part, cell_part/cell_part)
        :param cellpart_elems: list of cell_part elements in the xml (can be none)
        :param subpart_elems: list of cell_part/cell_part elements in the xml (can be none)
        :return:
        '''
        for col in df.columns:
            if 'Units' in col:
                unit_ind = df.columns.get_loc(col)
                paired_param = df.columns[unit_ind - 1]
                param_name = paired_param.replace('Parameter Value[', '').replace(']', '').strip()
                new_col = param_name + ' Measurement - Units'
                df.rename({col: new_col}, axis=1, inplace=True)

        df_geo_val_in = pd.read_excel(rF'{db}', sheet_name='A_GeometricalProperties', keep_default_na=False, usecols=
        ['Cell Geometrical Properties ISA Measurement Name', 'Cell Geometrical Properties xPaths'])
        df_geo_attr_in = pd.read_excel(rF'{db}', sheet_name='A_GeometricalProperties', keep_default_na=True, usecols=
        ['Cell Geometrical Properties Attributes', 'Cell Geometrical Properties ISA Entity Beginning',
         'Cell Geometrical Properties ISA Entity Tail']).dropna(how='all').fillna("")
        # remove blanks from geo_measure_paths, geo_measure, and geo_attr
        # Don't remove blanks from ISA entity beginning + tail lists (blank may be valid
        geo_measure_paths = [str(i) for i in df_geo_val_in['Cell Geometrical Properties xPaths'].tolist() if i]
        geo_measure = [str(i) for i in df_geo_val_in['Cell Geometrical Properties ISA Measurement Name'].tolist() if i]
        geo_attr = [str(i) for i in df_geo_attr_in['Cell Geometrical Properties Attributes'].tolist() if i]
        geo_header_begin = [str(i) for i in df_geo_attr_in['Cell Geometrical Properties ISA Entity Beginning'].tolist()]
        geo_header_tail = [str(i) for i in df_geo_attr_in['Cell Geometrical Properties ISA Entity Tail'].tolist()]

        #combine xlsx relationship sheet data to get dictionary with {ISA Header : xPath}
        geo_headers_paths = {}
        for j, meas in enumerate(geo_measure):
            geo_headers_paths[f'Parameter Value[{meas}]'] = '/geometrical_properties' + geo_measure_paths[j]
            for k, attr in enumerate(geo_attr):
                header = geo_header_begin[k] + meas + geo_header_tail[k]
                geo_headers_paths[header] = '/geometrical_properties' + geo_measure_paths[j] + f'[@{attr}]'

        #create dictionary of [assay file row: [elem base xPath, cell_part name]]
        cellpart_paths = [tree.getelementpath(x).rsplit('/',1)[1] for x in cellpart_elems]
        subpart_paths = [tree.getelementpath(x).rsplit('/',1)[1] for x in subpart_elems]
        row_base_paths = {}
        i = 0
        for sample in elem_dict.keys():
            sample_base = pheno_data_paths[sample]
            row_base_paths[i] = [sample_base + '/phenotype', 'nan']
            i+=1
            for j,part in enumerate(elem_dict[sample]):
                part_base = sample_base +'/'+ cellpart_paths[j]
                row_base_paths[i] = [part_base + '/phenotype', part]
                i += 1
                for k, subpart in enumerate(elem_dict[sample][part]):
                    subpart_base = part_base +'/'+ subpart_paths[k]
                    row_base_paths[i] = [subpart_base + '/phenotype', subpart]
                    i += 1
        for row_ind in df.index:
            base_path = row_base_paths[row_ind][0]
            part_name = row_base_paths[row_ind][1]
            #write phenotype[@type] for rows and part name if cell_part or cell_part/cell_part
            pheno_type = str(df.at[row_ind,'Characteristic[Phenotype Type]'])
            write_by_xPath(base_path + '[@type]', pheno_type)
            if part_name != 'nan':
                write_by_xPath(base_path.rsplit('/',1)[0] + '[@name]', part_name)
            for col in df.columns:
                if col in geo_headers_paths:
                    val_to_write = str(df.at[row_ind,col])
                    val_path = base_path + geo_headers_paths[col]
                    write_by_xPath(val_path, val_to_write)

    def MechanicsAssay(df, elem_dict, cellpart_elems, subpart_elems):
        '''
        :param df: dataframe of the mechanics assay.txt file
        :param elem_dict: dictionary of existing mechanics "level" names (sample, cell_part, cell_part/cell_part)
        :param cellpart_elems: list of cell_part elements in the xml (can be none)
        :param subpart_elems: list of cell_part/cell_part elements in the xml (can be none)
        :return:
        '''
        for col in df.columns:
            if 'Units' in col:
                unit_ind = df.columns.get_loc(col)
                paired_param = df.columns[unit_ind - 1]
                param_name = paired_param.replace('Parameter Value[', '').replace(']', '').strip()
                new_col = param_name + ' - Units'
                df.rename({col: new_col}, axis=1, inplace=True)

        # Import cell mechanics xPaths, correlate cell mechanics ISA headers from excel file and write each entity as string to list
        df_mech_in = pd.read_excel(rF'{db}', sheet_name='A_Mechanics', keep_default_na=False, usecols=
        ['Cell Mechanics ISA Entities', 'Cell Mechanics xPaths'])
        mech_paths = [str(i) for i in df_mech_in['Cell Mechanics xPaths'].tolist() if i]
        mech_headers = [str(i) for i in df_mech_in['Cell Mechanics ISA Entities'].tolist() if i]

        #combine xlsx relationship sheet data to get dictionary with {ISA Header : xPath}
        mech_headers_paths = {}
        for j, meas in enumerate(mech_headers):
            mech_headers_paths[mech_headers[j]] = '/mechanics' + mech_paths[j]

        #create dictionary of [assay file row: [elem base xPath, cell_part name]]
        cellpart_paths = [tree.getelementpath(x).rsplit('/',1)[1] for x in cellpart_elems]
        subpart_paths = [tree.getelementpath(x).rsplit('/',1)[1] for x in subpart_elems]
        row_base_paths = {}
        i = 0
        for sample in elem_dict.keys():
            sample_base = pheno_data_paths[sample]
            row_base_paths[i] = [sample_base + '/phenotype', 'nan']
            i+=1
            for j,part in enumerate(elem_dict[sample]):
                part_base = sample_base +'/'+ cellpart_paths[j]
                row_base_paths[i] = [part_base + '/phenotype', part]
                i += 1
                for k, subpart in enumerate(elem_dict[sample][part]):
                    subpart_base = part_base +'/'+ subpart_paths[k]
                    row_base_paths[i] = [subpart_base + '/phenotype', subpart]
                    i += 1
        for row_ind in df.index:
            base_path = row_base_paths[row_ind][0]
            part_name = row_base_paths[row_ind][1]
            #write phenotype[@type] for rows and part name if cell_part or cell_part/cell_part
            pheno_type = str(df.at[row_ind,'Characteristic[Phenotype Type]'])
            write_by_xPath(base_path + '[@type]', pheno_type)
            if part_name != 'nan':
                write_by_xPath(base_path.rsplit('/',1)[0] + '[@name]', part_name)
            for col in df.columns:
                if col in mech_headers_paths:
                    val_to_write = str(df.at[row_ind,col])
                    val_path = base_path + mech_headers_paths[col]
                    write_by_xPath(val_path, val_to_write)

    def MicroenvironmentAssay(df, sample_list, var_names, var_elems):
        '''

        :param df: microenvironment dataframe, made from ISA microenvironment assay.txt
        :param sample_list: list of sample names that have a microenvironment element
        :param var_names: list of variable names (includes .type)
        :param var_elems: list of element tree variable elements
        :return:
        '''
        # Change dataframe Units columns to match xlsx sheet (changed to 'units' in this case to write

        for col in df.columns:
            if 'Units' in col:
                unit_ind = df.columns.get_loc(col)
                #slice column list and location of units, parse backwards from index of units column,
                #match first occurance of 'Parameter Value["variable"], update col to include "variable" name
                back_list = df.columns.tolist()[0:unit_ind]
                back_list.reverse()
                for rev_col in back_list:
                    if 'Parameter Value[' in rev_col:
                        param_name = rev_col.replace('Parameter Value[', '').replace(']', '').strip()
                        break
                new_col = param_name + ' units'
                df.rename({col: new_col}, axis=1, inplace=True)
        # remove columns from dataframe that aren't used for writing data when looping through dataframe
        # i.e. associated header/xpath not in relationship xlsx
        df.drop(labels=['Assay Name', 'MCDS-DCL File', 'Sample Name',
                        'Protocol REF'], axis=1, inplace=True)

        # import data from relationship datasheet
        rel_micro_df = pd.read_excel(rF'{db}', sheet_name='A_Microenvironment',
                                     usecols=['ISA Condition Entities', 'Microenvironment Condition xPaths']).dropna()
        micro_cond_path = [str(i) for i in rel_micro_df['Microenvironment Condition xPaths'].tolist() if i]
        micro_cond_head = [str(i) for i in rel_micro_df['ISA Condition Entities'].tolist() if i]
        cond_dict = {}
        #make dictionary of ISA condition headers and their associated xPath tails
        for header in micro_cond_head:
            cond_dict[header] = micro_cond_path[micro_cond_head.index(header)]

        #associate sample names with their phenotype_dataset xPath and save to dict
        micro_base_paths = []
        for sample in sample_list:
            sample_base = pheno_data_paths[sample]
            micro_base_paths.append(sample_base + '/microenvironment/')

        #pair variable names and variable xPath tails in dictionary
        var_paths = [tree.getelementpath(x).split('/', 3)[3] for x in var_elems]
        micro_var_dict = {}
        for name in var_names:
            micro_var_dict[name] = var_paths[var_names.index(name)]
        #Loop through rows of microenvironment dataframe and write content
        for row_ind in df.index:
            sample_base = micro_base_paths[row_ind]
            for col in df:
                #Separate variable/variables content and condition (outside variables path) content
                if col in cond_dict.keys():
                    val_path = sample_base + cond_dict[col]
                    val_to_write = str(df.at[row_ind,col])
                    write_by_xPath(val_path, val_to_write)
                for var_name in micro_var_dict.keys():
                    if var_name in col:
                        var_path = sample_base + micro_var_dict[var_name]
                        #if column is the variable measurement, write value, name, and type (if exists) to Etree
                        if col == F'Parameter Value[{var_name}]':
                            meas_value = str(df.at[row_ind,col])
                            if meas_value != 'nan':
                                write_by_xPath(var_path + '/material_amount',meas_value)
                                if '.' in var_name:
                                    name_attr = var_name.split('.')[0]
                                    type_attr = var_name.split('.')[1]
                                    write_by_xPath(var_path + '[@name]',name_attr)
                                    write_by_xPath(var_path + '[@type]',type_attr)
                                else:
                                    write_by_xPath(var_path + '[@name]', var_name)
                        else:
                            val_to_write = str(df.at[row_ind, col])
                            #split at variable name and transform to match DCL element attribute
                            attrib = col.split(var_name)[1].strip(']').strip().replace(' ','_')
                            #write units and ID attributes to variables[@attr], write other attributes to material_amount/variables[@attr]
                            if any(x in attrib for x in ['units','ID']):
                                var_tail = '[@' + attrib + ']'
                            else:
                                var_tail = '/material_amount[@' + attrib + ']'
                            write_by_xPath(var_path + var_tail , val_to_write)

    def MotilityAssay(df, elem_dict, unrestrict_elem, restrict_elem):
        '''
        :param df: dataframe of Motility assay .txt file
        :param unrestrict_elem: list of unrestricted elems (may be empty if none from )
        :param restrict_elem:
        :return:
        '''

        for col in df.columns:
            if 'Units' in col:
                unit_ind = df.columns.get_loc(col)
                paired_param = df.columns[unit_ind - 1]
                param_name = paired_param.replace('Parameter Value[', '').replace(']', '').strip()
                new_col = param_name + ' - Units'
                df.rename({col: new_col}, axis=1, inplace=True)

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

        motility_dict = {}
        for j,meas in enumerate(motility_measure):
            motility_dict[f'Parameter Value[{meas}]'] = motility_measure_paths[j]
            for k,attr in enumerate(motility_attr):
                header = motility_header_begin[k] + meas + motility_header_tail[k]
                motility_dict[header] = motility_measure_paths[j] + f'[@{attr}]'
        #found without xPath in ISA script, added manually here
        motility_dict['Characteristic[Restriction Surface Name]'] = '/restriction/surface_variable[@name]'
        motility_dict['Characteristic[Restriction Surface MeSH ID]'] = '/restriction/surface_variable[@MeSH_ID]'

        unrestrict_path = [tree.getelementpath(x).split('/',2)[2] for x in unrestrict_elem]
        restrict_path = [tree.getelementpath(x).split('/',2)[2] for x in restrict_elem]

        row_base_paths = {}
        ind_cnt = 0
        for i, sample in enumerate(elem_dict.keys()):
            sample_base = pheno_data_paths[sample]
            j = 0
            k = 0
            for model in elem_dict[sample]:
                if model == 'restricted':
                    model_path_base = '/'.join([sample_base,restrict_path[j]])
                    id_num = j
                    j+= 1
                elif model == 'unrestricted':
                    model_path_base = '/'.join([sample_base, unrestrict_path[k]])
                    id_num = k
                    k+=1
                row_base_paths[ind_cnt] = [model_path_base, id_num]
                ind_cnt += 1

        #write motility elements
        for row_ind in df.index:
            base_path = row_base_paths[row_ind][0]
            elem_id = row_base_paths[row_ind][1]
            write_by_xPath(base_path + '[@ID]', elem_id)
            for col in df.columns:
                if col in motility_dict:
                    val_to_write = str(df.at[row_ind,col])
                    path_tail = motility_dict[col]
                    write_by_xPath(base_path + path_tail, val_to_write)


    def pkpdAssay(df):
        '''

        :param df: dataframe of pkpd assay .txt file
        :return:
        '''
        pkpd_heads_paths = {
        "Measurement Set ID#" : '/phenotype/PKPD/pharmacodynamics/therapy_measurement_set[@ID]',
        "Drug #1: Parameter Value[Drug Dose]" : '/phenotype/PKPD/pharmacodynamics/therapy_measurement_set/therapy/drug/dose',
        "Units" : "/phenotype/PKPD/pharmacodynamics/therapy_measurement_set/therapy/drug/dose[@units]",
        "Drug #1: Characteristic[Drug Dose Measurement Type]" : "/phenotype/PKPD/pharmacodynamics/therapy_measurement_set/therapy/drug/dose[@type]",
        "Parameter Value[IC50]" : '/phenotype/PKPD/pharmacodynamics/therapy_measurement_set/response/custom/IC_50',
        "Units.1" : '/phenotype/PKPD/pharmacodynamics/therapy_measurement_set/response/custom/IC_50[@units]',
        "Characteristic[IC50 Measurement Type]" : '/phenotype/PKPD/pharmacodynamics/therapy_measurement_set/response/custom/IC_50[@measurement_type]'
        }
        for row_ind in df.index:
            sample = str(PKPD_df.at[row_ind, 'Sample Name'])
            sample_base = pheno_data_paths[sample]
            write_by_xPath(sample_base + '/phenotype/PKPD/drug[@ID]', row_ind)
            write_by_xPath(sample_base + '/phenotype/PKPD/pharmacodynamics/therapy_measurement_set/therapy/drug[@ID]', row_ind)
            for col in df.columns:
                if col in pkpd_heads_paths.keys():
                    val_to_write = str(PKPD_df.at[row_ind, col])
                    val_path = sample_base + pkpd_heads_paths[col]
                    write_by_xPath(val_path,val_to_write)

    def StateTransitionAssay(df, pheno_collect_dict, state_cond_dict):
        '''
        :param df: dataframe of state transition assay.txt file
        :param pheno_collect_dict: dictionary of {phenotype_dataset_collection ID : phenotype_dataset_collection elem xPath}
        :param state_cond_dict: dictionary of {condition types : condition element xPath}
        :return:
        '''
        for col in df.columns:
            if 'Units' in col:
                unit_ind = df.columns.get_loc(col)
                paired_param = df.columns[unit_ind - 1]
                param_name = paired_param.replace('Parameter Value[','').replace(']','').strip()
                new_col = param_name + ' - Units'
                df.rename({col : new_col}, axis = 1, inplace = True)
        #remove columns from dataframe that aren't used for writing data when looping through dataframe
        #i.e. associated header/xpath not in relationship xlsx
        df.drop(labels = ['Sample Name', 'MCDS-DCL File', 'Protocol REF'],axis = 1, inplace = True)
        #import data from relationship datasheet
        rel_state_df = pd.read_excel(rF'{db}', sheet_name='A_StateTransition', usecols=['Transition ISA Headers'
                                                                                        , 'Transition xPaths']).dropna()
        for row_ind in df.index:
            for col in df.columns:
                # pound sign only in transition/phenotype_dataset_collection
                if '#' in col:
                    collect_ID = col.rsplit('#')[1]
                    #write ID to collection element
                    path_base = pheno_collect_dict[collect_ID]
                    write_by_xPath(path_base + '[@ID]', collect_ID )
                    val_to_write = str(df.at[row_ind, col])
                    if 'Name' in col:
                        val_path = path_base + '/name'
                        write_by_xPath(val_path, val_to_write)
                    elif 'IDs' in col:
                        val_path = path_base + '/IDs'
                        write_by_xPath(val_path, val_to_write)
                #for transition elements not under variable/condition path
                elif col in list(rel_state_df['Transition ISA Headers']):
                    rel_ind = rel_state_df['Transition ISA Headers'][rel_state_df['Transition ISA Headers'] == col].index[0]
                    trans_path = 'cell_line/transitions/transition'
                    path_tail = rel_state_df.at[rel_ind, 'Transition xPaths']
                    val_to_write = str(df.at[row_ind,col])
                    val_path = trans_path + path_tail
                    write_by_xPath(val_path, val_to_write)
                else:
                    #for variable/condition elements
                    for cond_type in state_cond_dict.keys():
                        if cond_type in col:
                            cond_path = state_cond_dict[cond_type]
                            val_to_write = str(df.at[row_ind, col])
                            if col == F'Parameter Value[{cond_type}]':
                                write_by_xPath(cond_path, val_to_write)
                                write_by_xPath(cond_path + '[@condition_type]',cond_type)
                            else:
                                attr = col.split('-')[1].strip(']').strip().lower()
                                write_by_xPath(cond_path + F'[@{attr}]',val_to_write)

    def TransportProcessAssay(df, elem_dict, var_elems):
        '''

        :param df: dataframe of transport processes assay.txt file
        :param elem_dict: dictionary of existing sample names : [variable names] in df
        :param var_elems: list of transport_process elements (original and copy) in template xml
        :return:
        '''

        for col in df.columns:
            if 'Units' in col:
                unit_ind = df.columns.get_loc(col)
                paired_param = df.columns[unit_ind - 1]
                param_name = paired_param.replace('Parameter Value[','').replace(']','').strip()
                new_col = param_name + ' - Units'
                df.rename({col : new_col}, axis = 1, inplace = True)
        #remove columns from dataframe that aren't used for writing data when looping through dataframe
        #i.e. associated header/xpath not in relationship xlsx
        df.drop(labels = ['Assay Name', 'MCDS-DCL File', 'Sample Name', 'Characteristic[Phenotype Type]',
                          'Protocol REF'],axis = 1, inplace = True)
        #import data from relationship datasheet for variables, measurements of variables, and attributes of measurments
        rel_var_df = pd.read_excel(rF'{db}', sheet_name='A_TransportProcesses', usecols=[
            'Transport Processes ISA Variable Headers', 'Transport Processes Variable Attributes']).dropna()
        rel_meas_df = pd.read_excel(rF'{db}', sheet_name='A_TransportProcesses', usecols=[
            'Transport Processes ISA Measurement Name', 'Transport Processes Variable Measurements']).dropna()
        rel_meas_attr_df = pd.read_excel(rF'{db}', sheet_name='A_TransportProcesses', usecols=[
            'Transport Processes Variable Measurement Attributes', 'Transport Processes ISA Entity Beginning',
            'Transport Processes ISA Entity Tail']).dropna(how='all').fillna("")
        #Join together measurements and measurement attributes info to make dictionary of ISA Header : xPath
        #(path will be extension added onto variable element path)
        trans_meas_path = [str(i) for i in rel_meas_df['Transport Processes Variable Measurements'].tolist() if i]
        trans_meas = [str(i) for i in rel_meas_df['Transport Processes ISA Measurement Name'].tolist() if i]
        meas_attr = [str(i) for i in rel_meas_attr_df['Transport Processes Variable Measurement Attributes'].tolist()
                     if i]
        meas_header_begin = [str(i) for i in rel_meas_attr_df['Transport Processes ISA Entity Beginning'].tolist()]
        meas_header_tail = [str(i) for i in rel_meas_attr_df['Transport Processes ISA Entity Tail'].tolist()]
        tp_meas_paths = {}
        for j in range(len(trans_meas)):
            tp_meas_paths['Parameter Value[' + trans_meas[j] + ']'] = trans_meas_path[j]
            for k in range(len(meas_attr)):
                tp_meas_paths[meas_header_begin[k] + trans_meas[j] + meas_header_tail[k]] = trans_meas_path[j] + '[@' + meas_attr[k] + ']'

        var_paths = [tree.getelementpath(x).split('/', 2)[2] for x in var_elems]
        # Match row index to appropriate base xPath and ID number
        tp_path_base_ID = {}
        ind_cnt = 0
        for i, sample in enumerate(elem_dict.keys()):
            sample_base = pheno_data_paths[sample]
            for j, var in enumerate(elem_dict[sample]):
                var_base = '/'.join([sample_base, var_paths[j]])
                tp_path_base_ID[ind_cnt] = var_base
                ind_cnt += 1
        # Write content to correct xPaths
        for row_ind in df.index:
            var_base = tp_path_base_ID[row_ind]
            for col in df:
                #Write variable attributes
                if 'Variable' in col:
                    rel_ind = rel_var_df['Transport Processes ISA Variable Headers'][rel_var_df['Transport Processes ISA Variable Headers'] == col].index[0]
                    var_attr = str(rel_var_df.at[rel_ind, 'Transport Processes Variable Attributes'])
                    path_to_write = var_base + '[@' + var_attr + ']'
                    val_to_write = str(df.at[row_ind, col])
                    write_by_xPath(path_to_write, val_to_write)
                #write measurement and measurement attributes under the variable
                else:
                    path_tail = tp_meas_paths[col]
                    path_to_write = var_base + path_tail
                    val_to_write = str(df.at[row_ind, col])
                    write_by_xPath(path_to_write, val_to_write)

    #Need to write phenotypes
    for sample in phenotype_type_dict:
        val_path = pheno_data_paths[sample] + '/phenotype[@type]'
        val_to_write = phenotype_type_dict[sample]
        write_by_xPath(val_path, val_to_write)

    if 'CellCycle' in exist_assay_names:
        CellCycleAssay(df= cellcycle_df, elem_dict= exist_cycle_dict, model_elems= cycle_model_elems, phase_elems= cycle_phase_elems)
    if 'CellDeath' in exist_assay_names:
        CellDeathAssay(df = celldeath_df, elem_dict = exist_death_dict, death_type_elems= death_type_elems)
    if 'ClinicalStain' in exist_assay_names:
        ClinicalStainAssay(df = clinstain_df, stain_path_def = stain_def, stain_meas_path = stain_meas)
    if 'GeometricalProperties' in exist_assay_names:
        GeoPropsAssay(df = geoprops_df, elem_dict = exist_geoprops_dict, cellpart_elems = geo_cellpart_elems, subpart_elems = geo_subpart_elems)
    if 'Mechanics' in exist_assay_names:
        MechanicsAssay(df = mechanics_df, elem_dict = exist_mechanics_dict, cellpart_elems = mech_cellpart_elems, subpart_elems = mech_subpart_elems)
    if 'Microenvironment' in exist_assay_names:
        MicroenvironmentAssay(df = micro_df, sample_list = exist_micro_samples, var_names = micro_var_names, var_elems = micro_var_elems)
    if 'Motility' in exist_assay_names:
        MotilityAssay(df = motility_df, elem_dict= all_mot_dict, unrestrict_elem = unrestrict_elems, restrict_elem = restrict_elems)
    if 'PKPD' in exist_assay_names:
        pkpdAssay(df = PKPD_df)
    if 'StateTransition' in exist_assay_names:
        StateTransitionAssay(df = statetrans_df, pheno_collect_dict = pheno_collect_dict, state_cond_dict = state_cond_dict)
    if 'TransportProcesses' in exist_assay_names:
        TransportProcessAssay(df = transport_df, elem_dict = exist_transprocess_dict, var_elems = transport_process_elems)

    #Purge tree of attributes with no value and elements with no text values/attribute values/children with values

    #delete attribute keys that have no value
    for child in root.iter():
        if len(child.attrib) > 0:
            for key in child.attrib:
                if len(child.attrib[key]) == 0:
                  del child.attrib[key]

    #while loop: Ends when the number of elements does not change from iteration to iteration (there is nothing to remove)
    # 0 <= level_ind < 15 used as "safety stop" - will stop after 15 iterations instead of looping forever
    #Deletion criteria: if all are true, remove element from tree
    #   type(child.text) != str or len(child.text.strip()) == 0 : element has no text (either closed tag or only space in text)
    #   len(child.attrib) == 0  : element has no attributes (attributes with no value were removed)
    #   len(child) == 0  : element has no children of its own
    num_children_list = []
    level_ind = 0
    while 0 <= level_ind < 15:
        #print('Level: ',level_ind)
        num_children = 0
        for child in root.iter():
            num_children += 1
            if ((type(child.text) != str) or (len(child.text.strip()) == 0)) & (len(child.attrib) == 0) & (len(child) == 0):
                child.getparent().remove(child)
        #print('Children: ', num_children)
        if num_children in num_children_list:
            break
        else:
            num_children_list.append(num_children)
            level_ind += 1

    #TODO - fix tabbing, write <elem> \n text \n <elem> for elem with text and attributes
    print(DCL_xml_dir)
    print(ISA_file_base)
    conv_DCL = os.path.join(DCL_xml_dir, 'MCDS Conversion Output', ISA_file_base + '_converted.xml')
    #print(conv_DCL)
    # from xml.dom import minidom
    # xmlstr = minidom.parseString(etree.tostring(root).toprettyxml(indent="   "))
    # xmlstr = etree.tostring(tree, encoding="UTF-8", pretty_print=True)
    with open(conv_DCL, 'wb') as f_xml:
        tree.write(f_xml, pretty_print = True, xml_declaration = True, encoding = "utf-8")
    # print(conv_DCL)
    # tree.write(conv_DCl_path, pretty_print = True)


