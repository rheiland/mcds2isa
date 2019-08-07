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
#   v0.3 - July 2019 : add more info from MCDS files into ISA-Tab files. Generate multiple a_ files.
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

sep_char = '\t'  # tab

tree = ET.parse(xml_file)  # TODO: relative path using env var?
xml_root = tree.getroot()

#------------------------------------------
def data_analyis_comments():
  uep = xml_root.find('.//metadata')
  for elm in uep.findall('data_analysis'):
    for child in elm.getchildren():
#      print("-------- data_analysis_comment:",child)
      print("-------- data_analysis_comment:",child.tag)
      c_str = "Comment[data-analysis_" + child.tag + "]" + sep_char 
      text_str = child.text
      if text_str is None:
        continue
      c_str += ' '.join(text_str.split())   # strip out tabs and newlines. sigh.
      c_str += '\n'
      fp.write(c_str)


#------------------------------------------
if not Path(xml_file).is_file():
	print(xml_file + 'does not exist!')
	sys.exit(-1)

if (os.sep in xml_file):
  xml_base_filename = xml_file[xml_file.rfind(os.sep)+1:]
else:
  xml_base_filename = xml_file

investigation_filename = "i_" + xml_base_filename[:-4] + ".txt"
study_filename = "s_" + xml_base_filename[:-4] + ".txt"

#=======================================================================
fp = open(investigation_filename, 'w')

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
url = []   # TODO: perhaps use later
uep = xml_root.find('.//data_origins')  # uep = unique entry point
for elm1 in uep.findall('data_origin'):
  print("-----------found data_origin")
  for elm in elm1.findall('citation'):
    print("-----------found citation")
    cite_pair = ['','']
    valid_citation = False
    for child in elm:
#      print("child.tag = ",child.tag)
      if (child.tag == 'DOI'):
        valid_citation = True
        doi_value = child.text
        doi_value = ' '.join(doi_value.split())   # strip out tabs and newlines. sigh.
        print("-----------found DOI = ", doi_value)
        cite_pair[0] = doi_value
#        doi.append(doi_value)  # do we want to append "" if none??
      elif (child.tag == 'PMID'):
        valid_citation = True
        pmid_value = child.text
        pmid_value = ' '.join(pmid_value.split())   # strip out tabs and newlines. sigh.
        print("-----------found PMID = ", pmid_value)
#        pmid.append(pmid_value)  # do we want to append "" if none??
        cite_pair[1] = pmid_value
      # elif (child.tag == 'URL'):   # not currently using
      #   url_value = child.text
      #   url_value = ' '.join(url_value.split())   # strip out tabs and newlines. sigh.
      #   print("-----------found URL = ", url_value)
      #   url.append(url_value)  # do we want to append "" if none??

    if valid_citation:
      doi.append(cite_pair[0])
      pmid.append(cite_pair[1])

      # Why doesn't this work??????????
#    doi.append(elm.find('.//DOI').text)
#     if (elm.find('.//DOI')):
#       print("-----------found DOI")
#     if (elm.find('.//PMID')):
#       print("-----------found PMID")
#     doi_ptr = elm.find('.//DOI')
# #    if (doi_ptr == None):
# #      doi_value = ""
# #    else:
#     if (doi_ptr):
#       print('    -- found DOI')
#       doi_value = doi_ptr.text
#     # doi.append(doi_value)  # do we want to append "" if none??
#       doi.append(doi_value)  # do we want to append "" if none??

#    pmid.append(elm.find('.//PMID').text)
#     pmid_ptr = elm.find('.//PMID')
#     if (pmid_ptr == None):
#       pmid_value = ""
#     else:
#       pmid_value = pmid_ptr.text
#       pmid.append(pmid_value)
# #    pmid.append(pmid_value)

#     url_ptr = elm.find('.//URL')
#     if (url_ptr == None):
#       url_value = ""
#     else:
#       url_value = url_ptr.text
#       url.append(url_value)

#print("(post data_origin) pmid=",pmid)
#print("(post data_origin) url=",url)

uep = xml_root.find('.//metadata')
for elm in uep.findall('data_analysis'):
  if False:  # skip for now (TODO later??)
    print("-----------found data_analysis")
    for child in elm:
      print(child.tag)
      if (child.tag == 'DOI'):
        doi_value = child.text
        doi_value = ' '.join(doi_value.split())   # strip out tabs and newlines. sigh.
        print("-----------found DOI = ", doi_value)
        doi.append(doi_value)  # do we want to append "" if none??
      elif (child.tag == 'PMID'):
        pmid_value = child.text
        pmid_value = ' '.join(pmid_value.split())   # strip out tabs and newlines. sigh.
        print("-----------found PMID = ", pmid_value)
        pmid.append(pmid_value)  # do we want to append "" if none??
      # elif (child.tag == 'URL'):
      #   url_value = child.text
      #   url_value = ' '.join(url_value.split())   # strip out tabs and newlines. sigh.
      #   print("-----------found URL = ", url_value)
      #   url.append(url_value)  # do we want to append "" if none??

#print("(post data_analysis) pmid=",pmid)

