import fnmatch
import os
import sys

"""  NOT USED NOW
ftypes=['*.xml', 'i_*.txt', 's_*.txt', 'a_*.txt']
ftypes=['*.xml']
ftypes=['i_*.txt']
ftypes=['s_*.txt']
ftypes=['a_*.txt']
"""
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


print("\n---- Verifying filenames found in all 4 lists")
idx = 0
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
    print("missing ",i_name)
    break
  if s_name not in s_:
    print("missing ",s_name)
    break
  if a_name not in a_:
    print("missing ",a_name)
    break

  idx += 1
#  if idx > 5:
#    break

sys.exit(0)

#------------- old (wrong) test
# NOTE! there's no guarantee of base filenames being in same order in each list.
# For example, we get the following - see 4th entries mismatching:
# argh 1:  GBM_TCGA-08-0354 GBM_TCGA-06-0179 ./GBM/GBM_TCGA-08-0354.xml
# ['./PSON/MCF10-A.xml', './Lymphoma/Arf_null/arf_null_v3.xml', './Lymphoma/p53_null/p53_null_v3.xml', './HUVEC/HUVEC_v4_SHF_test.xml', './GBM/GBM_TCGA-08-0354.xml', './GBM/GBM_TCGA-02-0009.xml', './GBM/GBM_16.xml', './GBM/GBM_TCGA-06-0188.xml']
# ['./PSON/i_MCF10-A.txt', './Lymphoma/Arf_null/i_arf_null_v3.txt', './Lymphoma/p53_null/i_p53_null_v3.txt', './HUVEC/i_HUVEC_v4_SHF_test.txt', './GBM/i_GBM_TCGA-06-0179.txt', './GBM/i_GBM_TCGA-06-0145.txt', './GBM/i_GBM_TCGA-06-0192.txt', './GBM/i_GBM_29.txt']

idx=0
print("---- verify filenames match up")
for xf in xml_:
  print('\n',xf)
  s= xf[:-4]
  print(s)
  jdx = s.rfind('/')  # assume *nix system
  bname = s[jdx+1:]  # base name
  print(bname)
  print('bname=',bname)

  print('---- check i_ filename match for: ',xf)
  # check that an "i_" name matches the base name
  s= i_[idx]
  s= s[:-4]
  jdx = s.rfind('/')
  iname = s[jdx+3:]
  print('iname=',iname)

  print(bname,'--->',iname)
  if (bname != iname):
    print('argh 1: ',bname,iname,xf)
    print('idx=',idx)
    print(xml_[0:idx+4])
    print(i_[0:idx+4])
    sys.exit(1)

  print('---- check s_ filename match')
  # check that an "s_" name matches the base name
  s= s_[idx]
  s= s[:-4]
  jdx = s.rfind('/')
  sname = s[jdx+3:]
#  print(bname,'--->',sname)
  if (bname != iname):
    print('argh 2: ',bname,sname,xf)
    sys.exit(1)

  print('---- check a_ filename match')
  # check that an "a_" name matches the base name
  s= a_[idx]
  s= s[:-4]
  jdx = s.rfind('/')
  aname = s[jdx+3:]
#  print(bname,'--->',iname)
  if (bname != iname):
    print('argh 3: ',bname,iname,xf)
    sys.exit(1)

  idx += 1
