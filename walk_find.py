import fnmatch
import os
import sys

ftypes=['*.xml', 'i_*.txt', 's_*.txt', 'a_*.txt']
ftypes=['*.xml']
ftypes=['i_*.txt']
ftypes=['s_*.txt']
ftypes=['a_*.txt']
#matches =[]
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

idx=0
for xf in xml_:
  s= xf[:-4]
  jdx = s.rfind('/')  # assume *nix system
  bname = s[jdx+1:]  # base name

  print('---- check i_ filename match for: ',xf)
  # check that an "i_" name matches the base name
  s= i_[idx]
  s= s[:-4]
  jdx = s.rfind('/')
  iname = s[jdx+3:]
#  print(bname,'--->',iname)
  if (bname != iname):
    print('arrgh: ',bname,iname,xf)
    sys.exit(1)

  print('---- check s_ filename match')
  # check that an "s_" name matches the base name
  s= s_[idx]
  s= s[:-4]
  jdx = s.rfind('/')
  sname = s[jdx+3:]
#  print(bname,'--->',sname)
  if (bname != iname):
    print('arrgh: ',bname,sname,xf)
    sys.exit(1)

  print('---- check a_ filename match')
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