sep_char_sq = sep_char + '"'   # tab + single quote

#print("----------- len(pmid) = ",len(pmid))
if len(pmid) == 0:
  pmid_str = sep_char + '""'
else:
  pmid_str = ''
  for elm in pmid:
    pmid_str += sep_char + '"' + elm + '"'
print("--------- pmid_str = ",pmid_str)
#fp.write('Investigation PubMed ID' + sep_char + pmid_str + '\n')
fp.write('Investigation PubMed ID' + pmid_str + '\n')

print("--------- len(doi) = ",len(doi))
if len(doi) == 0:
  doi_str = sep_char + '""'
else:
  doi_str = ''
  for elm in pmid:
    doi_str += sep_char + '"' + elm + '"'
print("--------- doi_str = ",doi_str)
#fp.write('Investigation Publication DOI' + sep_char + doi_str + '\n')
fp.write('Investigation Publication DOI' + doi_str + '\n')

if len(pmid) == 0:
  empty_str = '""'
else:
  empty_str = ''.join(sep_char + '""' for x in pmid) 
fp.write('Investigation Publication Author List' + sep_char + empty_str + '\n')
fp.write('Investigation Publication Title' + sep_char + empty_str + '\n')

if len(pmid) == 0:
  pub_status_str = sep_char + '""'
  pub_title_str = sep_char + '""'
  pub_status_TA_str = sep_char + '""'
  pub_status_TSR_str = sep_char + '""'
else:
  pub_status_str = ''.join(sep_char + '"Published"' for x in pmid) 
  pub_title_str = ''.join(sep_char + '""' for x in pmid)   # used later
  pub_status_TA_str = ''.join('\t"C19026"' for x in pmid) 
  pub_status_TSR_str = ''.join('\t"NCIT"' for x in pmid) 

#fp.write('Investigation Publication Status' + sep_char + pub_status_str + '\n')
#fp.write('Investigation Publication Status Term Accession' + sep_char + pub_status_TA_str + '\n')
#fp.write('Investigation Publication Status Term Source REF' + sep_char + pub_status_TSR_str + '\n')
fp.write('Investigation Publication Status' + pub_status_str + '\n')
fp.write('Investigation Publication Status Term Accession' + pub_status_TA_str + '\n')
fp.write('Investigation Publication Status Term Source REF' + pub_status_TSR_str + '\n')

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
data_analyis_comments()
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
# fp.write('Study Protocol Name\t"microenvironment.measurement"\n')
spn_str = "Study Protocol Name"
study_protocol_names = []
if xml_root.find('.//microenvironment'):
  study_protocol_names.append("microenvironment.measurement")
if xml_root.find('.//cell_line//phenotype_dataset//phenotype//cell_cycle'):
  study_protocol_names.append("cell_cyles.measurement")
if xml_root.find('.//cell_line//phenotype_dataset//phenotype//cell_death'):
  study_protocol_names.append("cell_death.measurement")
if xml_root.find('.//cell_line//phenotype_dataset//phenotype//mechanics'):
  study_protocol_names.append("mechanics.measurement")
if xml_root.find('.//cell_line//phenotype_dataset//phenotype//motility'):
  study_protocol_names.append("motility.measurement")

for spn in study_protocol_names:
  spn_str += "\t" + spn 
spn_str += "\n"
fp.write(spn_str)


#empty_cell = "N/A"
empty_cell = ""
empty_row = ''
for spn in study_protocol_names:
  empty_row += '\t' + empty_cell

# one less, if <microenv*> column
empty_row2 = ''
for idx in range(len(study_protocol_names) - 1):
  empty_row2 += '\t' + empty_cell

#fp.write('Study Protocol Type\t""\n')
fp.write('Study Protocol Type' + empty_row + '\n')
fp.write('Study Protocol Type Term Accession Number' + empty_row + '\n')
fp.write('Study Protocol Type Term Source REF' + empty_row + '\n')
fp.write('Study Protocol Description' + empty_row + '\n')
fp.write('Study Protocol URI' + empty_row + '\n')
fp.write('Study Protocol Version' + empty_row + '\n')


if xml_root.find('.//microenvironment'):
  # for <microenvironment> 
  #fp.write('Study Protocol Parameters Name  "oxygen.partial_pressure; DCIS_cell_density(2D).surface_density; DCIS_cell_area_fraction.area_fraction; DCIS_cell_volume_fraction.volume_fraction"\n')
#  comment_str = 'Study Protocol Parameters Name\t"'
  comment_str = 'Study Protocol Parameters Name\t'
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
#    fp.write(comment_str[:-2] + '"\n')
    my_str = comment_str[:-2] + empty_row2 + '\n'
#    my_str = comment_str[:-2] + empty_row + '\n'
#    print("my_str=",my_str)
    fp.write(my_str)
else:
  fp.write('Study Protocol Parameters Name' + empty_row + '\n')


#print(" -------- len(pmid) = ",len(pmid))
#semicolon_sep_empty_str = ''.join('; ' for x in pmid)

