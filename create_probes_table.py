"""
This script is used to create the table used in the pharmacoscan query tool.

The original table is too large to distribute. This code reads in the pharmacoscan annot file and produces a simplified version of the table with the data needed for the pharmacoscan query tool.

The columns that are extracted are listed below with descriptions as needed:
Probe Set ID
Chromosome
Physical Position - Start position on the chromosome
Ref Allele - This is different than the Allele A/B that is also in the original table. Allele A/B is the nomenclature that Thermo/Affymetrix uses for their probes to identify which color spectrum will be used. These may not match exactly with the REF/ALT base for a variant from CPIC/PharmVar depending on the strand that is used. Ref Allele and Alt  Allele columns are the columns for a variant based on the current genome build. Note that these don't follow the current vcf 4.2 format. I.e an insertion of an A after a T will be represented as REF:"-", ALT:"A" not REF:"T", ALT:"TA"
Alt Allele - see Ref Allele
Associated Gene - A variant can have multiple genes associated with it. All  genes are parsed out and are used
Probe Count
Extended RSID - The dbSNP RS ID column was not used because in order to have an rsid for that column the variant must match exactly with dbSNP. This is sometimes not possible with multiallelic variants. As an example rs3745274 has the possible G->T or G->A variants, but only G->T is used to call *9. Therefore this probe would not have an rsid listed under the dbSNP RS ID column, but it will under Extended RSID.

For more information on these columns or others please see the readme file included with the annot.csv file from Thermo's website. 

Author: Andrew Haddad
Library version: r9
"""
from datetime import datetime

import numpy as np
import pandas as pd


def split_rsids_col(data):
    # It is possible for multiple rsids to be associated with a variant
    # These are represented in the table as rsid1,rsid2,etc
    data["Extended RSID"] = data["Extended RSID"].str.split(",")
    data = data.explode("Extended RSID", ignore_index=True)
    data["Extended RSID"] = data["Extended RSID"].str.strip()
    return data


def split_up_data(data):
    # Need to split the data based on the Associated Gene column.
    # There are some probesets that are not associated with any
    # genes and these won't parse out correctly in a later step
    mod_condition = data["Associated Gene"].str.len() % 7
    # copy avoids SettingwithCopyWarning
    no_genes = data.loc[mod_condition != 0].copy()
    genes = data.loc[mod_condition == 0]
    return genes, no_genes


def split_gene_col(data):
    # The associated gene column contains the following data:
    # "transcript accession // SNP-gene relationship // distance
    # (value 0 if within the gene) // UniGene Cluster ID //
    # gene name or symbol // NCBI Gene ID // GenBank description"
    # A probeset not associated with any gene will return [---]

    data.loc[:, "Associated Gene"] = data["Associated Gene"].str.split("//")
    return data


def explode_and_filter(data):
    # Explode the gene column that was split
    # Then take every 7th row starting with the 4th index
    data = (
        data.explode("Associated Gene", ignore_index=True)
        .iloc[4::7]
        .drop_duplicates(ignore_index=True)
    )
    data.loc[:, "Associated Gene"] = data.loc[:, "Associated Gene"].str.strip()
    return data


def remove_blank_data(data):
    # Some rows are still left as duplicates because the data is represented as
    # "---" or None
    # These rows are removed in this step
    data = (
        data.replace(r"---", np.nan, regex=False)
        .replace("", np.nan, regex=False)
        .fillna(value=np.nan)
        .drop_duplicates(ignore_index=True)
    )
    return data


def _check_row_for_na(df):
    result = df.dropna(subset=["Associated Gene"])
    if result.shape[0] == 0:
        # If the rows consist only of NaNs then we need to keep it
        return df
    # Otherwise drop the NaNs
    return result


def remove_na_gene(data):
    # Some gene rows have NaN in the values and need to be dropped
    # These can't be dropped outright because there might not be a gene
    # listed for a particular Probe Set ID
    data = (
        data.groupby("Probe Set ID", as_index=False, sort=False)
        .apply(_check_row_for_na)
        .reset_index(drop=True)
    )
    return data


def write_output(data, out_file):
    date = datetime.today()
    lines_to_write = [
        "Pharmacoscan query file",
        f"Original annot file used: {file_path_in}",
        "Author: Andrew Haddad",
        f"Date Created: {date.strftime('%B')} {date.day}, {date.year}",
        f"Library version number: {version}",
    ]
    with open(out_file, "w") as f:
        for line in lines_to_write:
            f.write(f"#{line}\n")
    data.to_csv(out_file, index=False, mode="a")


def rename_cols(data):
    new_names = [
        "Probe Set ID",
        "Chromosome",
        "Position",
        "Ref",
        "Alt",
        "Gene",
        "Probe Count",
        "rsID",
    ]
    data.columns = new_names
    return data


if __name__ == "__main__":
    cols = [
        "Probe Set ID",
        "Chromosome",
        "Physical Position",
        "Ref Allele",
        "Alt Allele",
        "Associated Gene",
        "Probe Count",
        "Extended RSID",
    ]
    file_path_in = "PharmacoScan_96F.na36.r9.a4.annot.csv"
    version = "r9"
    data = pd.read_csv(file_path_in, comment="#", usecols=cols)
    data = split_gene_col(data)
    gene_data, no_gene_data = split_up_data(data)
    # No gene associated with these rows
    no_gene_data.loc[:, "Associated Gene"] = np.nan
    gene_data = explode_and_filter(gene_data)
    data = pd.concat([gene_data, no_gene_data], ignore_index=True, axis=0)
    data = split_rsids_col(data)

    data = remove_blank_data(data)
    data = remove_na_gene(data)
    data = rename_cols(data)
    write_output(data, f"pscan_table_{version}.csv")
