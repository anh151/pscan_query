import csv
import os
import re
import sys

import numpy as np
import pandas as pd


def parse_gene_text(text_entered):
    text_entered = text_entered.split("\n")
    genes = []
    for gene1 in text_entered:
        for gene2 in gene1.strip().split(","):
            gene = gene2.strip().upper()
            if len(gene) != 0:
                genes.append(gene)
    if len(genes) == 0:
        return None
    return genes


def parse_rsid_text(text_entered):
    rsids = re.findall(r"rs\d+", text_entered, flags=re.IGNORECASE)
    if len(rsids) == 0:
        return None
    return [rsid.lower() for rsid in rsids]


def _parse_gene_file(file_path):
    file_contents = None
    error = None
    genes = []
    try:
        with open(file_path, "r") as f:
            csv_reader = csv.reader(f)
            for line in csv_reader:
                for gene in line:
                    genes.append(gene.strip().upper())
    except Exception:
        ex_type, *_ = sys.exc_info()
        error = ex_type
        return file_contents, error
    if len(genes) != 0:
        file_contents = genes
    return file_contents, error


def _parse_rsid_file(file_path):
    file_contents = None
    error = None
    try:
        with open(file_path, "r") as f:
            lines = f.readlines()
    except Exception:
        ex_type, *_ = sys.exc_info()
        error = ex_type
        return file_contents, error
    rsids = parse_rsid_text(str(lines))
    if len(rsids) != 0:
        file_contents = rsids
    return file_contents, error


def read_file(file_path, data_type=None):
    file_contents = None
    error = None
    if file_path is None:
        return file_contents, error
    if not os.path.isfile(file_path):
        error = FileNotFoundError
        return file_contents, error
    if data_type == "gene":
        file_contents, error = _parse_gene_file(file_path)
    elif data_type == "rsid":
        file_contents, error = _parse_rsid_file(file_path)
    return file_contents, error


def _filter_by_rsids(df, rsids):
    filtered_table = (
        df.loc[df["rsID"].isin(rsids)]
        .merge(
            pd.Series(rsids, name="rsID"),
            how="outer",
            on="rsID",
            indicator=True,
        )
        .query("`_merge`.isin(['both', 'right_only'])")
    )
    filtered_table["On Array"] = np.where(
        filtered_table["_merge"] == "both", "Yes", "No"
    )
    filtered_table = filtered_table.loc[
        :, ["Gene", "rsID", "On Array"]
    ].drop_duplicates()
    return filtered_table


def _filter_by_genes(df, genes):
    cols = ["Gene", "rsID", "Position", "Ref", "Alt", "Probe Count"]
    df = (
        df.loc[df["Gene"].isin(genes), cols]
        .drop_duplicates()
        .sort_values(["Gene", "Position"])
    )
    return df


def _find_data_type(query_data):
    if re.search(r"rs\d+", query_data[0], flags=re.IGNORECASE):
        return "rsid"
    else:
        return "gene"


def create_pretty_filename(file_path, save=False):
    file_name = os.path.basename(file_path)
    if len(file_name) < 10:
        file_print = file_name
    else:
        file_print = f"{file_name[:8]}..."
    if save:
        text = f"Exported to: {file_print}"
    else:
        text = f"File Opened: {file_print}"
    return text


def _resource_path(file_name):
    try:
        bundle_dir = os.path.abspath(os.path.dirname(__file__))
        path_to_data = os.path.join(bundle_dir, file_name)
    except NameError:
        path_to_data = os.path.join(os.getcwd(), file_name)
    return path_to_data


def query_table(query_data):
    # Need to parse one of the columns to int that can handle NaNs
    file_name = "pscan_table_r9.csv"
    table_path = _resource_path(file_name)
    pharmacoscan_table = pd.read_csv(table_path, comment="#").astype(
        {"Position": "Int64"}
    )

    data_type = _find_data_type(query_data)
    if data_type == "gene":
        pharmacoscan_table = _filter_by_genes(pharmacoscan_table, query_data)
    if data_type == "rsid":
        pharmacoscan_table = _filter_by_rsids(pharmacoscan_table, query_data)
    return pharmacoscan_table


def export_data(df, file_path):
    ext = os.path.splitext(file_path)[-1]
    try:
        if ext == ".txt" or ext == ".tsv":
            df.to_csv(file_path, sep="\t", index=False)
        elif ext == ".csv":
            df.to_csv(file_path, index=False)
        elif ext == ".xlsx":
            df.to_excel(file_path, index=False)
        elif ext == ".xls":
            # xls files are deprecated so will be changed to xlsx
            file_path = file_path + "x"
            df.to_excel(file_path, index=False)
        else:
            # any other extension will be treated as .tsv files
            # may need to fix in future if needed
            df.to_csv(file_path, sep="\t", index=False)
    except Exception:
        ex_type, *_ = sys.exc_info()
        error = ex_type
        return error