#fp.write('Study Protocol Parameters Name Term Accession Number\t"' + semicolon_sep_empty_str + ' "\n')
fp.write('Study Protocol Parameters Name Term Accession Number' + empty_row + '\n')
fp.write('Study Protocol Parameters Name Term Source REF' + empty_row + '\n')
fp.write('Study Protocol Components Name' + empty_row + '\n')
fp.write('Study Protocol Components Type' + empty_row + '\n')
fp.write('Study Protocol Components Type Term Accession Number' + empty_row + '\n')
fp.write('Study Protocol Components Type Term Source REF' + empty_row + '\n')


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


#  suffix += 1   # WHAT? just doing this causes invalid results in Metadata Utility???????
  row_str += dqte + pd_elm.attrib['keywords'] + dqte + sep_char + dqte + source_name + '.' + str(suffix) + dqte
  suffix += 1   # WHAT? just doing this causes invalid results in Metadata Utility???????
  fp_s.write(row_str + '\n')

fp_s.close()
print(' --> ' + study_filename)


#=======================================================================
# NOTE: Cannot assume this a_ will be created. E.g., MCDS_L_0000000083.xml doesn't have <microenvironment> or <variables>.

assay_filenames_str = ""
#measure_types = sep_char 
#measure_types = "" 
measure_types = []
assay_filenames = []
if (xml_root.find('.//microenvironment')):

  measure_types.append("microenvironment")

  #assay_filename1 = "a_" + xml_base_filename[:-4] + "-1.txt"
  assay_filename1 = "a_" + xml_base_filename[:-4] + "-cellMicroenvironmentAssay.txt"
  assay_filenames.append(assay_filename1)
  fp = open(assay_filename1, 'w')
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
  print(' --> ' + assay_filename1)
  
#=======================================================================
# For appending onto the "i_" file at the end
#tech_types = sep_char + "Digital Cell Line"
empty_types = sep_char + '""'

#assay_filename2 = "a_" + xml_base_filename[:-4] + "-2.txt"
assay_filename2 = "a_" + xml_base_filename[:-4] + "-cellCycleAssay.txt"
#fp = open(assay_filename2, 'w')

has_content = False

# For each <phenotype_dataset>, each <phenotype>, extract a row of relevant info to match the column headings.
count = 0
# TODO: am I making too many assumptions about elements - existence, ordering, etc.?
id = xml_root.find(".//metadata").find(".//ID").text
uep = xml_root.find('.//cell_line')
for elm in uep.findall('phenotype_dataset'):  # incr 'count' for each 
  # param_unit_list = len(pval_list)*[sep_char,"",sep_char,""]  # create a dummy list of Param/Unit entries and fill in if present
  # param_unit_str = ""

  phenotype = elm.find('.//phenotype')   # TODO: use 'type' attrib?
#  print("----- found <variables>, count=",count)
  # nvar = 0
#  for ma in v.findall('material_amount'):
  if phenotype:
    # comment_str = id + '.0.' + str(count) + '\t' + 'phenotype.cell_cycle'    # start of a new row of info
#   print(comment_str)
    # if (not phenotype.find('cell_cycle'):
    #     comment_str += sep_char
    # else:
    for cell_cycle in phenotype.findall('cell_cycle'):  

      if not has_content:
        has_content = True
        measure_types.append("phenotype cell_cycle cell_cycle_phase duration")
        # tech_types += sep_char + "Digital Cell Line"
        empty_types += sep_char + '""'

        fp = open(assay_filename2, 'w')
        assay_filenames.append(assay_filename2)
        # The header (column titles) is known in advance 
        fp.write('Sample Name' + sep_char + 'Protocol REF' + sep_char + 'Parameter Value[cell_cycle.model]' + 
          sep_char + 'Parameter Value[cell_cycle_phase.name]' +
          sep_char + 'Parameter Value[duration]' +
          sep_char + 'Units' + 
          sep_char + 'Parameter Value[duration.measurement_type]' +
          sep_char + 'Parameter Value[net_birth_rate]' +
          sep_char + 'Units' +
          sep_char + 'Parameter Value[net_birth_rate.measurement_type]' +
          sep_char + 'Parameter Value[net_birth_rate.standard_error_of_the_mean]' +
          sep_char + 'Data File\n' )

      comment_str = id + '.0.' + str(count) + '\t' + 'phenotype.cell_cycle'    # start of a new row of info
      # nvar += 1
  #    print(v.attrib['units'])
  #    print(v.find('.//material_amount').text)

      if ('model' in cell_cycle.attrib.keys()):  # TODO: what's desired format if attribute is missing?
        # pval_str = v.attrib['model'] + '.' + v.attrib['type']
        comment_str += sep_char + cell_cycle.attrib['model'] 
      else:
        comment_str += sep_char

