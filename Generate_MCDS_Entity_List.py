# Author: Connor Burns and Corey Chitwood
# Date:
#   v0.1 - Feb 2021: Initial working script
#   v0.2 - Feb 2021: Made writing to excel file more compact, added writing child.keys
#   v0.3 - Feb 2021: Added separations for elements
#   v0.4 - Feb 2021: Modifying script for use with Digital Snapshots
#   v0.5 - Feb 2021: Removing repetitive xpaths from .xml files before proceeding to minimize runtime

import os
from lxml import etree
import pandas as pd
import re

os.chdir(r'C:\Users\Corey\PyCharmProjects\mcds2isa')
cwd = os.getcwd()
# Define Path for XML Directory
DSS_xml_dir = r'C:\Users\Corey\PycharmProjects\mcds2isa\All_Digital_Snapshots'

column_names = ["MCDS Entity", "xPath", "File Name", "Entity Type"]
# Define column names
df = pd.DataFrame(columns=column_names)
# Create empty Pandas dataframe
parser = etree.XMLParser(remove_comments=True)
# Parse XML tree and remove comments

# Loop through all XML files in All_Digital_Snapshots folder
# Due to large numbers of cells captured in a Snapshot file, need to remove repetitive .../cell xPaths in order to create
# an excel file (.xlsx was exceeding max number of rows) and to reduce time required to run script (was taking >10 hours)


with os.scandir(DSS_xml_dir) as directory: #scans folder to create file directory
    print('Gathering File Entities')
    for XML_FileName in directory: #loops through each file in directory
        tree = etree.parse(os.path.join(DSS_xml_dir, XML_FileName), parser=parser)
        root = tree.getroot()
        print(XML_FileName)
        for child in root.iter(): #iterates through each tag within XML_FileName
            '''if 'CHEBI_ID' in child.attrib:
                print(XML_FileName, 'has the receptor entity')
                break'''
            if 'ID' in child.attrib: #breaks for child in root.iter(): loop and progresses to next file if Cell ID > 1
                if int(child.attrib.get('ID')) > 1: #Accounts for unique xPaths, without excessive redundancy
                    print('Break in File')
                    break


            #writes entity/xpath to df depending on its type
            if type(child.text) == str:
                if len(child.text.strip()) > 0:
                    df = df.append(pd.Series([child.tag, re.sub(r"\[[0-9]]", "", tree.getpath(child)), XML_FileName, "Text Element"],
                                         index=df.columns), ignore_index=True)
                    #contains text
                elif len(child.keys()) > 0:
                    df = df.append(pd.Series([child.tag, re.sub(r"\[[0-9]]", "", tree.getpath(child)), XML_FileName, "Attribute Element"],
                                        index=df.columns), ignore_index=True)
                    #contains attributes
                else:
                    df = df.append(pd.Series([child.tag, re.sub(r"\[[0-9]]", "", tree.getpath(child)), XML_FileName, "Parent Element"],
                                  index=df.columns), ignore_index=True)
                    #contains only children, no direct text or attribute
                for attr in child.keys():
                    df = df.append(pd.Series([attr, ("".join([re.sub(r"\[[0-9]]", "", tree.getpath(child)), "[@",attr,"]"])),
                                              XML_FileName, "Attribute"], index=df.columns), ignore_index=True)

            #if no text in tag, it is a closed tag, but is still appended to df
            else:
                df = df.append(pd.Series([child.tag, re.sub(r"\[[0-9]]", "", tree.getpath(child)), XML_FileName, "Closed Tag"],
                                         index=df.columns), ignore_index=True)
#write to excel file
df.to_excel('MCDS_DSS_All_Entities.xlsx')

print('Finished. Excel file should be available in defined path.')