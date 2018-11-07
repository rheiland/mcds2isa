Welcom to MultiCellDB, the MultiCellular DataBase, for Digital Cell Lines!

# Digital Cell Lines (DCLs)

Digital Cell Lines (DCLs) are digital analogues of traditional cell
lines. The database supports both curated and uncurated DCLs.

To organize all of the DCLs, we have adopted a hierarchical structure
that we represent (in this incarnation of MultiCellDB) via a directory
structure that represents how version numbers are assigned to the
DCLs.

## Digital Cell Line Numbering Scheme

MultiCellDS takes inspiration from version control software, such as
git, to handle different DCLs.

Each Digital Cell Line has the following version numbering scheme:

Line.Variant.Branch.Version

where each number is an integer and Line is [1,inf), Variant is
[0,inf), Branch is [0,inf), and Version is [1,inf). We may at some
point in the future introduce a different version numbering scheme.

Variant #0 and Branch #0 are special "master branches." For the master
variant branch, this represents the idealized form of that cell line
(e.g. *E. coli*). The master branch represents aggregated measurements
across different branches. The curator(s) for each Line should dictate
when DCLs from non-master variants and non-master branches get merged
into the master variant or branch respectively.

## Directory Structure

Replicating the numbering scheme, we have the following directory
structure:

* Line
    * Variant
        * Branch
            * Version

# Master numbering scheme 

The Core Committee of MultiCellDS will maintain a list assigning cell
line numbers.
  
