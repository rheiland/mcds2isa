# mcds_entity_list.py - look through all DCL's in MCDS folder, generate xlsx file with all tags/xPath's
# Used to determined semi-complete list of possible DCL unique tags.
# User should remove duplicate rows from xlsx file after generating

# Input:
#   MCDS-DCL xml files in MCDS_2_ISATab\All_Digital_Cell_Lines
#   At time of script creation, MCDS-DCL #001-237 are included (numbering is not continuous)
# Output:
#   1 Excel File containing MCDS tags:   MCDS_DCL_All_Tags.xlsx

# Author: Connor Burns
# Date:
#   v0.1 - Feb 2020: Initial working script
#   v0.2 - Feb 2020: Made writing to excel file more compact, added writing child.keys

import os
from lxml import etree
import pandas as pd
import re

os.chdir(r'C:\Users\Connor\PycharmProjects\MCDS_2_ISATab\Burns_Thesis_DatabaseConversion')
cwd = os.getcwd()
# TODO - Only works if cwd is set to directory in line 21 - update later for other users?
DCL_xml_dir = os.path.join(cwd[:-32], 'All_Digital_Cell_Lines')
# DCL_xml_dir = (r'...<enter local path>...\MCDS_2_ISATab\All_Digital_Cell_Lines')
DCL_list = os.listdir(DCL_xml_dir)

column_names = ["MCDS Entity", "xPath", "File Name", "Entity Type"]
# Define column names
df = pd.DataFrame(columns=column_names)
# Create empty Pandas dataframe
parser = etree.XMLParser(remove_comments=True)
# Parse XML tree and remove elements that are comments

for XML_FileName in DCL_list:
    # Loop through all XML files in All_Digital_Cell_Lines folder
    tree = etree.parse(os.path.join(DCL_xml_dir, XML_FileName), parser=parser)
    root = tree.getroot()
    for child in root.iter():
        df = df.append(pd.Series([child.tag, re.sub(r"\[[0-9]]", "", tree.getpath(child)), XML_FileName, "Element"],
                                 index=df.columns), ignore_index=True)
        # Append all MCDS tags from file, xPath with indexing removed, and XML file to list
        for attr in child.keys():
            df = df.append(pd.Series([attr, ("/".join([re.sub(r"\[[0-9]]", "", tree.getpath(child)), attr])),
                                      XML_FileName, "Attribute"], index=df.columns), ignore_index=True)
            # Append all MCDS attributes for child, xPath with indexing removed, and XML file to list

df.to_excel('MCDS_DCL_All_Entities.xlsx')
