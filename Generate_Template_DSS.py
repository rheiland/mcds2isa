#script is messy, but contains each individual step used to create a template MCDS DSS merged into one script
#if creating a new template DSS, may be best to heavily modify this script or separate it into component parts
#was a relatively inefficient process, but managed to generate a clean DSS without too much trouble

#general process
#1. determine which existing snapshots contain all possible tags
#2. clean all data from that DSS
#3. manually edited DSS to ensure proper spacing (as all '\n' and '\t' characters were removed as well
#4. determined maximum number of cell tags of all snapshots in repository
#5. used script to 'copy and paste' cell tags and child tags to account for max number of cells


'''
import os
import sys
import re
import pandas as pd
from lxml import etree

os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))
cwd = os.getcwd()
db = os.path.join(cwd, 'All_Tags.xlsx')
#Define Master database directory path - assumes that database is in same folder as script
DSS_folder = os.path.join(cwd, 'All_Digital_Snapshots')
column_names = ['all xpath','found xpath','missing xpath','filename','complete files']
dirty_DSS = os.path.join(cwd,'Dirty_DSS.xml')
current_DSS = os.path.join(cwd,'Current_Clean_DSS.xml')
print(current_DSS)

df_out = pd.DataFrame(columns=column_names)
i=-1

#this section was used to determine which DSS contained all tags
'''


'''
with os.scandir(DSS_folder) as DSS_list:
    for DSS_in in DSS_list:
        list = []
        i = i + 1
        print(DSS_in)
        parser = etree.XMLParser(remove_comments=True)
        tree = etree.parse(os.path.join(DSS_folder, DSS_in), parser=parser)
        root = tree.getroot()
        df = pd.read_excel(rF'{db}', sheet_name='Sheet1',usecols=['MCDS Entity','xPath'])
        for df_row in df.index:
            entity = df.at[df_row,'MCDS Entity']
            xpath = df.at[df_row,'xPath']
            searching = root.find(xpath)
            if searching is None:
                df_out.at[df_row + len(df.index)*i,'missing xpath'] = xpath
            else:
                list.append(xpath)
        if len(df.index) == len(list):
            df_out.at[i,'complete files'] = DSS_in
df_out.to_excel('Generate Clear DSS.xlsx')
'''

#FROM THIS SCRIPT IT WAS DETERMINED THAT MCDS_S_0000000089 was the lowest number file that contained all possible tags
#From here, the script will clean this DSS of all data

#This section was used to remove all data from tags and attributes
'''parser = etree.XMLParser(remove_comments=True)
tree = etree.parse(dirty_DSS, parser=parser)
root = tree.getroot()
for child in root.iter():
    if len(child.attrib) > 0:
        for attr in child.attrib:
            child.set(attr,'')
    if type(child.text) == str:
        if len(child.text) > 0:
            child.text = ''
tree.write('Clean_DSS.xml')
'''

#from here, manually edited .xml file to the correct formatting and manually closed tags


#then determined the maximum number of

'''with os.scandir(DSS_folder) as DSS_list:
    list = []
    for DSS_in in DSS_list:
        i = i + 1
        parser = etree.XMLParser(remove_comments=True)
        tree = etree.parse(os.path.join(DSS_folder, DSS_in), parser=parser)
        root = tree.getroot()
        #print(len(root.findall('cellular_information/cell_populations/cell_population/cell[@ID]')))
        list.append(len(root.findall('cellular_information/cell_populations/cell_population/cell[@ID]')))
    print(max(list))
'''

#determined that max occurances of xpath 'cellular_information/cell_populations/cell_population/cell[@ID]' is 1132
#means that template should repeat this tag + children 1132 times
#can clear any empty tags afterwards

'''copy_paste = os.path.join(cwd,'copypaste.txt')
paste = os.path.join(cwd,'paste.txt')
f = open(copy_paste,'r')
lines = f.readlines()
f.close()
f = open(paste,'w')
for i in range(1132):
    for j in range(len(lines)):
        f.write(lines[j])
    f.write('\n')
f.close()
f = open(paste,'r')
pasted_lines = f.readlines()
if len(pasted_lines) != 1132*len(lines):
    print('error')
f.close()'''