#          *083
				# <cell_cycle ID="0" model="total">
				# 	<cell_cycle_phase ID="0" name="total">
				# 		<net_birth_rate measurement_type="inferred" units="1/year">28.468</net_birth_rate>
				# 		<cell_cycle_arrest>
				# 			<condition measurement_type="estimated" type="maximum_cell_density" units="cells/mm^3">250000.0</condition>
				# 		</cell_cycle_arrest>
				# 	</cell_cycle_phase>
				# 	<custom>
				# 		<velocity units="mm/year">65.136</velocity>
				# 	</custom>
				# </cell_cycle>

      for cell_cycle_phase in cell_cycle.findall('cell_cycle_phase'):  
        if ('name' in cell_cycle_phase.attrib.keys()):  
          comment_str += sep_char + cell_cycle_phase.attrib['name'] 
        else:
          comment_str += sep_char 

        found = False
        for duration in cell_cycle_phase.findall('duration'):  
          found = True
          text_val = ' '.join(duration.text.split())
          comment_str += sep_char + text_val
          if ('units' in duration.attrib.keys()):  
            comment_str += sep_char + duration.attrib['units'] 
          else:
            comment_str += sep_char 
          if ('measurement_type' in duration.attrib.keys()):  
            comment_str += sep_char + duration.attrib['measurement_type'] 
          else:
            comment_str += sep_char 
          # text_val = duration.text
          # comment_str += sep_char + duration.text
        if (not found):
          print("------ cell cyle: no duration found")
          comment_str += sep_char + "" + sep_char + "" + sep_char + ""

        found = False
        for net_birth_rate in cell_cycle_phase.findall('net_birth_rate'):  
          found = True
          text_val = ' '.join(net_birth_rate.text.split())
          comment_str += sep_char + text_val
          if ('units' in net_birth_rate.attrib.keys()):  
            comment_str += sep_char + net_birth_rate.attrib['units'] 
          else:
            comment_str += sep_char 
          if ('measurement_type' in net_birth_rate.attrib.keys()):  
            comment_str += sep_char + net_birth_rate.attrib['measurement_type'] 
          else:
            comment_str += sep_char 
          if ('standard_error_of_the_mean' in net_birth_rate.attrib.keys()):  
            comment_str += sep_char + net_birth_rate.attrib['standard_error_of_the_mean'] 
          else:
            comment_str += sep_char 
        if (not found):
          comment_str += sep_char + "" + sep_char + "" + sep_char + "" + sep_char + ""


      # var_idx = pval_list.index(pval_str)  # get the index of this Parameter Value in our list
      # print(pval_str,' index = ',var_idx)

      # Need to strip out tabs here (sometimes)
      # text_val = cell_cycle.find('.//material_amount').text
#      print('------ text_val --->',text_val,'<---------')
      # text_val = ' '.join(text_val.split())
#      print('------ text_val --->',text_val,'<---------')

      # param_unit_str.join(param_unit_list) 

    if has_content:
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

#   else:  # if no 'variables' present, just print minimal info
# #    comment_str = id + '.0.' + str(count) + '\t' + '' + '\t' + xml_file + '\n' 
#     comment_str = id + '.0.' + str(count) + '\t' + '' + '\t' + xml_base_filename + '\n' 
#     count += 1
#     fp.write(comment_str)

if has_content:
  fp.close()
  print(' --> ' + assay_filename2)
else:
  print(' --> MISSING ' + assay_filename2)

# assay_filenames_str += sep_char + assay_filename2

#=======================================================================
#assay_filename3 = "a_" + xml_base_filename[:-4] + "-3.txt"
assay_filename3 = "a_" + xml_base_filename[:-4] + "-cellDeathAssay.txt"
#fp = open(assay_filename3, 'w')

has_content = False

# For each <phenotype_dataset>, each <phenotype>, extract a row of relevant info to match the column headings.
count = 0
# TODO: am I making too many assumptions about elements - existence, ordering, etc.?
id = xml_root.find(".//metadata").find(".//ID").text
uep = xml_root.find('.//cell_line')
for elm in uep.findall('phenotype_dataset'):  # incr 'count' for each 
  phenotype = elm.find('.//phenotype')   # TODO: use 'type' attrib?
  if phenotype:
    for cell_death in phenotype.findall('cell_death'):  

      if not has_content:
        has_content = True
        measure_types.append("phenotype cell_death")
        # tech_types += sep_char + "Digital Cell Line"
        empty_types += sep_char + '""'

        fp = open(assay_filename3, 'w')
        assay_filenames.append(assay_filename3)
        # The header (column titles) is known in advance 
        fp.write('Sample Name' + sep_char + 'Protocol REF' + 
          sep_char + 'Parameter Value[cell_death.type]' +
          sep_char + 'Parameter Value[duration]' +
          sep_char + 'Units' + 
          sep_char + 'Parameter Value[cell_death.measurement_type]' +
          sep_char + 'Data File\n' )

      comment_str = id + '.0.' + str(count) + '\t' + 'phenotype.cell_death'    # start of a new row of info

      if ('type' in cell_death.attrib.keys()):  # TODO: what's desired format if attribute is missing?
        comment_str += sep_char + cell_death.attrib['type'] 
      else:
        comment_str += sep_char

      for duration in cell_death.findall('duration'):  
        text_val = ' '.join(duration.text.split())
        comment_str += sep_char + text_val
        if ('units' in duration.attrib.keys()):  
          comment_str += sep_char + duration.attrib['units'] 
        else:
          comment_str += sep_char 
        if ('measurement_type' in duration.attrib.keys()):  
          comment_str += sep_char + duration.attrib['measurement_type'] 
        else:
          comment_str += sep_char 

      if has_content:
        comment_str += sep_char + xml_base_filename + '\n'
        fp.write(comment_str)

    count += 1

