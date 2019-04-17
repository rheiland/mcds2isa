#
# mcds_dcl2isa.py - using a MultiCellDS digital cell line XML file, generate associated ISA-Tab files
#
# Input:
#   a MultiCellDS digital cell line file  <DCL-root-filename>.xml
# Output:
#   3 ISA files:
#    i_<DCL-root-filename>.txt
#    s_<DCL-root-filename>.txt
#    a_<DCL-root-filename>.txt
#
# Author: Randy Heiland
# Date:
#   v0.1 - May 2018
#   v0.2 - Oct 2018 : add more tab sep_char in various rows
# 

import os
import sys
import re
import xml.etree.ElementTree as ET
from pathlib import Path  # Python 3?

if (len(sys.argv) < 2):
  print("Usage: " + sys.argv[0] + " <MultiCellDS Digital Cell Line XML file>")
  sys.exit(0)
else:
  xml_file = sys.argv[1]

# for testing, just set it
#xml_file = "MCDS_L_0000000052.xml"

dqte = '"'

header = '\
ONTOLOGY SOURCE REFERENCE\n\
Term Source Name	"NCIT"	"UO"	"NCBITAXON"	"EDDA"\n\
Term Source File	"https://ncit.nci.nih.gov/ncitbrowser/"	"https://bioportal.bioontology.org/ontologies/UO"	"http://purl.obolibrary.org/obo/NCBITaxon_1"	"http://bioportal.bioontology.org/ontologies/EDDA"\n\
Term Source Version	"17.02d"	""	""	"2.0"\n\
Term Source Description	"NCI Thesarus"	""	""	"Evidence in Documents, Discovery, and Analytics (EDDA)"\
'

if not Path(xml_file).is_file():
	print(xml_file + 'does not exist!')
	sys.exit(-1)

if (os.sep in xml_file):
  xml_base_filename = xml_file[xml_file.rfind(os.sep)+1:]
else:
  xml_base_filename = xml_file

investigation_filename = "i_" + xml_base_filename[:-4] + ".txt"
study_filename = "s_" + xml_base_filename[:-4] + ".txt"
assay_filename = "a_" + xml_base_filename[:-4] + ".txt"

#=======================================================================
fp = open(investigation_filename, 'w')

tree = ET.parse(xml_file)  # TODO: relative path using env var?
xml_root = tree.getroot()

sep_char = '\t'  # tab

fp.write(header + '\n')
fp.write('INVESTIGATION\n')
#print(xml_root.find(".//MultiCellDB").find(".//ID").text)
i_identifier = '"' + xml_root.find(".//metadata").find(".//ID").text + '"'
#i_title = '"' + xml_root.find(".//metadata").find(".//name").text + '"'
i_title = '"' + xml_root.find(".//metadata").find(".//name").text + ' Digital Cell Line"'
i_desc = '"' + xml_root.find(".//metadata").find(".//description").text + '"'
i_desc = re.sub('\t','',i_desc)
i_desc = re.sub('\n','',i_desc)
fp.write('Investigation Identifier' + sep_char + i_identifier + '\n')
fp.write('Investigation Title' + sep_char +  i_title + '\n')
fp.write('Investigation Description' + sep_char + i_desc + '\n')
fp.write('Investigation Submission Date' + sep_char + '""\n')
fp.write('Investigation Public Release Date \t "" \n') 
citation_str = '"' + re.sub('[\t\n]','',xml_root.find(".//citation").find(".//text").text) + '"'  # remove all tabs and newlines 
fp.write('Comment [MultiCellDS/cell_line/metadata/citation/text]' + sep_char + citation_str + '\n')

# TODO: check that "citation" exists first?
if (xml_root.find(".//citation").find(".//notes")):
  fp.write('Comment [MultiCellDS/cell_line/metadata/citation/notes]' + sep_char + xml_root.find(".//citation").find(".//notes").text  + '\n')
  

