#!/usr/bin/python
# There's a problem with the XML. Cannot use XML software because it is not well formed.
import sys

for i in range(len(sys.argv)) :
    if i > 0 :
        f = open(sys.argv[i],"r")

        file_contents = f.read()
        f.close()

        #rho_over_d = "<rho_over_d"
        old_units = "units "
        new_units ="units="
        file_contents = file_contents.replace(old_units, new_units)
        f = open(sys.argv[i], "w")
        f.write(file_contents)
        f.close()

        # Run like
        # ls *.xml | xargs python fix_GBM.py 
        
        