if has_content:
  fp.close()
  print(' --> ' + assay_filename3)
else:
  print(' --> MISSING ' + assay_filename3)

#=======================================================================
#<mechanics>
#					<maximum_cell_deformation measurement_type="literature" units="micron / hour" range="5 11">6.2</maximum_cell_deformation>
#assay_filename4 = "a_" + xml_base_filename[:-4] + "-4.txt"
assay_filename4 = "a_" + xml_base_filename[:-4] + "-cellMechanicsAssay.txt"
#assay_filenames_str += " " + assay_filename4
#fp = open(assay_filename4, 'w')

has_content = False

# For each <phenotype_dataset>, each <phenotype>, extract a row of relevant info to match the column headings.
count = 0
# TODO: am I making too many assumptions about elements - existence, ordering, etc.?
id = xml_root.find(".//metadata").find(".//ID").text
uep = xml_root.find('.//cell_line')
for elm in uep.findall('phenotype_dataset'):  # incr 'count' for each 
  phenotype = elm.find('.//phenotype')   # TODO: use 'type' attrib?
  if phenotype:
    for mechanics in phenotype.findall('mechanics'):  

      if not has_content:
        has_content = True
        measure_types.append("phenotype mechanics")
        # tech_types += sep_char + "Digital Cell Line"
        empty_types += sep_char + '""'

        fp = open(assay_filename4, 'w')
        assay_filenames.append(assay_filename4)

        # The header (column titles) is known in advance 
        fp.write('Sample Name' + sep_char + 'Protocol REF' + 
          sep_char + 'Parameter Value[maximum_cell_deformation]' +
          sep_char + 'Units' + 
          sep_char + 'Parameter Value[maximum_cell_deformation.measurement_type]' +
          sep_char + 'Parameter Value[maximum_cell_deformation.range]' +
          sep_char + 'Data File\n' )


      comment_str = id + '.0.' + str(count) + '\t' + 'phenotype.mechanics'    # start of a new row of info

      for maximum_cell_deformation in mechanics.findall('maximum_cell_deformation'):  
        text_val = ' '.join(maximum_cell_deformation.text.split())
        comment_str += sep_char + text_val
        if ('units' in maximum_cell_deformation.attrib.keys()):  
          comment_str += sep_char + maximum_cell_deformation.attrib['units'] 
        else:
          comment_str += sep_char 

        if ('measurement_type' in maximum_cell_deformation.attrib.keys()):  
          comment_str += sep_char + maximum_cell_deformation.attrib['measurement_type'] 
        else:
          comment_str += sep_char 

        if ('range' in maximum_cell_deformation.attrib.keys()):  
          comment_str += sep_char + maximum_cell_deformation.attrib['range'] 
        else:
          comment_str += sep_char 

      if has_content:
        comment_str += sep_char + xml_base_filename + '\n'
        fp.write(comment_str)

    count += 1

if has_content:
  fp.close()
  print(' --> ' + assay_filename4)
else:
  print(' --> MISSING ' + assay_filename4)

#================================================================================
# Question: can a cell line have BOTH <restricted> and  <unrestricted> motility??
#
# e.g., in  *043.xml:
				# <motility>
				# 	<restricted ID="0">
				# 		<timescale units="hour">24</timescale>
				# 		<restriction>
				# 			<surface_variable name="glass"/>
				# 		</restriction>
				# 		<mean_speed units="micron / hour" standard_deviation="3.22" number_obs="11">15.25</mean_speed>
				# 		<persistence units="hour" standard_deviation="0.85" number_obs="11">2.58</persistence>
				# 		<diffusion_coefficient units="10^-6 cm^2 / h" standard_deviation="0.98" number_obs="11">3.00</diffusion_coefficient>
				# 	</restricted>
				# 	<restricted ID="1">
				# 		<timescale units="hour">24</timescale>
				# 		<restriction>
				# 			<surface_variable name="fibrinogen" MeSH_ID="D005340"/>
				# 		</restriction>
				# 		<mean_speed units="micron / hour" standard_deviation="1.11" number_obs="8">14.86</mean_speed>
				# 		<persistence units="hour" standard_deviation="0.63" number_obs="8">2.14</persistence>
				# 		<diffusion_coefficient units="10^-6 cm^2 / h" standard_deviation="0.71" number_obs="8">2.37</diffusion_coefficient>
				# 	</restricted>
				# </motility>

# e.g., in  *083.xml:
#                                <motility>
#                                        <unrestricted ID="0">
#                                                <timescale measurement_type="inferred" units="days">4.0</timescale>
#                                                <diffusion_coefficient measurement_type="inferred" units="mm^2 / year">37.259</diffusion_coefficient>
#                                        </unrestricted>
#                                </motility>

