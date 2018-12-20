# Clean up (remove) all previously generated ISA files from the repo.
import fnmatch
import os
import sys

ftypes=['i_*.txt', 's_*.txt', 'a_*.txt']

count = 0
for root, dirnames, filenames in os.walk("."):
  for ftype in ftypes:
    for fname in fnmatch.filter(filenames, ftype):
      count += 1
      cmd = "git rm " + os.path.join(root,fname)
      print(cmd)
      os.system(cmd)
#      if (count > 9):
#        sys.exit(0)

