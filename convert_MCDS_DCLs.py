#
# convert_MCDS_DCLs.py - process all subdirectories of MultiCellDS Digital Cell Lines and convert
#      each one (*.xml) to ISA-Tab formatted files ({i_,s_,a_}*.txt). Write (move) to same directory.
#
#      Downloaded MCDS DCLs from https://gitlab.com/MultiCellDS/Digital_Cell_Lines.
# 
# Author: Randy Heiland
#
import os
import sys
import glob
import shutil 

count = 0
for root, dirs, files in os.walk("."):
    path = root.split(os.sep)
    #print((len(path) - 1) * '---', os.path.basename(root))
    for file in files:
      if (file[-3:] == 'xml'):
#        os.chdir(root)  # let's NOT attempt this approach

#         print(root)
#         print(file)
         count += 1
         # edit the following path accordingly
#         cmd = "python ../isaTABModelledFiles/mcds_dcl2isa.py " + os.path.join(root,file)
         cmd = "python mcds_dcl2isa.py " + os.path.join(root,file)
         print(cmd)
         os.system(cmd)
         for isa_file in glob.glob(r'*.txt'):
#            print("mv ",isa_file,root)
            shutil.move(isa_file,root)
#         if (count > 5):
#         sys.exit()