fp.write('INVESTIGATION PUBLICATIONS\n')
# Extract over all <PMID> in <data_origin> and <data_analysis>
#print('Investigation PubMed ID	"21988888"	"23084996"	"22342935" ' )
# Extract <PMID> and <DOI> in all <data_origin> and <data_analysis>
# TODO? will we have matching # of each?
pmid = []
doi = []
url = []
uep = xml_root.find('.//data_origins')  # uep = unique entry point
for elm in uep.findall('data_origin'):
#    doi.append(elm.find('.//DOI').text)
    doi_ptr = elm.find('.//DOI')
    if (doi_ptr == None):
      doi_value = ""
    else:
      doi_value = doi_ptr.text
    doi.append(doi_value)  # do we want to append "" if none??

#    pmid.append(elm.find('.//PMID').text)
    pmid_ptr = elm.find('.//PMID')
    if (pmid_ptr == None):
      pmid_value = ""
    else:
      pmid_value = pmid_ptr.text
      pmid.append(pmid_value)
#    pmid.append(pmid_value)

    url_ptr = elm.find('.//URL')
    if (url_ptr == None):
      url_value = ""
    else:
      url_value = url_ptr.text
      url.append(url_value)

#print("(post data_origin) pmid=",pmid)
#print("(post data_origin) url=",url)

uep = xml_root.find('.//metadata')
for elm in uep.findall('data_analysis'):
#    print(' "' + el.find('.//PMID').text + '"', end='')
#  doi.append(elm.find('.//DOI').text)
#  pmid.append(elm.find('.//PMID').text)
  doi_ptr = elm.find('.//DOI')
  if (doi_ptr == None):
    doi_value = ""
  else:
    doi_value = doi_ptr.text
  doi.append(doi_value)  # do we want to append "" if none??

#    pmid.append(elm.find('.//PMID').text)
  pmid_ptr = elm.find('.//PMID')
  if (pmid_ptr == None):
    pmid_value = ""
  else:
    pmid_value = pmid_ptr.text
    pmid.append(pmid_value)
#  pmid.append(pmid_value)

#print("(post data_analysis) pmid=",pmid)

sep_char_sq = sep_char + '"'   # tab + single quote

pmid_str = ''
for elm in pmid:
  pmid_str += sep_char + '"' + elm + '"'
fp.write('Investigation PubMed ID' + sep_char + pmid_str + '\n')

doi_str = ''
for elm in doi:
  doi_str += sep_char + '"' + elm + '"'
fp.write('Investigation Publication DOI' + sep_char + doi_str + '\n')

empty_str = ''.join(sep_char + '""' for x in pmid) 
fp.write('Investigation Publication Author List' + sep_char + empty_str + '\n')
fp.write('Investigation Publication Title' + sep_char + empty_str + '\n')

pub_status_str = ''.join('\t"Published"' for x in pmid) 
pub_title_str = ''.join('\t""' for x in pmid) 
fp.write('Investigation Publication Status' + sep_char + pub_status_str + '\n')
pub_status_TA_str = ''.join('\t"C19026"' for x in pmid) 
fp.write('Investigation Publication Status Term Accession' + sep_char + pub_status_TA_str + '\n')
pub_status_TSR_str = ''.join('\t"NCIT"' for x in pmid) 
fp.write('Investigation Publication Status Term Source REF' + sep_char + pub_status_TSR_str + '\n')

fp.write('INVESTIGATION CONTACTS\n') 
fp.write('Investigation Person Last Name' + sep_char_sq + xml_root.find(".//current_contact").find(".//family-name").text + '"\t\n') 
fp.write('Investigation Person First Name' + sep_char_sq + xml_root.find(".//current_contact").find(".//given-names").text + '"\n') 
fp.write('Investigation Person Mid Initials' + sep_char + '""\n')
fp.write('Investigation Person Email' +  sep_char_sq + xml_root.find(".//current_contact").find(".//email").text + '"\n') 
fp.write('Investigation Person Phone' + sep_char +  '""\n')
fp.write('Investigation Person Fax' + sep_char +  '""\n')
fp.write('Investigation Person Address'  + sep_char +  '""\n')
fp.write('Investigation Person Affiliation' + sep_char_sq + xml_root.find(".//current_contact").find(".//organization-name").text + 
            ', ' + xml_root.find(".//current_contact").find(".//department-name").text + '"\n') 
