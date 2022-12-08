import sys
#sys.path.append("/usr/local/lib/python3.7/site-packages")
import glob
import os
import random
#import pathlib
import subprocess
import numpy as np
import pandas as pd
import torch
import time
import datetime
#import matplotlib
#from pdbfixer import PDBFixer
#from simtk.openmm.app import PDBFile
from Bio.PDB.Polypeptide import index_to_one, one_to_index
#from collections import OrderedDict
#from torch.utils.data import DataLoader, Dataset
#import yaml
import argparse

#from google.colab import files
sys.path.append('./src/')

from cavity_model import (
     CavityModel,
     DownstreamModel,
#     ResidueEnvironment,
     ResidueEnvironmentsDataset,
)

from helpers import (
#     populate_dfs_with_resenvs,
#     remove_disulfides,
#     fermi_transform,
#     inverse_fermi_transform,
     init_lin_weights,
     ds_pred,
     cavity_to_prism,
     get_seq_from_variant,
)

#from visualization import (
#     hist_plot,
#)

# prepare parameters
parser = argparse.ArgumentParser(prog = "RaSP_workflow",
                                 usage = 'RaSP_workflow [-h] help')

parser.add_argument("-i", '--input',
                    metavar = 'input pdb or code',
                    type=str,
                    help='The name of the input pdb, either a file or a AF (uniprot) or PDB code')

parser.add_argument("-c", '--chain',
                    metavar = 'chain for saturation mutagenesis',
                    type=str,
                    help='The chain to be analyzed')

parser.add_argument("-v", '--version',
                    metavar = 'version of the AlphaFold model to be analyzed',
                    type=int,
                    default=4,
                    help='The AF version to be analyzed')

parser.add_argument("-r", "--runtype",
                    metavar = "cpu or cuda",
                    type=str,
                    default = 'cpu',
                    help="RaSP can run on either cuda or cpu")

args = parser.parse_args()

pdb_input = args.input

if pdb_input[-4:].lower() == '.pdb':
    PDB_custom = pdb_input
else: PDB_custom = ''

if len(pdb_input) == 4:
    PDB_ID = pdb_input
else: PDB_ID = ''

if len(pdb_input) == 6:
    AF_ID = pdb_input
else: AF_ID = ''

version = int(args.version)

chain = args.chain

runtype = args.runtype


# Setup pipeline with parameters
## Set seeds
np.random.seed(0)
random.seed(0)
torch.manual_seed(0)
if runtype == 'cuda':
    torch.cuda.manual_seed(0)
    torch.cuda.manual_seed_all(0)
torch.backends.cudnn.enabled = False
torch.backends.cudnn.benchmark = False
torch.backends.cudnn.deterministic = True

## Main deep parameters
DEVICE = runtype # "cpu" #"cuda"  # "cpu" or "cuda"
NUM_ENSEMBLE = 10
TASK_ID = int(1)
PER_TASK = int(1)

#clean up
if os.path.exists("query_protein.pdb"):
    os.remove("query_protein.pdb")
if os.path.exists("data/test/predictions/raw/query_protein_uniquechain.pdb"):
    os.remove("data/test/predictions/raw/query_protein_uniquechain.pdb")
if os.path.exists("data/test/predictions/cleaned/query_protein_uniquechain_clean.pdb"):
    os.remove("data/test/predictions/cleaned/query_protein_uniquechain_clean.pdb")
if os.path.exists("data/test/predictions/parsed/query_protein_uniquechain_clean_coordinate_features.npz"):
    os.remove("data/test/predictions/parsed/query_protein_uniquechain_clean_coordinate_features.npz")

#load pdb
if (AF_ID !=''): 
    subprocess.call(['curl','-s','-f',f'https://alphafold.ebi.ac.uk/files/AF-{AF_ID}-F1-model_v{version}.pdb','-o','query_protein.pdb'])
    print("ALPHAFOLD downloaded")
elif (PDB_ID !=''):
    subprocess.call(['curl','-s','-f',f'https://files.rcsb.org/download/{PDB_ID}.pdb','-o','query_protein.pdb'])
    print("PDB downloaded")