#assay_filename5 = "a_" + xml_base_filename[:-4] + "-5.txt"
assay_filename5 = "a_" + xml_base_filename[:-4] + "-cellMotilityAssay.txt"

has_content = False

# For each <phenotype_dataset>, each <phenotype>, extract a row of relevant info to match the column headings.
count = 0
# TODO: am I making too many assumptions about elements - existence, ordering, etc.?
id = xml_root.find(".//metadata").find(".//ID").text
uep = xml_root.find('.//cell_line')
for elm in uep.findall('phenotype_dataset'):  # incr 'count' for each 
  phenotype = elm.find('.//phenotype')   # TODO: use 'type' attrib?
  if phenotype:
    for motility in phenotype.findall('motility'):  

      if not has_content:
        has_content = True
        measure_types.append("phenotype motility")
        # tech_types += sep_char + "Digital Cell Line"
        empty_types += sep_char + '""'

        assay_filenames.append(assay_filename5)
        fp = open(assay_filename5, 'w')

        # The header (column titles) is known in advance 
        fp.write('Sample Name' + sep_char + 'Protocol REF' + 
          sep_char + 'Parameter Value[timescale]' +
          sep_char + 'Units' + 
          sep_char + 'Parameter Value[restriction.surface_variable.name]' +
          sep_char + 'Parameter Value[restriction.surface_variable.MeSH_ID]' +
          sep_char + 'Parameter Value[mean_speed]' +
          sep_char + 'Units' + 
          sep_char + 'Parameter Value[mean_speed.standard_deviation]' +
          sep_char + 'Parameter Value[mean_speed.number_obs]' +
          sep_char + 'Parameter Value[persistence]' +
          sep_char + 'Units' + 
          sep_char + 'Parameter Value[persistence.standard_deviation]' +
          sep_char + 'Parameter Value[persistence.number_obs]' +
          sep_char + 'Parameter Value[diffusion_coefficient]' +
          sep_char + 'Units' + 
          sep_char + 'Parameter Value[diffusion_coefficient.standard_deviation]' +
          sep_char + 'Parameter Value[diffusion_coefficient.number_obs]' +
          sep_char + 'Data File\n' )


      #  -------- for <restricted> motility:
      for restricted in motility.findall('restricted'):  
        comment_str = id + '.0.' + str(count) + '\t' + 'phenotype.motility.restricted'    # start of a new row of info
#        print('restricted: ', comment_str )

        for timescale in restricted.findall('timescale'):  
          text_val = ' '.join(timescale.text.split())
          comment_str += sep_char + text_val
          if ('units' in timescale.attrib.keys()):  
            comment_str += sep_char + timescale.attrib['units'] 
          else:
            comment_str += sep_char 
            
        found = False
        for restriction in restricted.findall('restriction'):  
          found = True
          for surface_var in restriction.findall('surface_variable'):  
            if ('name' in surface_var.attrib.keys()):  
              comment_str += sep_char + surface_var.attrib['name'] 
            else:
              comment_str += sep_char 

            if ('MeSH_ID' in surface_var.attrib.keys()):  
              comment_str += sep_char + surface_var.attrib['MeSH_ID'] 
            else:
              comment_str += sep_char 
        if not found:
          comment_str += sep_char + "" + sep_char + ""

				# 		<mean_speed units="micron / hour" standard_deviation="3.22" number_obs="11">15.25</mean_speed>
				# 		<persistence units="hour" standard_deviation="0.85" number_obs="11">2.58</persistence>
				# 		<diffusion_coefficient units="10^-6 cm^2 / h" standard_deviation="0.98" number_obs="11">3.00</diffusion_coefficient>
        found = False
        for mean_speed in restricted.findall('mean_speed'):  
          found = True
          text_val = ' '.join(mean_speed.text.split())
          comment_str += sep_char + text_val
          if ('units' in mean_speed.attrib.keys()):  
            comment_str += sep_char + mean_speed.attrib['units'] 
          else:
            comment_str += sep_char 
          if ('standard_deviation' in mean_speed.attrib.keys()):  
            comment_str += sep_char + mean_speed.attrib['standard_deviation'] 
          else:
            comment_str += sep_char 
          if ('number_obs' in mean_speed.attrib.keys()):  
            comment_str += sep_char + mean_speed.attrib['number_obs'] 
          else:
            comment_str += sep_char 
        if not found:
          # comment_str += sep_char + "" + sep_char + ""
          comment_str += sep_char + sep_char + sep_char + sep_char 

        found = False
        for persistence in restricted.findall('persistence'):  
          found = True
          text_val = ' '.join(persistence.text.split())
          comment_str += sep_char + text_val
          if ('units' in persistence.attrib.keys()):  
            comment_str += sep_char + persistence.attrib['units'] 
          else:
            comment_str += sep_char 
          if ('standard_deviation' in persistence.attrib.keys()):  
            comment_str += sep_char + persistence.attrib['standard_deviation'] 
          else:
            comment_str += sep_char 
          if ('number_obs' in persistence.attrib.keys()):  
            comment_str += sep_char + persistence.attrib['number_obs'] 
          else:
            comment_str += sep_char 
        if not found:
          # comment_str += sep_char + "" + sep_char + ""
          comment_str += sep_char + sep_char + sep_char + sep_char 

        found = False
        for diffusion_coef in restricted.findall('diffusion_coefficient'):  
          found = True
          text_val = ' '.join(diffusion_coef.text.split())
          comment_str += sep_char + text_val
          if ('units' in diffusion_coef.attrib.keys()):  
            comment_str += sep_char + diffusion_coef.attrib['units'] 
          else:
            comment_str += sep_char 
          if ('standard_deviation' in diffusion_coef.attrib.keys()):  
            comment_str += sep_char + diffusion_coef.attrib['standard_deviation'] 
          else:
            comment_str += sep_char 
          if ('number_obs' in diffusion_coef.attrib.keys()):  
            comment_str += sep_char + diffusion_coef.attrib['number_obs'] 
          else:
            comment_str += sep_char 
        if not found:
          # comment_str += sep_char + "" + sep_char + ""
          comment_str += sep_char + sep_char + sep_char + sep_char 

        if has_content:
          comment_str += sep_char + xml_base_filename + '\n'
          fp.write(comment_str)

        count += 1


      #  -------- for <unrestricted> motility:
      for unrestricted in motility.findall('unrestricted'):  
        comment_str = id + '.0.' + str(count) + '\t' + 'phenotype.motility.unrestricted'    # start of a new row of info