fp.write('Investigation Person Roles' + sep_char +  '""\n')
fp.write('Investigation Person Roles Term Accession Number' + sep_char + '""\n')
fp.write('Investigation Person Roles Term Source REF' + sep_char + '""\n')
fp.write('Comment[Investigation Person REF]' + sep_char + '""\n')


fp.write('STUDY\n')
fp.write('Study Identifier\t' + i_identifier + '\n')
fp.write('Study Title\t' + i_title + '\n')
fp.write('Study Description\t' + i_desc + '\n')
fp.write('Comment[Study Grant Number]\t""\n')
fp.write('Comment[Study Funding Agency]\t""\n')
fp.write('Study Submission Date\t""\n')
fp.write('Study Public Release Date\t""\n')
fp.write('Study File Name\t' + '"' + study_filename + '"\n')


fp.write('STUDY DESIGN DESCRIPTORS\n')
fp.write('Study Design Type\t""\n')
fp.write('Study Design Type Term Accession Number\t""\n')
fp.write('Study Design Type Term Source REF\t""\n')

# TODO? are these different than the previous pubs?
fp.write('STUDY PUBLICATIONS\n')
fp.write('Study PubMed ID' + sep_char + pmid_str + '\n')
fp.write('Study Publication DOI' + sep_char + doi_str + sep_char + '\n')
fp.write('Study Publication Author List' + sep_char + empty_str + '\n')
fp.write('Study Publication Title' + sep_char + pub_title_str + '\n')
fp.write('Study Publication Status' + sep_char + pub_status_str + sep_char + '\n')
fp.write('Study Publication Status Term Accession Number' + sep_char + pub_status_TA_str + sep_char + '\n')
fp.write('Study Publication Status Term Source REF' + sep_char + pub_status_TSR_str + '\n')


fp.write('STUDY FACTORS' + 3*sep_char + '\n')
fp.write('Study Factor Name\t"phenotype_dataset"\n')
fp.write('Study Factor Type\t""\n')
fp.write('Study Factor Type Term Accession Number\t""\n')
fp.write('Study Factor Type Term Source REF\t""\n')
#fp.write('Comment[phenotype_dataset_keywords] "viable; hypoxic; physioxia(standard);  physioxia(breast); necrotic,chronic hypoxia"\n')
#fp.write('Comment[phenotype_dataset_keywords] "')
comment_str = 'Comment[phenotype_dataset_keywords]\t"'
uep = xml_root.find('.//cell_line')
for elm in uep.findall('phenotype_dataset'):
  comment_str += elm.attrib['keywords'] + '; '
#  print(comment_str)
fp.write(comment_str[:-2] + '"\n')

# TODO: fill these in with something meaningful
# fp.write('STUDY ASSAYS\t\n')
# fp.write('Study Assay Measurement Type\t"phenotype cell_cycle cell_cycle_phase duration"\n')
# fp.write('Study Assay Measurement Type Term Accession Number\t""\n')
# fp.write('Study Assay Measurement Type Term Source REF\t""\n')
# fp.write('Study Assay Technology Type\t"Digital Cell Line"\n')
# fp.write('Study Assay Technology Type Term Accession Number\t""\n')
# fp.write('Study Assay Technology Type Term Source REF\t""\n')
# fp.write('Study Assay Technology Platform\t""\n')
# fp.write('Study Assay File Name\t' + '"' + assay_filename + '"\n')


fp.write('STUDY PROTOCOLS\t\n')
fp.write('Study Protocol Name\t"microenvironment.measurement"\n')
fp.write('Study Protocol Type\t""\n')
fp.write('Study Protocol Type Term Accession Number\t""\n')
fp.write('Study Protocol Type Term Source REF\t""\n')
fp.write('Study Protocol Description\t""\n')
fp.write('Study Protocol URI\t""\n')
fp.write('Study Protocol Version\t""\n')
#fp.write('Study Protocol Parameters Name  "oxygen.partial_pressure; DCIS_cell_density(2D).surface_density; DCIS_cell_area_fraction.area_fraction; DCIS_cell_volume_fraction.volume_fraction"\n')
comment_str = 'Study Protocol Parameters Name\t"'
# TODO? search for all phenotype_dataset/microenvironment/domain/variables/...
uep = xml_root.find('.//variables')
if (uep):
  for elm in uep.findall('variable'):
    if ('type' in elm.attrib.keys()):  # TODO: what's desired format if 'type' is missing?
      comment_str += elm.attrib['name'] + '.' + elm.attrib['type'] + '; '
    else:
      comment_str += elm.attrib['name'] + '; '
