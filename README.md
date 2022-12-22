# RaSP_workflow
See guides in docs for Bioinfo01, 03, and 04 specific installation and use guides.

## RaSP - The original Tool

### citation:
```
Rapid protein stability prediction using deep learning representations
Lasse M. Blaabjerg, Maher M. Kassem, Lydia L. Good, Nicolas Jonsson, Matteo Cagiada, Kristoffer E. Johansson, Wouter Boomsma, Amelie Stein, Kresten Lindorff-Larsen
bioRxiv 2022.07.14.500157; doi: https://doi.org/10.1101/2022.07.14.500157 
```
The scripts to re-run the paper and data can be found at
```
https://github.com/KULL-Centre/papers/tree/main/2022/ML-ddG-Blaabjerg-et-al
```
The tool can be run directly at
```
https://colab.research.google.com/github/KULL-Centre/papers/blob/main/2022/ML-ddG-Blaabjerg-et-al/RaSPLab.ipynb
```

Below is the installation and use guides for a free standing version of RaSP:

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
conda install pdbfixer=1.5 openmm=7.3.1 -c omnia -c conda-forge -c anaconda -c defaults --yes
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

If an existing pdb is used, it needs to be present in the working directory.

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
