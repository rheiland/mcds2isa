# mcds_entity_list.py - look through all DCL's in MCDS folder, generate xlsx file with all tags/xPath's
# Used to determined complete list of DCL elements and attributes used in existing DCL's

# Input:
#   Folder containing MCDS-DCL xml files: ...\MCDS_2_ISATab\All_Digital_Cell_Lines
#   At time of script creation, MCDS-DCL #001-237 are included (numbering is not continuous)
# Output:
#   1 Excel File containing MCDS tags:   MCDS_DCL_All_Entities.xlsx

# Author: Connor Burns
# Date:
#   v0.1 - Feb 2021: Initial working script
#   v0.2 - Feb 2021: Made writing to excel file more compact, added writing child.keys
#   v0.3 - Feb 2021: Added separations for elements
#   v0.4 - Mar 2021: Added separate column containing xPath with indices, changed getpath to getelementpath (provides
#                   callable xPath without root), added column for multiple vs single values
import os
from lxml import etree
import pandas as pd
import re
from tqdm import tqdm
import sys

os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))
cwd = os.getcwd()

DCL_xml_dir = os.path.join(os.path.dirname(cwd), 'All_Digital_Cell_Lines')
# DCL_xml_dir = (r'...<enter local path>...\MCDS_2_ISATab\All_Digital_Cell_Lines')
# Other user: remove line 21-23 and use line 24
DCL_list = os.listdir(DCL_xml_dir)
Obsolete_DCL = ['MCDS_L_0000000001.xml','MCDS_L_0000000002.xml','MCDS_L_0000000043.xml'
                ,'MCDS_L_0000000045.xml','MCDS_L_0000000046.xml']
DCL_list = [os.path.join(DCL_xml_dir,DCL) for DCL in DCL_list if DCL not in Obsolete_DCL]

column_names = ["MCDS Entity", "xPath", "xPath - Index Removed", "File Name", "Entity Type"]
# Define column names
df = pd.DataFrame(columns=column_names)
# Create empty Pandas dataframe
parser = etree.XMLParser(remove_comments=True)
# Parse XML tree and remove comments

# Loop through all XML files in All_Digital_Cell_Lines folder, get tag + xPath of each element, classify element
for XML_FileName in tqdm(DCL_list, desc= 'DCL File Processing:', total=len(DCL_list)):
    tree = etree.parse(os.path.join(DCL_xml_dir, XML_FileName), parser=parser)
    root = tree.getroot()

    for child in root.iter():
        #Entity type will be text if it has text and attributes
        if (type(child.text) == str and len(child.text.strip()) > 0):
            df = df.append(pd.Series([child.tag, tree.getelementpath(child), re.sub(r"\[[0-9]]", "", tree.getelementpath(child)), os.path.basename(XML_FileName), "Text Element"],
                                     index=df.columns), ignore_index=True)
            if len(child.keys()) > 0:
                for attr in child.keys():
                    df = df.append(pd.Series([attr,(tree.getelementpath(child) + "[@" + attr + "]"),("".join([re.sub(r"\[[0-9]]", "", tree.getelementpath(child)), "[@",attr,"]"])),
                                          os.path.basename(XML_FileName), "Attribute"], index=df.columns), ignore_index=True)
                #Write tags and xPaths of elements that contain text
        #Entity type will be attribute element if it only has attributes
        elif len(child.keys()) > 0:
            df = df.append(pd.Series([child.tag, tree.getelementpath(child), re.sub(r"\[[0-9]]", "", tree.getelementpath(child)), os.path.basename(XML_FileName), "Attribute Element"],
                                    index=df.columns), ignore_index=True)
                #Write tags and xPaths of elements that have attributes
            for attr in child.keys():
                df = df.append(pd.Series([attr,(tree.getelementpath(child) + "[@" + attr + "]"),("".join([re.sub(r"\[[0-9]]", "", tree.getelementpath(child)), "[@",attr,"]"])),
                                          os.path.basename(XML_FileName), "Attribute"], index=df.columns), ignore_index=True)
            # Append all MCDS attributes for child, xPath, xPath with indexing removed, and XML file to list
        #Entity type is parent if it has no text and no attributes, but has children
        elif ((type(child.text) == str) and len(child.text.strip()) == 0):
            df = df.append(pd.Series([child.tag, tree.getelementpath(child), re.sub(r"\[[0-9]]", "", tree.getelementpath(child)), os.path.basename(XML_FileName), "Parent Element"],
                              index=df.columns), ignore_index=True)
                #Parent - contains only children, no direct text or attribute

        #Entity type is closed if it has no child, no text, and no attributes
        else:
            df = df.append(pd.Series([child.tag, tree.getelementpath(child), re.sub(r"\[[0-9]]", "", tree.getelementpath(child)), os.path.basename(XML_FileName), "Closed Tag"],
                                     index=df.columns), ignore_index=True)

#Write multiple to new column if xPath contains indexing, write single if xPath does not contain indexing
df.loc[df['xPath'].str.contains(r"\[[0-9]]"), 'Multiple or Single'] = 'Multiple'
df.loc[~df['xPath'].str.contains(r"\[[0-9]]"), 'Multiple or Single'] = 'Single'

writer = pd.ExcelWriter('MCDS_DCL_All_Entities.xlsx')
#write all content to excel sheet
df.to_excel(writer, sheet_name='All Entities')

#remove parent and closed tags, remove duplicates of xPath within file, write columns except xPath with index to excel sheet
df = df[(df.loc[:,'Entity Type'] != 'Parent Element') & (df.loc[:,'Entity Type'] != 'Closed Tag')]
df = df.drop_duplicates(subset=['xPath - Index Removed', 'File Name'])
df.to_excel(writer, sheet_name='Unique Entities in Files', columns=["MCDS Entity", "xPath - Index Removed", "File Name", "Entity Type", 'Multiple or Single'])

#Remove duplicates of rows which have xPath and entity type that repeats
df2 = df.copy(deep=True)
df2 = df2.drop_duplicates(subset=['xPath - Index Removed', 'Entity Type'])

#TODO - Can this be vectorized to speed up?
#For each unique entity, write Multiple or Single as multiple if the entity is ever a multiple in the dataframe (for all files)
#Since there can be multiple phenotype datasets, any entities under phenotype_dataset will be multiple by default
for ind in df2.index:
    if df2.at[ind,'Multiple or Single'] == 'Single':
        if 'cell_line/phenotype_dataset' in df2.at[ind,'xPath - Index Removed']:
            df2.at[ind, 'Multiple or Single'] = 'Multiple'
        else:
            mult_series = df.loc[(df['xPath - Index Removed'] == df2.at[ind,'xPath - Index Removed']) & (df['Entity Type'] == df2.at[ind, 'Entity Type'])]['Multiple or Single']
            if 'Multiple' in mult_series.values:
                df2.at[ind, 'Multiple or Single'] = 'Multiple'

df2.to_excel(writer, sheet_name='Unique Attr and Text Elem', columns=["MCDS Entity", "xPath - Index Removed", "File Name", "Entity Type", 'Multiple or Single'])
writer.save()