#      comment_str += '; '
#  print(comment_str)
  fp.write(comment_str[:-2] + '"\n')

semicolon_sep_empty_str = ''.join('; ' for x in pmid)
fp.write('Study Protocol Parameters Name Term Accession Number\t" ' + semicolon_sep_empty_str + ' "\n')
fp.write('Study Protocol Parameters Name Term Source REF\t" ' + semicolon_sep_empty_str + ' "\n')
fp.write('Study Protocol Components Name\t"' + semicolon_sep_empty_str + ' "\n')
fp.write('Study Protocol Components Type\t"' + semicolon_sep_empty_str + ' "\n')
fp.write('Study Protocol Components Type Term Accession Number\t"' + semicolon_sep_empty_str + ' "\n')
fp.write('Study Protocol Components Type Term Source REF\t"' + semicolon_sep_empty_str + ' "\n')


fp.write('STUDY CONTACTS\t\n')
fp.write('Study Person Last Name\t"' + xml_root.find(".//current_contact").find(".//family-name").text + '"\n') 
fp.write('Study Person First Name\t"' + xml_root.find(".//current_contact").find(".//given-names").text + '"\n') 
fp.write('Study Person Mid Initials\t""\n')
fp.write('Study Person Email\t"' +  xml_root.find(".//current_contact").find(".//email").text + '"\n') 
fp.write('Study Person Phone\t""\n')
fp.write('Study Person Fax\t""\n')
fp.write('Study Person Address\t""\n')
fp.write('Study Person Affiliation\t"' +  xml_root.find(".//current_contact").find(".//organization-name").text + 
            ', ' + xml_root.find(".//current_contact").find(".//department-name").text + '"\n') 
fp.write('Study Person Roles\t""\n')
fp.write('Study Person Roles Term Accession Number\t""\n')
fp.write('Study Person Roles Term Source REF\t""\n')
fp.write('Comment[creator_orcid-id_family-name]\t"' + xml_root.find(".//creator").find(".//family-name").text + '"\n') 
fp.write('Comment[creator_orcid-id_given-names]\t"' + xml_root.find(".//creator").find(".//given-names").text + '"\n') 
fp.write('Comment[creator_orcid-id_email]\t"' + xml_root.find(".//creator").find(".//email").text + '"\n')
fp.write('Comment[creator_orcid-id_organization-name]\t"' +  xml_root.find(".//creator").find(".//organization-name").text + 
            ', ' + xml_root.find(".//creator").find(".//department-name").text + '"\n') 


#curator_ptr = xml_root.find(".//curator").find(".//family-name").text + '"\n') 
family_name = ""
given_names = ""
email = ""
org = ""
dept = ""

curator_ptr = xml_root.find(".//curator")
if (curator_ptr):
  family_name_ptr = curator_ptr.find(".//family-name")
  given_names_ptr = curator_ptr.find(".//given-names")
  email_ptr = curator_ptr.find(".//email")
  org_ptr = curator_ptr.find(".//organization-name")
  dept_ptr = curator_ptr.find(".//department-name")

  if (family_name_ptr):
    family_name = family_name_ptr.find(".//family-name").text 
  if (given_names_ptr):
    given_names = given_names_ptr.find(".//given-names").text 
  if (email_ptr):
    email = email_ptr.find(".//email").text 
  if (org_ptr):
    org = org_ptr.find(".//organization-name").text 
  if (dept_ptr):
    dept = dept_ptr.find(".//department-name").text 