elif PDB_custom:
  os.rename(PDB_custom, "query_protein.pdb")
  print('PDB file correctly loaded')

else:
  print('ERROR: Please select input')

os.system(f"pdb_selchain -{chain} query_protein.pdb | pdb_delhetatm | pdb_delres --999:0:1 | pdb_fixinsert | pdb_tidy  > data/test/predictions/raw/query_protein_uniquechain.pdb")

pdb_input_dir = "data/test/predictions/raw/"
input_pdbs = sorted(list(filter(lambda x: x.endswith(".pdb"), os.listdir('data/test/predictions/raw/'))))
start = (TASK_ID-1)*(PER_TASK)
end = (TASK_ID*PER_TASK)
if end > len(input_pdbs):
    end = len(input_pdbs) #avoid end index exceeding length of list
pdbs = input_pdbs[start:end] 
pdb_names = [i.split(".")[0] for i in pdbs]
print("Pre-processing PDBs ...")

os.system("python src/pdb_parser_scripts/clean_pdb.py --pdb_file_in data/test/predictions/raw/query_protein_uniquechain.pdb --out_dir data/test/predictions/cleaned/ --reduce_exe src/pdb_parser_scripts/reduce/reduce") #&> /dev/null
os.system("python src/pdb_parser_scripts/extract_environments.py --pdb_in data/test/predictions/cleaned/query_protein_uniquechain_clean.pdb  --out_dir data/test/predictions/parsed/")  #&> /dev/null

if os.path.exists("data/test/predictions/parsed/query_protein_uniquechain_clean_coordinate_features.npz"):
  print("Pre-processing PDBs correctly ended")
else:
  print("Pre-processing PDB didn't end correcly, please check input informations")


print("#################### PREPARE RUN #####################")

pdb_filenames_ds = sorted(glob.glob("data/test/predictions/parsed/*coord*"))

dataset_structure = ResidueEnvironmentsDataset(pdb_filenames_ds, transformer=None)

resenv_dataset = {}

for resenv in dataset_structure:
    if AF_ID!='':
      key = (f"--{AF_ID}--{resenv.chain_id}--{resenv.pdb_residue_number}--{index_to_one(resenv.restype_index)}--"
          )
    elif PDB_ID!='':
      key = (f"--{PDB_ID}--{resenv.chain_id}--{resenv.pdb_residue_number}--{index_to_one(resenv.restype_index)}--"
          )
    else:
      key = (f"--{'CUSTOM'}--{resenv.chain_id}--{resenv.pdb_residue_number}--{index_to_one(resenv.restype_index)}--"
          )
    resenv_dataset[key] = resenv

    
df_structure_no_mt = pd.DataFrame.from_dict(resenv_dataset, orient='index', columns=["resenv"])
df_structure_no_mt.reset_index(inplace=True)
df_structure_no_mt["index"]=df_structure_no_mt["index"].astype(str)
res_info = pd.DataFrame(df_structure_no_mt["index"].str.split('--').tolist(),
                        columns = ['blank','pdb_id','chain_id','pos','wt_AA', 'blank2'])

df_structure_no_mt["pdbid"] = res_info['pdb_id']
df_structure_no_mt["chainid"] = res_info['chain_id']
df_structure_no_mt["variant"] = res_info["wt_AA"] + res_info['pos'] + "X"
aa_list = ["A", "C", "D", "E", "F", "G", "H", "I", "K", "L", 
            "M", "N", "P", "Q", "R", "S", "T", "V", "W", "Y"]
df_structure = pd.DataFrame(df_structure_no_mt.values.repeat(20, axis=0), columns=df_structure_no_mt.columns)
for i in range(0, len(df_structure), 20):
    for j in range(20):
        df_structure.iloc[i+j, :]["variant"] = df_structure.iloc[i+j, :]["variant"][:-1] + aa_list[j]
df_structure.drop(columns="index", inplace=True)


