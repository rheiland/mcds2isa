#!/usr/bin/python

import MultiCellDS
import sys
import csv
import lxml
from time import gmtime, strftime
import datetime

from xml.dom import minidom
from xml.dom.minidom import Node

def remove_blanks(node):
    for x in node.childNodes:
        if x.nodeType == Node.TEXT_NODE:
            if x.nodeValue:
                x.nodeValue = x.nodeValue.strip()
        elif x.nodeType == Node.ELEMENT_NODE:
            remove_blanks(x)
            
# Run this program like:
# python update_citation_text.py file1.xml file2.xml ...

for i in range(len(sys.argv)) :
    if i > 0 :
        xml = open(sys.argv[i]).read()

        result = MultiCellDS.CreateFromDocument(xml)

        csvfile = open("../../Collections/MultiCellDB ID numbers.csv","r")
        dcl_id_dict = {}
        with open('../../Collections/MultiCellDB ID numbers.csv', 'rb') as f:
            reader = csv.reader(f)
            reader.next() # Skip header row
            for row in reader:
                #print row
                row_entry = row[0:2]
                row_entry.extend(row[4:6])
                dcl_id_dict[row[1]] = row_entry

        name = result.cell_line[0].metadata.MultiCellDB.name
        label = result.cell_line[0].label
        old_citation_text = result.cell_line[0].metadata.citation.text
        MultiCellDB_name = ""
        MultiCellDB_ID = ""
        MultiCellDB_line = 0
        dict_name = ""
        if name in dcl_id_dict:
            dict_name = name
        if label in dcl_id_dict:
            dict_name = label
        print(name, label, dict_name)

        MultiCellDB_classification = dcl_id_dict[dict_name][2]
        MultiCellDB_ID = dcl_id_dict[dict_name][3]
        MultiCellDB_line = dcl_id_dict[dict_name][0]

        new_indent = '\n\t\t\t\t\t'
        new_string = new_indent+'If this digital cell line is used in a publication, cite it as:'+new_indent+("'We used digital cell line %s [1] version 1 (MultiCellDB_ID: %s) created with data and contributions from [2]'" % (dict_name, MultiCellDB_ID) ) + new_indent + "[1] S. H. Friedman et al., MultiCellDS: a standard and a community for sharing multicellular data (2016, submitted)" + new_indent + "[2] Baldock AL, Yagle K, Born DE, Ahn S, Trister AD, Neal M, et al. Invasion and proliferation kinetics in enhancing gliomas predict IDH1 mutation status. Neuro Oncol. 2014 Jun;14(6):779-86. DOI: 10.1093/neuonc/nou027"+new_indent[:-1]

        result.cell_line[0].metadata.citation.text = new_string
        result.cell_line[0].metadata.curation.classification.classification_number = MultiCellDB_classification
        result.cell_line[0].metadata.curation.classification.line = MultiCellDB_line
        result.cell_line[0].metadata.MultiCellDB.ID = MultiCellDB_ID

        time = datetime.datetime.now().isoformat()
        tz_str = strftime("%z", gmtime())
        tz_str = tz_str[:-2]+':'+tz_str[-2:] # Insert : before last two digits
        last_modified_time = time+tz_str
        result.cell_line[0].metadata.curation.last_modified = last_modified_time

        xml_ugly = result.toxml(encoding="utf-8")
        #xml_parser = lxml.etree.XMLParser(remove_blank_text=True)
        #new_root = lxml.etree.fromstring(xml_ugly, parser=xml_parser)
        #xml_better = lxml.etree.tostring(new_root, pretty_print=True, encoding="utf-8", with_tail=False)

        ugly_dom = minidom.parseString(xml_ugly)
        remove_blanks(ugly_dom)
        ugly_dom.normalize()
        xml_good = ugly_dom.toprettyxml(encoding="utf-8")
        
        #result.cell_line[0].metadata.custom.toxml(encoding="utf-8",root_only=True).translate(None,'\n\t').decode("utf-8").encode("ascii","ignore")


        fout = open(sys.argv[i],'w')
        fout.write(xml_good)
#        fout.write(result.toDOM().toprettyxml(encoding="utf-8"))
        fout.close()

        fout = open(MultiCellDB_ID+".xml",'w')
        fout.write(xml_good)
#        fout.write(result.toDOM().toprettyxml(encoding="utf-8"))
        fout.close()
        