#fp.write('Comment[curator_orcid-id_family-name]\t"' + xml_root.find(".//curator").find(".//family-name").text + '"\n') 
fp.write('Comment[curator_orcid-id_family-name]\t"' + family_name + '"\n') 

#fp.write('Comment[curator_orcid-id_given-names]\t"' + xml_root.find(".//curator").find(".//given-names").text + '"\n')
fp.write('Comment[curator_orcid-id_given-names]\t"' + given_names + '"\n')

#fp.write('Comment[curator_orcid-id_email]\t"' + xml_root.find(".//curator").find(".//email").text + '"\n')
fp.write('Comment[curator_orcid-id_email]\t"' + email + '"\n')

fp.write('Comment[curator_orcid-id_organization-name]\t"' +  org + ', ' +  dept + '"\n') 


fp.write('Comment[last_modified_by_orcid-id_family-name]\t"' + xml_root.find(".//last_modified_by").find(".//family-name").text + '"\n')
fp.write('Comment[last_modified_by_orcid-id_given-names]\t"' + xml_root.find(".//last_modified_by").find(".//given-names").text + '"\n')
fp.write('Comment[last_modified_by_orcid-id_email]\t"' + xml_root.find(".//last_modified_by").find(".//email").text + '"\n')
fp.write('Comment[last_modified_by_orcid-id_organization-name]\t"' +  xml_root.find(".//last_modified_by").find(".//organization-name").text + 
            ', ' + xml_root.find(".//last_modified_by").find(".//department-name").text + '"\n') 
fp.write('Comment[Study Person REF]' + sep_char + '""' + '\n')

fp.close()
print(' --> ' + investigation_filename)


#=======================================================================
""" example of column headers (12)
"Source Name"	"Comment[data_origin/citation]"	"Comment[data_origin/citation]"	"Comment[data_origin/citation]"	"Comment[data_origin/citation]"	
"Characteristics[BTO_ID]"	"Characteristics[CLO_ID]"	"Characteristics[species]"	"Characteristics[organ]"	"Characteristics[custom]"	
"Factor Value[phenotype_dataset]"	"Sample Name"
"""
fp_s = open(study_filename, 'w')

# ------- row #1 (column titles)
#fp.write('Source Name' + sep_char)
fp_s.write('"Source Name"' + sep_char)
source_name = i_identifier[1:-1] + '.0'

uep = xml_root.find('.//data_origins')  # uep = unique entry point
for elm in uep.findall('data_origin'):
  for elm2 in elm.findall('citation'):
    # fp_s.write('Comment[citation]' + sep_char)
    # fp_s.write('"Comment[citation]"' + sep_char)
    fp_s.write('"Comment[data_origin/citation]"' + sep_char)
    # TODO: why did I insert the following line?
    # pmid_origin = elm.find('.//PMID').text

uep = xml_root.find('.//metadata')
for elm in uep.findall('data_analysis'):
  for elm2 in elm.findall('citation'):
    # fp_s.write('Comment[citation]' + sep_char)
    # fp_s.write('"Comment[citation]"' + sep_char)
    # fp_s.write('"Comment[metadata/data_analysis/citation]"' + sep_char)
    print("--------> Need to do:  Comment[metadata/data_analysis/citation]")

uep = xml_root.find('.//cell_origin')
cell_origin_characteristics = []
if (uep):
  for elm in uep.getchildren():
    # fp_s.write('Characteristics[' + elm.tag + ']' + sep_char)
    fp_s.write('"Characteristics[cell_origin/' + elm.tag + ']"' + sep_char)
    text_val = elm.text
    text_val = ' '.join(text_val.split())   # strip out tabs and newlines
    cell_origin_characteristics.append(text_val)
#    print("cell_origin_characteristics----->",cell_origin_characteristics,"<-------")

print("cell_origin_characteristics----->",cell_origin_characteristics,"<-------")
#fp_s.write('Factor Value[phenotype_dataset]' + sep_char + 'Sample Name\n')
fp_s.write('"Factor Value[phenotype_dataset]"' + sep_char + '"Sample Name"\n')

