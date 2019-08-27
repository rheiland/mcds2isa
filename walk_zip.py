# Walk through all subdirs and bundle an "archive" for *each* DCL. 
# Each archive file (.zip) consists of 4 files: the original MCDS file (.xml), and the 3 generated ISA (i_,s_,a_) files.
#
# Author: Randy Heiland
#
import fnmatch
import os
import sys
import zipfile
import shutil

# No longer used.
# ftypes=['*.xml', 'i_*.txt', 's_*.txt', 'a_*.txt']
# ftypes=['*.xml']
# ftypes=['i_*.txt']
# ftypes=['s_*.txt']
# ftypes=['a_*.txt']
#matches =[]

#  walk through all dirs and gather filenames into 4 lists
xml_ =[]
i_ =[]
s_ =[]
a_ =[]
for root, dirnames, filenames in os.walk("."):
  for fname in fnmatch.filter(filenames, '*.xml'):
    xml_.append(os.path.join(root,fname))
#print(xml_)
print('# xml =',len(xml_))

for root, dirnames, filenames in os.walk("."):
  for fname in fnmatch.filter(filenames, 'i_*.txt'):
    i_.append(os.path.join(root,fname))
#print(i_)
print('# i_ =',len(i_))

for root, dirnames, filenames in os.walk("."):
  for fname in fnmatch.filter(filenames, 's_*.txt'):
    s_.append(os.path.join(root,fname))
#print(s_)
print('# s_ =',len(s_))

for root, dirnames, filenames in os.walk("."):
  for fname in fnmatch.filter(filenames, 'a_*.txt'):
    a_.append(os.path.join(root,fname))
#print(a_)
print('# a_ =',len(a_))


#------------ Don't both with this after going with 5 "a_*" files
if False:
 print("\n---- Verifying filenames found in all 4 lists")
 count = 0
 for xf in xml_:
  # print('\n',xf)
  s= xf[:-4]
  # print(s)
  jdx = s.rfind('/')  # assume *nix system
#  kdx = s.find('/')  # assume *nix system
  bname = s[jdx+1:]  # base name
  i_name = s[:jdx+1] + "i_" + bname + ".txt"
  s_name = s[:jdx+1] + "s_" + bname + ".txt"
  a_name = s[:jdx+1] + "a_" + bname + ".txt"
#  print('bname=',bname)
#  print('i_name=',i_name)
  if i_name not in i_:
    print(count,") missing ",i_name)
    sys.exit(1)
  if s_name not in s_:
    print(count,") missing ",s_name)
    sys.exit(1)
  if a_name not in a_:
    print(count,") missing ",a_name)
    sys.exit(1)

  count += 1
#  if idx > 5:
#    break



# step through all files in our lists, zip them together, and move them into their own directory (/zip_files)
idx = 0
cwd = os.getcwd()
zip_dir =  os.path.join(cwd,"zip_files")
 
#   For example, we want: 
# xml file= ./PSON/MCF10-A.xml
# MCF10-A.xml
# MCF10-A.zip
# ./PSON/MCF10-A.xml
# isafiles= ['MCF10-A.xml', 'i_MCF10-A.txt', 's_MCF10-A.txt', 'a_MCF10-A.txt']

for xf in xml_:
#  print('xml file=',xf)
  #bname= os.path.basename(xf)
  bname= os.path.basename(xf)[:-4]
#  print("bname=",bname)
#  zfile = os.path.basename(xf)[:-3] + ".zip"
  zfile = bname + ".zip"
#  print("zfile=",zfile)
#  fns = [xf, i_[idx], s_[idx], a_[idx]]

#  s= xf[:-4]
  i_name = "i_" + bname + ".txt"
  s_name = "s_" + bname + ".txt"
  fns = [xf, i_name, s_name]

  dirp = os.path.dirname(fns[0])   # get dir path to the .xml file
  print('dirp=',dirp)

#  a_name = "a_" + bname + ".txt"
  a_name1 = "a_" + bname + "-cellMicroenvironmentAssay.txt"
  a_name2 = "a_" + bname + "-cellCycleAssay.txt"
  a_name3 = "a_" + bname + "-cellDeathAssay.txt"
  a_name4 = "a_" + bname + "-cellMechanicsAssay.txt"
  a_name5 = "a_" + bname + "-cellMotilityAssay.txt"
  a_files = [a_name1,a_name2,a_name3,a_name4,a_name5]
  for af in a_files:
#    print("af=",af)
    full_af =  os.path.join(dirp,af)
#    print("full_af=",full_af)
    if os.path.isfile(full_af):
      fns.append(af)
#    else:
#      print('-- not a file?!')

#  fns = [xf, i_name, s_name, a_name1,a_name2,a_name3,a_name4,a_name5 ]
#  print("idx=",idx, ", fns=",fns)

#  print(os.path.expanduser(fns[0]))

  isafiles = list(map(os.path.basename, fns))
#  print()
#  print("isafiles=",isafiles)

#  dirp = os.path.dirname(fns[0])
#  print('dirp=',dirp)
#  sys.exit(0)
  os.chdir(dirp)

  with zipfile.ZipFile(zfile, 'w') as myzip:
#    myzip.write(f)
    for f in isafiles:
      myzip.write(f)

  shutil.move(zfile, zip_dir)
  os.chdir(cwd)

  if (idx > 500):
#  if (idx > 0):
    sys.exit(1)

  idx += 1
