# mcds2isa

This repo contains a Python script (mcds_dcl2isa.py) to convert MultiCellDS digital cell line files (.xml) to ISA-Tab files ({i_,s_,a_}*.txt). It also contains another Python script (convert_MCDS_DCLs.py) that will "walk" through an entire directory of MCDS DCL files and invoke the conversion script to generate the three ISA files in the same directory as the corresponding MCDS file.

It also provides a script for verifying we have i_,s_,a_ (.txt) triples for each .xml file. And it provides a script for zip'ing each set of i_,s_,a_ triples into compressed (.zip) files.

A couple of issues came to light during this process. First, for two of the .xml files, our conversion script seemed to only generate an i_ file (not s_ and a_ files):
```
All_Digital_Cell_Lines/i_1.0.0.1.txt
All_Digital_Cell_Lines/i_S_00000001.txt
```
So those files were removed. Second, during the zip process, we discovered that we have one duplicate .xml base filename:
```
~/git/mcds2isa$ python walk_zip.py
...
Traceback (most recent call last):
  File "walk_zip.py", line 113, in <module>
    shutil.move(zfile, zip_dir)
  File "/Users/heiland/anaconda3/lib/python3.6/shutil.py", line 542, in move
    raise Error("Destination path '%s' already exists" % real_dst)
shutil.Error: Destination path '/Users/heiland/git/mcds2isa/zip_files/MDA_MB_231.zip' already exists
~/git/mcds2isa$ find . -name MDA_MB_231.xml
./ATCC/MDA_MB_231/MDA_MB_231.xml
./PSON/MDA_MB_231.xml

~/git/mcds2isa$ ll zip_files/|wc -l
     469
     
~/git/mcds2isa$ ll zip_files/|sort|head
-rw-r--r--  1 heiland  staff  5848 Dec  6 06:03 s_aureus.zip
-rw-r--r--  1 heiland  staff  5929 Dec  6 06:03 MCDS_L_0000000046.zip
-rw-r--r--  1 heiland  staff  5939 Dec  6 06:03 e_coli.zip
-rw-r--r--  1 heiland  staff  5998 Dec  6 06:03 VCAP.zip
-rw-r--r--  1 heiland  staff  6030 Dec  6 06:03 MCDS_L_0000000002.zip
-rw-r--r--  1 heiland  staff  6038 Dec  6 06:03 MCDS_L_0000000045.zip
-rw-r--r--  1 heiland  staff  6046 Dec  6 06:03 NL20.zip
-rw-r--r--  1 heiland  staff  6052 Dec  6 06:03 MCF10-A.zip
-rw-r--r--  1 heiland  staff  6055 Dec  6 06:03 GBM_1.zip
-rw-r--r--  1 heiland  staff  6055 Dec  6 06:03 GBM_2.zip
~/git/mcds2isa$ ll zip_files/|sort|tail
-rw-r--r--  1 heiland  staff  8654 Dec  6 06:03 MCDS_L_0000000058.zip
-rw-r--r--  1 heiland  staff  8654 Dec  6 06:03 MCDS_L_0000000059.zip
-rw-r--r--  1 heiland  staff  8654 Dec  6 06:03 MCDS_L_0000000060.zip
-rw-r--r--  1 heiland  staff  8663 Dec  6 06:03 DCIS_ACP2011_18.1.zip
-rw-r--r--  1 heiland  staff  8663 Dec  6 06:03 MCDS_L_0000000054.zip
-rw-r--r--  1 heiland  staff  8664 Dec  6 06:03 DCIS_ACP2011_18.2.zip
-rw-r--r--  1 heiland  staff  8664 Dec  6 06:03 MCDS_L_0000000055.zip
-rw-r--r--  1 heiland  staff  8890 Dec  6 06:03 HUVEC_v4_SHF_test.zip
-rw-r--r--  1 heiland  staff  8890 Dec  6 06:03 MCDS_L_0000000043.zip

```