#-------------------------------
# ------- remaining rows (after header; need to match the # of entries in each row with # entries in header)
uep = xml_root.find('.//cell_line')  # uep = unique entry point
#for pd_elm in uep.findall('phenotype_dataset'):
suffix = 0
for pd_elm in uep.findall('phenotype_dataset'):
  print("====> phenotype_dataset")
  row_str = dqte + source_name + dqte + sep_char 
  # row_str = ""
  fp_s.write(row_str)

  uep = xml_root.find('.//data_origins')  # uep = unique entry point
  for elm in uep.findall('data_origin'):
    for elm2 in elm.findall('citation'):
      cite_str = ""
      for cite in elm2.getchildren():
        text_val = cite.text
        text_val = ' '.join(text_val.split())   # strip out tabs and newlines
        text_val = text_val.replace('"', '')
        cite_str += str(text_val) + ','
      fp_s.write('"' + cite_str + '"' + sep_char)

  uep = xml_root.find('.//metadata')
  for elm in uep.findall('data_analysis'):
    for elm2 in elm.findall('citation'):
      # fp_s.write('Comment[citation]' + sep_char)
      # fp_s.write('"Comment[citation]"' + sep_char)
      # fp_s.write('"Comment[metadata/data_analysis/citation]"' + sep_char)
      print("---> Need row entry for: Comment[metadata/data_analysis/citation]")

  #uep = xml_root.find('.//cell_line')
  uep = xml_root.find('.//cell_origin')
  # suffix = 0
  #for elm in uep.findall('phenotype_dataset'):
  # for elm in uep.getchildren():
  #  row_str = dqte + source_name + dqte + sep_char 
    # do we want a hierarchy of preferred citation types? (e.g., PMID,PMCID,DOI,URL)
    # if (len(pmid) > 0):
    #   for p in pmid:
    #     row_str += '"PMID: ' + p + dqte + sep_char
    # elif (len(url) > 0):
    #   for p in url:
    #     row_str += '"URL: ' + p + dqte + sep_char

  #  print("cell_origin_characteristics=",cell_origin_characteristics)
    # for c in cell_origin_characteristics:
  row_str = ""
  for c in cell_origin_characteristics:
      row_str += dqte + c + dqte + sep_char 
    # row_str += dqte + elm.attrib['keywords'] + dqte + sep_char + dqte + source_name + '.' + str(suffix) + dqte
                
#     suffix += 1
  #  print(row_str)
    # fp_s.write(row_str + '\n')


  suffix += 1   # WHAT? just doing this causes invalid results in Metadata Utility???????
  row_str += dqte + pd_elm.attrib['keywords'] + dqte + sep_char + dqte + source_name + '.' + str(suffix) + dqte
  fp_s.write(row_str + '\n')

fp_s.close()
print(' --> ' + study_filename)


#=======================================================================
fp = open(assay_filename, 'w')
"""
Sample Name Protocol REF  Parameter Value[oxygen.partial_pressure]  Unit  Parameter Value[DCIS_cell_density(2D).surface_density]  Unit  Parameter Value[DCIS_cell_area_fraction.area_fraction]  Unit  Parameter Value[DCIS_cell_volume_fraction.volume_fraction]  Unit  Data File
MCDS_L_0000000052.0.0 microenvironment.measurement  6.17  mmHg  0.00883 1/micron^2  0.8 dimensionless 0.8 dimensionless MCDS_L_0000000052.xml
MCDS_L_0000000052.0.1 microenvironment.measurement  8 mmHg              MCDS_L_0000000052.xml
MCDS_L_0000000052.0.2 microenvironment.measurement  38  mmHg              MCDS_L_0000000052.xml
MCDS_L_0000000052.0.3 microenvironment.measurement  52  mmHg              MCDS_L_0000000052.xml
MCDS_L_0000000052.0.4 microenvironment.measurement  5 mmHg              MCDS_L_0000000052.xml
"""

# We will do a two-pass approach:

# 1st pass: parse all <variables> elements to generate the header row. Keep a running list of unique [name.type] attribute pairs.
#
# Columns' titles
fp.write('Sample Name' + sep_char + 'Protocol REF' + sep_char )
#uep = xml_root.find('.//variables')  # TODO: also req: keywords="viable"?

