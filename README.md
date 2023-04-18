# RaSP_workflow
This pipeline is an adapted version of the Rapid protein stability prediction (RaSP) tool. In summary, this limited version allows the user to run RaSP from the command line keeping the naming conventions of files and allow limiting the core usage. 

## RaSP

### citation:
```
Rapid protein stability prediction using deep learning representations
Lasse M. Blaabjerg, Maher M. Kassem, Lydia L. Good, Nicolas Jonsson, Matteo Cagiada, Kristoffer E. Johansson, Wouter Boomsma, Amelie Stein, Kresten Lindorff-Larsen
bioRxiv 2022.07.14.500157; doi: https://doi.org/10.1101/2022.07.14.500157 
```
The scripts to re-run the paper and data can be found at:
```
https://github.com/KULL-Centre/_2022_ML-ddG-Blaabjerg
```
The tool can be run directly at:
```
https://colab.research.google.com/github/KULL-Centre/papers/blob/main/2022/ML-ddG-Blaabjerg-et-al/RaSPLab.ipynb
```

Below is the installation and use guides for a free standing workflow version of RaSP:

## Installation

### Using conda 

```
conda create --name rasp
conda activate rasp
```
### Clone This GitHub

```
git clone https://github.com/ELELAB/RaSP_workflow.git
```

### INSTALL DEPENDENCY PACKAGES
```
conda install --channel defaults conda python=3.7 --yes
conda update --channel defaults --all --yes
pip install numpy==1.17.3 pandas==1.3.5 torch==1.2.0 biopython==1.72 pdb-tools
pip install --upgrade pdb-tools
conda install pdbfixer=1.8.1 openmm=7.7.0 -c conda-forge --yes
conda install -c anaconda scikit-learn=1.0.2
```

### CLONE ADDITIONAL DEPENDENCIES
```
cd RaSP_workflow/src/pdb_parser_scripts
git clone https://github.com/rlabduke/reduce.git
cd reduce/
make
mv reduce_src/reduce .
cd ../../../
chmod +x src/pdb_parser_scripts/reduce/reduce

```

## Running
```
$ RaSP_workflow [flags]
```

### Flags and Options
* -t [INPUT TYPE]

```
There are three modes of running RaSP:
        1) with a uniprot id to download the AlphaFold model
        2) with a PDB id to download a PDB model
        3) with a file name to run RaSP on an existing PDB file.

In each case, this should be defined with the input type [-t].
 ex. -t FILE for an existing pdb file.
 ex. -t AF to download a new Alphafold Sturcture
 ex. -t PDB to download a new PDB structure. 

Per default FILE is used, hence you can ommit this flag if you use an existing file.

```


* -i [INPUT FILE]

```
There are three modes of running RaSP:
	1) with a uniprot id to download the AlphaFold model
	2) with a PDB id to download a PDB model
	3) with a file name to run RaSP on an existing PDB file.

This is defined using the flag [-i] input pdb
 ex.  -i P62942 for the alphafold model
 ex.  -i 2XWR for the pdb model
 ex.  -i 2PPN.pdb for an existing structure. 

If an existing pdb is used, it needs to be present in the working directory or data/input/

```

* -c [CHAIN NAME]

```
RaSP can only take one chain at a time as input. The chain name 
should be defined using -c chain. 

 ex. -c A
 ex. -c B
```

* -v [ALPHAFOLD VERSION] 

```
When an AlphaFold model is downloaded the version can be defined 
using the -v version flag. This is optional. Per default version 4. 
```

* -r [RUNTYPE]

```
RaSP have two runtypes, cpu and cuda. Cuda is a gpu type. 

```
* -n [cores]

```
RaSP can be run on multiple cores, specify using n.

```
* -p [PATH]
```

The src directory containing the scripts, model and all additional
data, can be specified using the command -p. Per default this is
./src, but can be changed to any other path

### Output

After a successful run, the output files are deposited: 

```
output/predictions/
```

The file is named based on the input code. If you used a pre-existing pdb
the name will be CUSTOM, and you may wish to rename the file. 

using the first example run with P62942 as an output example,
the output files are: 

```
output/predictions/cavity_pred_P62942_A.csv  
output/predictions/prism_cavity_P62942_A.txt 
```

To see the estimated ddG, we examine the csv file: 
```
pdbid,chainid,variant,wt_idx,mt_idx,wt_nlf,mt_nlf,score_ml_fermi,score_ml,pos,wt_AA,mt_AA,wt
P62942,A,M1A,10,0,3.785956884138847,2.4839824262174384,0.2559438,0.33210336415230135,1,M,A,M
P62942,A,M1C,10,1,3.785956884138847,4.335140045203785,0.29353338,0.8042885819152235,1,M,C,M
P62942,A,M1D,10,2,3.785956884138847,2.8246796259135976,0.22557239,-0.08370761983215846,1,M,D,M
P62942,A,M1E,10,3,3.785956884138847,2.712832422359037,0.24662709,0.2082927845099386,1,M,E,M
P62942,A,M1F,10,4,3.785956884138847,3.2079371983380796,0.25724873,0.34920552719755193,1,M,F,M
P62942,A,M1G,10,5,3.785956884138847,2.5602131485714543,0.27896655,0.6260158311485233,1,M,G,M
P62942,A,M1H,10,6,3.785956884138847,3.772712370515455,0.23301259,0.02155520521038179,1,M,H,M
```

The mutation is available in the variant column and the esitmated ddG is available in the score_ml column. 

To post process this file and convert to mutatex and rosetta compatible formatting you can use: 

```
$ RaSP_postprocess -i cavity_pred_{identifier}_{chain}.csv
```
e.g.:

```
$ RaSP_postprocess -i output/predictions/cavity_pred_P62942_A.csv
```
The output will also be available in output/predictions/.
```

## License
Source code and model weights are licensed under the Apache Licence, Version 2.0.
