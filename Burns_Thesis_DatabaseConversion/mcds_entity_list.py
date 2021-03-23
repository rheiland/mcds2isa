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

os.chdir(r'C:\Users\Connor\PycharmProjects\MCDS_2_ISATab\Burns_Thesis_DatabaseConversion')
cwd = os.getcwd()
DCL_xml_dir = os.path.join(cwd[:-32], 'All_Digital_Cell_Lines')
# DCL_xml_dir = (r'...<enter local path>...\MCDS_2_ISATab\All_Digital_Cell_Lines')
# Other user: remove line 21-23 and use line 24
DCL_list = os.listdir(DCL_xml_dir)

column_names = ["MCDS Entity", "xPath", "xPath - Index Removed", "File Name", "Entity Type"]
# Define column names
df = pd.DataFrame(columns=column_names)
# Create empty Pandas dataframe
parser = etree.XMLParser(remove_comments=True)
# Parse XML tree and remove comments

# Loop through all XML files in All_Digital_Cell_Lines folder, get tag + xPath of each element, classify element
for XML_FileName in DCL_list:
    tree = etree.parse(os.path.join(DCL_xml_dir, XML_FileName), parser=parser)
    root = tree.getroot()
    for child in root.iter():
        if type(child.text) == str:
            if len(child.text.strip()) > 0:
                df = df.append(pd.Series([child.tag, tree.getelementpath(child), re.sub(r"\[[0-9]]", "", tree.getelementpath(child)), XML_FileName, "Text Element"],
                                     index=df.columns), ignore_index=True)
                #Write tags and xPaths of elements that contain text
            elif len(child.keys()) > 0:
                df = df.append(pd.Series([child.tag, tree.getelementpath(child), re.sub(r"\[[0-9]]", "", tree.getelementpath(child)), XML_FileName, "Attribute Element"],
                                    index=df.columns), ignore_index=True)
                #Write tags and xPaths of elements that have attributes
            else:
                df = df.append(pd.Series([child.tag, tree.getelementpath(child), re.sub(r"\[[0-9]]", "", tree.getelementpath(child)), XML_FileName, "Parent Element"],
                              index=df.columns), ignore_index=True)
                #Parent - contains only children, no direct text or attribute
            for attr in child.keys():
                df = df.append(pd.Series([attr,(tree.getelementpath(child) + "[@" + attr + "]"),("".join([re.sub(r"\[[0-9]]", "", tree.getelementpath(child)), "[@",attr,"]"])),
                                          XML_FileName, "Attribute"], index=df.columns), ignore_index=True)
            # Append all MCDS attributes for child, xPath, xPath with indexing removed, and XML file to list
        else:
            df = df.append(pd.Series([child.tag, tree.getelementpath(child), re.sub(r"\[[0-9]]", "", tree.getelementpath(child)), XML_FileName, "Closed Tag"],
                                     index=df.columns), ignore_index=True)

#Write multiple to new column if xPath contains indexing, write single if xPath does not contain indexing
df.loc[df['xPath'].str.contains(r"\[[0-9]]"), 'Multiple or Single'] = 'Multiple'
df.loc[~df['xPath'].str.contains(r"\[[0-9]]"), 'Multiple or Single'] = 'Single'

df.to_excel('MCDS_DCL_All_Entities.xlsx')