pval_list = []
uep = xml_root.find('.//cell_line')
num_vars = 0
for pheno in uep.findall('phenotype_dataset'):
  vs = pheno.find('.//variables') 
  # TODO: what to do if there are none
  if (vs):   # uep):
    for elm in vs.findall('variable'):

      # TODO: what about case-sensitive text?
      if ('type' in elm.attrib.keys()):  # TODO: what's desired format if 'type' is missing?
        pval_str = elm.attrib['name'] + '.' + elm.attrib['type']
      else:
        pval_str = elm.attrib['name'] 

      if pval_str not in pval_list:
        pval_list.append(pval_str)
        # print(pval_list)

        # pval_str = elm.attrib['name'] + '.' + elm.attrib['type']
        fp.write('Parameter Value[' + pval_str + '] ' + sep_char + 'Unit' + sep_char)
        num_vars += 1
fp.write('Data File\n')
#print('num_vars=',num_vars)


# 2nd pass: for each <phenotype_dataset>, each <variables>, and each <variable>, extract a row of relevant
#           info to match the column headings.
count = 0
# TODO: am I making too many assumptions about elements - existence, ordering, etc.?
id = xml_root.find(".//metadata").find(".//ID").text
uep = xml_root.find('.//cell_line')
for elm in uep.findall('phenotype_dataset'):  # incr 'count' for each 
  param_unit_list = len(pval_list)*[sep_char,"",sep_char,""]  # create a dummy list of Param/Unit entries and fill in if present
  param_unit_str = ""

  vs = elm.find('.//variables') 
#  print("----- found <variables>, count=",count)
  nvar = 0
#  for ma in v.findall('material_amount'):
  if vs:
    comment_str = id + '.0.' + str(count) + '\t' + 'microenvironment.measurement' 
#   print(comment_str)
    for v in vs.findall('variable'):  
      nvar += 1
  #    print(v.attrib['units'])
  #    print(v.find('.//material_amount').text)

      if ('type' in v.attrib.keys()):  # TODO: what's desired format if 'type' is missing?
        pval_str = v.attrib['name'] + '.' + v.attrib['type']
      else:
        pval_str= v.attrib['name'] 

      var_idx = pval_list.index(pval_str)  # get the index of this Parameter Value in our list
      # print(pval_str,' index = ',var_idx)

      # Need to strip out tabs here (sometimes)
      text_val = v.find('.//material_amount').text
#      print('------ text_val --->',text_val,'<---------')
      text_val = ' '.join(text_val.split())
#      print('------ text_val --->',text_val,'<---------')

      param_unit_str.join(param_unit_list) 

      if ('units' in v.attrib.keys()):  # TODO: what's desired format if missing?
        param_unit_list[4*var_idx + 1] = text_val
        param_unit_list[4*var_idx + 3] = v.attrib['units']
        # comment_str += (2*var_idx + 1)*sep_char + text_val + sep_char + v.attrib['units']
      else:
        param_unit_list[4*var_idx + 1] = text_val
        # comment_str += (2*var_idx + 1)*sep_char + text_val + sep_char + ""
      # print(param_unit_list)

#      comment_str += sep_char + v.find('.//material_amount').text + sep_char + v.attrib['units']
  #  print(comment_str)
  #  print('nvar=',nvar)
    comment_str += param_unit_str.join(param_unit_list)
    comment_str += sep_char + xml_base_filename + '\n'
    fp.write(comment_str)

    # if (nvar == num_vars):
    #   fp.write(sep_char)
    # else:
    #   for idx in range(nvar,2*num_vars):
    #     fp.write(sep_char)
  #  fp.write(comment_str + sep_char + xml_file + '\n')
#    fp.write(xml_file + '\n')
#    print("----- ",xml_base_filename, " + CR")

    # fp.write(xml_base_filename + '\n')
    count += 1

  else:  # if no 'variables' present, just print minimal info
#    comment_str = id + '.0.' + str(count) + '\t' + '' + '\t' + xml_file + '\n' 
    comment_str = id + '.0.' + str(count) + '\t' + '' + '\t' + xml_base_filename + '\n' 
    count += 1
    fp.write(comment_str)


