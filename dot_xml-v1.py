# Walk a .xml file and generate a .dot file for Graphviz
#
# Randy Heiland
#
import xml.etree.ElementTree as ET
import sys

tree = ET.parse('/Users/heiland/git/mcds2isa/HUVEC/HUVEC_v4_SHF_test.xml')
root = tree.getroot()

num_nodes = 0
#for node in root.iter():
for node in []:
  print(node)
  num_nodes += 1
#print("num_nodes=",num_nodes)

#print('----- recursive -----')
print('digraph huvec {')
#prefix = ""
def print_children(parent):
  global prefix
  for child in parent:
    print('"',parent.tag,'"->"',child.tag,'"')
#    prefix = prefix + "--"
    print_children(child)
#  prefix = prefix - "--"
  # prefix = prefix[2:]

print_children(root)
print('}')

sys.exit(1)  #  <---- exit

#---- Not doing this --------
print('-----------------------')
for child in root:
  print(child.tag)
  for child2 in child:
    print('--',child2.tag)
    for child3 in child2:
      print('----',child3.tag)
      for child4 in child3:
        print('------',child4.tag)
#  print(child.tag, child.attrib)
