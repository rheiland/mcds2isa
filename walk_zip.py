import fnmatch
import os
import sys
import zipfile
import shutil

ftypes=['*.xml', 'i_*.txt', 's_*.txt', 'a_*.txt']
ftypes=['*.xml']
ftypes=['i_*.txt']
ftypes=['s_*.txt']
ftypes=['a_*.txt']
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


# --- Verify we have an i_,s_,a_ (.txt) triple for each .xml 
# (if not, remove those that don't)
idx=0
for xf in xml_:
  s= xf[:-4]
  jdx = s.rfind('/')  # assume *nix system
  bname = s[jdx+1:]  # base name

#  print('---- check i_ filename match for: ',xf)
  # check that an "i_" name matches the base name
  s= i_[idx]
  s= s[:-4]
  jdx = s.rfind('/')
  iname = s[jdx+3:]
#  print(bname,'--->',iname)
  if (bname != iname):
    print('arrgh: ',bname,iname,xf)
    sys.exit(1)

#  print('---- check s_ filename match')
  # check that an "s_" name matches the base name
  s= s_[idx]
  s= s[:-4]
  jdx = s.rfind('/')
  sname = s[jdx+3:]
#  print(bname,'--->',sname)
  if (bname != iname):
    print('arrgh: ',bname,sname,xf)
    sys.exit(1)

#  print('---- check a_ filename match')
  # check that an "a_" name matches the base name
  s= a_[idx]
  s= s[:-4]
  jdx = s.rfind('/')
  aname = s[jdx+3:]
#  print(bname,'--->',iname)
  if (bname != iname):
    print('arrgh: ',bname,iname,xf)
    sys.exit(1)

  idx += 1


# step through all files in our lists, zip them together, and move them into their own directory (/zip_files)
idx = 0
cwd = os.getcwd()
zip_dir =  os.path.join(cwd,"zip_files")
 
for xf in xml_:
  print('xml file=',xf)
  print(os.path.basename(xf))
  zfile = os.path.basename(xf)[:-3] + "zip"
  print(zfile)
  fns = [xf, i_[idx], s_[idx], a_[idx]]
#  print(idx, fns)
  print(os.path.expanduser(fns[0]))

  isafiles=list(map(os.path.basename, fns))
  print(isafiles)

  dirp=os.path.dirname(fns[0])
  os.chdir(dirp)

  with zipfile.ZipFile(zfile, 'w') as myzip:
#    myzip.write(f)
    for f in isafiles:
      myzip.write(f)

  shutil.move(zfile, zip_dir)
  os.chdir(cwd)

  if (idx > 500):
    sys.exit(1)

  idx += 1