fp.close()
print(' --> ' + assay_filename)


#=======================================================================
# Hackish, but let's open the i_ file again and append more Study info to the end.
if True:
  print('---------  make another pass to create more Assay files... ')
  fp_i = open(investigation_filename, 'a')
  #fp_a = open(investigation_filename, 'w')

  assay_basename = assay_filename[:-4]

  assay_filenames_str = sep_char + assay_filename
  measure_types_str = ""

  count = 0
  uep = xml_root.find('.//cell_line')
  for pheno_data in uep.findall('phenotype_dataset'):
    # print('-phenotype_dataset')
    # for pheno in pheno_data.findall('phenotype/cell_cycle/cell_cycle_phase/duration'):
    for pheno in pheno_data.findall('phenotype'):
      for cycle in pheno.findall('cell_cycle'):
        # print(cycle.attrib['model'],'.',end='')
        for phase in cycle.findall('cell_cycle_phase'):
          # print(phase.attrib['name'],'.',end='')
          for duration in phase.findall('duration'):
            measure_type = "phenotype cell_cycle cell_cycle_phase duration"
            # print('---phenotype/cell_cycle/cell_cycle_phase/duration', end="")
            print(measure_type, ", ",end="")
            print(duration.attrib['units'],'.',float(duration.text))

            count += 1
            # if (count > 3):
              # break
            assay_filename  = assay_basename + "-" + str(count) + ".txt"
            print("---> ",assay_filename)
            # Create a new Assay file
            fp_a = open(assay_filename, 'w')
            write_title = True

            # Append info onto the existing Investigation file
            # fp_i.write('STUDY ASSAYS\t\n')
            # fp_i.write('Study Assay File Name\t' + '"' + assay_filename + '"\n')
            # fp_i.write('Study Assay Measurement Type\t""\n')
            # line = 'Study Assay Measurement Type\t"' + measure_type + '"\n'

            assay_filenames_str += sep_char + assay_filename
            measure_types_str += sep_char + measure_type

            # fp_i.write(line)
            # fp_i.write('Study Assay Measurement Type Term Accession Number\t""\n')
            # fp_i.write('Study Assay Measurement Type Term Source REF\t""\n')
            # fp_i.write('Study Assay Technology Type\t"Digital Cell Line"\n')
            # fp_i.write('Study Assay Technology Type Term Accession Number\t""\n')
            # fp_i.write('Study Assay Technology Type Term Source REF\t""\n')
            # fp_i.write('Study Assay Technology Platform\t""\n')

            # Columns' titles
            if write_title:
              fp_a.write('Sample Name' + sep_char + 'Protocol REF' + sep_char + '\n')
              write_title = False
            
            sample_name = measure_type + str(count)
            duration_str = ' '.join(duration.text.split())   # strip out tabs and newlines
            fp_a.write(dqte + sample_name + dqte + sep_char + dqte + duration_str + dqte + '\n')
            fp_a.close()

  # Append info onto the existing Investigation file
  fp_i.write('STUDY ASSAYS\t\n')
  # TODO: check if any were found; need to have quotes around strings??
  # fp_i.write('Study Assay File Name\t' + '"' + assay_filenames_str + '"\n')
  fp_i.write('Study Assay File Name' + assay_filenames_str + '\n')
  # fp_i.write('Study Assay Measurement Type\t""\n')
  # line = 'Study Assay Measurement Type\t"' + measure_types_str + '"\n'
  line = 'Study Assay Measurement Type' + measure_types_str + '\n'
  fp_i.write(line)
  fp_i.write('Study Assay Measurement Type Term Accession Number\t""\n')
  fp_i.write('Study Assay Measurement Type Term Source REF\t""\n')
  fp_i.write('Study Assay Technology Type\t"Digital Cell Line"\n')
  fp_i.write('Study Assay Technology Type Term Accession Number\t""\n')
  fp_i.write('Study Assay Technology Type Term Source REF\t""\n')
  fp_i.write('Study Assay Technology Platform\t""\n')

  fp_i.close()