#        print('unrestricted: ', comment_str )

        found = False
        for timescale in unrestricted.findall('timescale'):  
          text_val = ' '.join(timescale.text.split())
          comment_str += sep_char + text_val
          if ('units' in timescale.attrib.keys()):  
            comment_str += sep_char + timescale.attrib['units'] 
          else:
            comment_str += sep_char 


          # the next 2 columns will be missing for <unrestricted>
          comment_str += sep_char + "" + sep_char + ""

        # ------ I don't think the following fields are present for <unrestricted>, but leave in place ------------
				# 		<mean_speed units="micron / hour" standard_deviation="3.22" number_obs="11">15.25</mean_speed>
				# 		<persistence units="hour" standard_deviation="0.85" number_obs="11">2.58</persistence>
				# 		<diffusion_coefficient units="10^-6 cm^2 / h" standard_deviation="0.98" number_obs="11">3.00</diffusion_coefficient>
        found = False
        for mean_speed in unrestricted.findall('mean_speed'):  
          found = True
          text_val = ' '.join(mean_speed.text.split())
          comment_str += sep_char + text_val
          if ('units' in mean_speed.attrib.keys()):  
            comment_str += sep_char + mean_speed.attrib['units'] 
          else:
            comment_str += sep_char 
          if ('standard_deviation' in mean_speed.attrib.keys()):  
            comment_str += sep_char + mean_speed.attrib['standard_deviation'] 
          else:
            comment_str += sep_char 
          if ('number_obs' in mean_speed.attrib.keys()):  
            comment_str += sep_char + mean_speed.attrib['number_obs'] 
          else:
            comment_str += sep_char 
        if not found:
          # comment_str += sep_char + "" + sep_char + ""
          comment_str += sep_char + sep_char + sep_char + sep_char 

        found = False
        for persistence in unrestricted.findall('persistence'):  
          found = True
          text_val = ' '.join(persistence.text.split())
          comment_str += sep_char + text_val
          if ('units' in persistence.attrib.keys()):  
            comment_str += sep_char + persistence.attrib['units'] 
          else:
            comment_str += sep_char 
          if ('standard_deviation' in persistence.attrib.keys()):  
            comment_str += sep_char + persistence.attrib['standard_deviation'] 
          else:
            comment_str += sep_char 
          if ('number_obs' in persistence.attrib.keys()):  
            comment_str += sep_char + persistence.attrib['number_obs'] 
          else:
            comment_str += sep_char 
        if not found:
          # comment_str += sep_char + "" + sep_char + ""
          comment_str += sep_char + sep_char + sep_char + sep_char 
        # ------ ^^  leave in place ------------


        found = False
        for diffusion_coef in unrestricted.findall('diffusion_coefficient'):  
          found = True
          text_val = ' '.join(diffusion_coef.text.split())
          comment_str += sep_char + text_val
          if ('units' in diffusion_coef.attrib.keys()):  
            comment_str += sep_char + diffusion_coef.attrib['units'] 
          else:
            comment_str += sep_char 
          if ('standard_deviation' in diffusion_coef.attrib.keys()):  
            comment_str += sep_char + diffusion_coef.attrib['standard_deviation'] 
          else:
            comment_str += sep_char 
          if ('number_obs' in diffusion_coef.attrib.keys()):  
            comment_str += sep_char + diffusion_coef.attrib['number_obs'] 
          else:
            comment_str += sep_char 
        if not found:
          # comment_str += sep_char + "" + sep_char + ""
          comment_str += sep_char + sep_char + sep_char + sep_char 


        if has_content:
          comment_str += sep_char + xml_base_filename + '\n'
          fp.write(comment_str)

        count += 1

if has_content:
  fp.close()
  print(' --> ' + assay_filename5)