# Load PDB amino acid frequencies used to approximate unfolded states
pdb_nlfs = -np.log(np.load("data/pdb_frequencies.npz")["frequencies"])
#pdb_nlfs = -np.log(np.load(f"{os.getcwd()}/data/pdb_frequencies.npz")["frequencies"])

# # Add wt and mt idxs and freqs to df

df_structure["wt_idx"] = df_structure.apply(lambda row: one_to_index(row["variant"][0]), axis=1)
df_structure["mt_idx"] = df_structure.apply(lambda row: one_to_index(row["variant"][-1]), axis=1)
df_structure["wt_nlf"] = df_structure.apply(lambda row: pdb_nlfs[row["wt_idx"]], axis=1)
df_structure["mt_nlf"] = df_structure.apply(lambda row: pdb_nlfs[row["mt_idx"]], axis=1)

# Define models
best_cavity_model_path = open("output/cavity_models/best_model_path.txt", "r").read()
#added line
best_cavity_model_path = best_cavity_model_path.split("/content/")[1][:-1]

cavity_model_net = CavityModel(get_latent=True).to(DEVICE)

if runtype == 'cpu':
    t = torch.load(f"{best_cavity_model_path}", map_location=torch.device('cpu'))
elif runtype == 'cuda':
    t = torch.load(f"{best_cavity_model_path}")

cavity_model_net.load_state_dict(t)

cavity_model_net.eval()
ds_model_net = DownstreamModel().to(DEVICE)
ds_model_net.apply(init_lin_weights)
ds_model_net.eval()

###set start time
start_time = time.perf_counter()

# Make ML predictions
print("Starting downstream model prediction")

print("########### RUNNING ################")

dataset_key="predictions"
df_ml = ds_pred(cavity_model_net,
                ds_model_net,
                df_structure,
                dataset_key,
                NUM_ENSEMBLE, #10
                DEVICE, #cpu
                ) 

print("Finished downstream model prediction")
end_time = time.perf_counter()
elapsed = datetime.timedelta(seconds = end_time - start_time)
print("Complete - prediction execution took", elapsed)

elapsed = datetime.timedelta(seconds = end_time - start_time)
print("Generating output files")
#Merge and save data with predictions

df_total = df_structure.merge(df_ml, on=['pdbid','chainid','variant'], how='outer')
#df_total["b_factors"] = df_total.apply(lambda row: row["resenv"].b_factors, axis=1)
df_total = df_total.drop("resenv", 1)
print(f"{len(df_structure)-len(df_ml)} data points dropped when matching total data with ml predictions in: {dataset_key}.")

# Parse output into separate files by pdb, print to PRISM format
for pdbid in df_total["pdbid"].unique():
    df_pdb = df_total[df_total["pdbid"]==pdbid]
    for chainid in df_pdb["chainid"].unique():
        pred_outfile = f"output/{dataset_key}/cavity_pred_{pdbid}_{chainid}.csv"
        #pred_outfile = f"{os.getcwd()}/output/{dataset_key}/cavity_pred_{pdbid}_{chainid}.csv"
        print(f"Parsing predictions from pdb: {pdbid}{chainid} into {pred_outfile}")
        df_chain = df_pdb[df_pdb["chainid"]==chainid]
        df_chain = df_chain.assign(pos = df_chain["variant"].str[1:-1])
        df_chain['pos'] = pd.to_numeric(df_chain['pos'])
        first_res_no = min(df_chain["pos"])
        df_chain = df_chain.assign(wt_AA = df_chain["variant"].str[0])
        df_chain = df_chain.assign(mt_AA = df_chain["variant"].str[-1])
        seq = get_seq_from_variant(df_chain)
        df_chain.to_csv(pred_outfile, index=False)
        prism_outfile = f"output/{dataset_key}/prism_cavity_{pdbid}_{chainid}.txt"
        cavity_to_prism(df_chain, pdbid, chainid, seq, prism_outfile)

# End timer and print result
elapsed = datetime.timedelta(seconds = end_time - start_time)
if PDB_custom != '':
    os.rename("query_protein.pdb", PDB_custom)
if os.path.exists("query_protein.pdb"):
    os.remove("query_protein.pdb")
print("Complete - files generated")

