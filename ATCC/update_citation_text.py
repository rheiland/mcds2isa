#!/usr/bin/python

import MultiCellDS
import sys
import csv
from time import gmtime, strftime
import datetime


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
        new_string = new_indent+'If this digital cell line is used in a publication, cite it as:'+new_indent+("'We used digital cell line %s [1] version 1 (MultiCellDB_ID: %s) created with data and contributions from [2]'" % (dict_name, MultiCellDB_ID) ) + new_indent + "[1] S. H. Friedman et al., MultiCellDS: a standard and a community for sharing multicellular data (2016, submitted)" + new_indent + "[2] Juarez, E. F. et al. Quantifying differences in cell line population dynamics using CellPD. BMC Systems Biology 10, 92, doi:10.1186/s12918-016-0337-5 (2016)."+new_indent[:-1]

        result.cell_line[0].metadata.citation.text = new_string
        result.cell_line[0].metadata.curation.classification.classification_number = MultiCellDB_classification
        result.cell_line[0].metadata.curation.classification.line = MultiCellDB_line
        result.cell_line[0].metadata.MultiCellDB.ID = MultiCellDB_ID

        time = datetime.datetime.now().isoformat()
        tz_str = strftime("%z", gmtime())
        tz_str = tz_str[:-2]+':'+tz_str[-2:] # Insert : before last two digits
        last_modified_time = time+tz_str
        result.cell_line[0].metadata.curation.last_modified = last_modified_time


        fout = open(sys.argv[i],'w')
        fout.write(result.toDOM().toprettyxml())
        fout.close()

        fout = open(MultiCellDB_ID+".xml",'w')
        fout.write(result.toDOM().toprettyxml())
        fout.close()
        