else:
  print(' --> MISSING ' + assay_filename5)

#=======================================================================
# Hackish, but let's open the i_ file again and append more Study info to the end.
'''
if False:
  print('---------  make another pass to create more Assay files... ')
  # fp_i = open(investigation_filename, 'a')
  #fp_a = open(investigation_filename, 'w')

  # assay_basename = assay_filename[:-4]

  # assay_filenames_str = sep_char + assay_filename
  measure_types_str = ""
  assay_tech_types_str = ""

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
            # assay_filename  = assay_basename + "-" + str(count) + ".txt"
            # print("---> ",assay_filename)
            # Create a new Assay file
            # fp_a = open(assay_filename, 'w')
            write_title = True

            # Append info onto the existing Investigation file
            # fp_i.write('STUDY ASSAYS\t\n')
            # fp_i.write('Study Assay File Name\t' + '"' + assay_filename + '"\n')
            # fp_i.write('Study Assay Measurement Type\t""\n')
            # line = 'Study Assay Measurement Type\t"' + measure_type + '"\n'

            # assay_filenames_str += sep_char + assay_filename
            measure_types_str += sep_char + measure_type
            assay_tech_types_str += sep_char + "Digital Cell Line"  # jus duplicate - is it necessary to have one in each column?

            # fp_i.write(line)
            # fp_i.write('Study Assay Measurement Type Term Accession Number\t""\n')
            # fp_i.write('Study Assay Measurement Type Term Source REF\t""\n')
            # fp_i.write('Study Assay Technology Type\t"Digital Cell Line"\n')
            # fp_i.write('Study Assay Technology Type Term Accession Number\t""\n')
            # fp_i.write('Study Assay Technology Type Term Source REF\t""\n')
            # fp_i.write('Study Assay Technology Platform\t""\n')

            # Columns' titles
            # if write_title:
            #   fp_a.write('Sample Name' + sep_char + 'Protocol REF' + sep_char + '\n')
            #   write_title = False
            
            # sample_name = measure_type + str(count)
            # duration_str = ' '.join(duration.text.split())   # strip out tabs and newlines
            # fp_a.write(dqte + sample_name + dqte + sep_char + dqte + duration_str + dqte + '\n')
            # fp_a.close()
'''

# Append info onto the existing Investigation file
# duplicate, for each Assay file
'''
measure_types = sep_char + "microenvironment"
measure_types += sep_char + "phenotype cell_cycle cell_cycle_phase duration"
measure_types += sep_char + "phenotype cell_death"
measure_types += sep_char + "phenotype mechanics"
measure_types += sep_char + "phenotype motility"

tech_types = sep_char + "Digital Cell Line"
tech_types += sep_char + "Digital Cell Line"
tech_types += sep_char + "Digital Cell Line"
tech_types += sep_char + "Digital Cell Line"
tech_types += sep_char + "Digital Cell Line"
'''

fp_i = open(investigation_filename, 'a')
fp_i.write('STUDY ASSAYS\t\n')
# TODO: check if any were found; need to have quotes around strings??
# fp_i.write('Study Assay File Name\t' + '"' + assay_filenames_str + '"\n')
#fp_i.write('Study Assay File Name' + assay_filenames_str + '\n')

#assay_filenames_str = assay_filename1 + sep_char + assay_filename2+ sep_char + assay_filename3
#assay_filenames_str += sep_char + assay_filename4 + sep_char + assay_filename5

#fp_i.write('Study Assay File Name' + sep_char + assay_filenames_str + '\n')
line = 'Study Assay File Name' 
for f in assay_filenames:
  line += sep_char + f 
line += '\n'
fp_i.write(line)

# fp_i.write('Study Assay Measurement Type\t""\n')
# line = 'Study Assay Measurement Type\t"' + measure_types_str + '"\n'
line = 'Study Assay Measurement Type' 
first_time = True
for m in measure_types:
  line += sep_char + m 
  if first_time:
    first_time = False
#    empty_types = sep_char + '""'
    empty_types = sep_char + empty_cell
  else:
#    empty_types += sep_char + '""'
    empty_types += sep_char + empty_cell
line += '\n'
fp_i.write(line)

line = 'Study Assay Measurement Type Term Accession Number' + empty_types + '\n'
fp_i.write(line)
line = 'Study Assay Measurement Type Term Source REF' + empty_types + '\n'
fp_i.write(line)

#fp_i.write('Study Assay Technology Type\t"Digital Cell Line"\n')
#line = 'Study Assay Technology Type' + assay_tech_types_str + '\n'
#line = 'Study Assay Technology Type' + tech_types + '\n'
line = 'Study Assay Technology Type' 
for m in measure_types:
  line += sep_char + "Digital Cell Line" 
line += '\n'
fp_i.write(line)

line = 'Study Assay Technology Type Term Accession Number' + empty_types + '\n'
fp_i.write(line)
line = 'Study Assay Technology Type Term Source REF' + empty_types + '\n'
fp_i.write(line)
line = 'Study Assay Technology Platform' + empty_types + '\n'
fp_i.write(line)

fp_i.close()