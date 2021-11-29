import argparse
import os
import re
import sys
import warnings


def install_dependencies():
    user_response = input(
        "Required libraries are not installed. Allow global installation? (y/n)"
    )
    if user_response.lower().strip() != "y":
        sys.exit("ERROR: Exiting due to missing libraries.")
    import subprocess

    command = subprocess.run(
        ["pip", "install", "pandas", "requests", "openpyxl", "--quiet"],
        capture_output=True,
        text=True,
    )
    if command.returncode != 0:
        sys.exit(
            f"ERROR: Attempt to install dependencies manually resulted in error:{command.stderr}.\nTry installing manully."
        )


try:
    import pandas as pd
    import requests
except ModuleNotFoundError:
    install_dependencies()

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-f",
        "--file",
        help="Path to pharmacoscan file input",
        type=str,
        metavar="",
        default="PharmacoScan_96F.r8_UPMC_2.na36.dc_annot.csv",
    )
    parser.add_argument(
        "-g",
        "--gene",
        type=str,
        help="Gene to search for in the file.",
        metavar="",
    )
    parser.add_argument(
        "-r",
        "--rsid",
        type=str,
        help="rsID to search for in the file. Format accepted is rs1234",
        metavar="",
    )
    parser.add_argument(
        "-p",
        "--position",
        type=str,
        help='Position in chromosome to search for. Format accepted is "123456789".',
        metavar="",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Path to output file as a .csv.",
        metavar="",
        default=os.path.join(os.getcwd(), "output.csv"),
    )
    return parser.parse_args()


def check_input_file(file):
    if file is None:
        sys.exit("ERROR: Pharmacoscan input file is required.")
    if not os.path.isfile(file):
        sys.exit(
            "ERROR: Unable to find pharmacoscan input file.\nPath is either invalid or file does not exist."
        )


def check_gene_input(pscan_data, gene):
    possible_genes = pscan_data["gene"].unique()
    if gene.upper() not in possible_genes:
        sys.exit("ERROR: Gene provided does not exist in the file.")


def filter_by_gene(pscan_data, gene):
    return pscan_data.loc[pscan_data["gene"] == gene.upper()]


def read_table(file_path):
    pscan_data = (
        pd.read_csv(
            "PharmacoScan_96F.r8_UPMC_2.na36.dc_annot.csv",
            comment="#",
            usecols=[
                "Probe Set ID",
                "Associated Gene",
                "dbSNP RS ID",
                "Chromosome",
                "Physical Position",
            ],
        )
        .rename(
            columns={
                "Probe Set ID": "probeset_id",
                "Associated Gene": "gene",
                "dbSNP RS ID": "rsid",
                "Chromosome": "chrom",
                "Physical Position": "pos",
            }
        )
        .astype({"pos": "Int64"})
    )
    return pscan_data


def check_rsid_input(pscan_data, rsid):
    if re.match(r"^rs\d+$", rsid, flags=re.IGNORECASE) is None:
        sys.exit(
            "ERROR: Incorrect format provided for rsID. Must be in format of rs1234."
        )
    possible_rsids = pscan_data["rsid"].unique()
    if rsid.lower() not in possible_rsids:
        sys.exit("ERROR: The rsID provided does not have a corresponding probe.")


def filter_by_rsid(pscan_data, rsid):
    return pscan_data.loc[pscan_data["rsid"] == rsid.lower()]


def check_position_input(pscan_data, position):
    try:
        position = int(position)
    except ValueError:
        sys.exit(
            "ERROR: Incorrect format provided for position. Must be in format 123456789."
        )
    possible_positions = pscan_data["pos"].unique()
    if position not in possible_positions:
        sys.exit("ERROR: The position provided does not have a corresponding_probe.")


def filter_by_position_input(pscan_data, position):
    return pscan_data.loc[pscan_data["pos"] == int(position)]


def get_probe_count(pscan_data):
    pscan_data["probe_count"] = pscan_data.groupby("pos")["pos"].transform("count")
    pscan_data = pscan_data.drop(columns="probeset_id").drop_duplicates(
        ignore_index=True
    )
    return pscan_data


def send_cpic_request(gene):
    response = requests.get(
        f"https://api.pharmgkb.org/v1/download/file/attachment/{gene}_allele_definition_table.xlsx"
    )
    if response.ok:
        gene_cpic_data = parse_cpic_response(response)
        return gene_cpic_data
    else:
        print(f"INFO: Unable to access CPIC allele info for gene: {gene}.")


def parse_cpic_response(response):
    cpic_data = pd.read_excel(response.content, header=5, engine="openpyxl")
    cpic_data = cpic_data.transpose().drop(columns=0)
    new_header = cpic_data.iloc[0]
    cpic_data = cpic_data[1:]
    cpic_data.columns = new_header
    for col in cpic_data.columns:
        cpic_data.loc[~cpic_data[col].isna(), col] = col
    cpic_data = cpic_data.reset_index().rename(columns={"index": "rsid"})
    cpic_data.columns.name = None
    cpic_data = cpic_data.loc[
        ~cpic_data["rsid"].str.contains("Unnamed", case=False, regex=False)
    ]
    gene_cpic_data = (
        pd.melt(
            cpic_data,
            id_vars="rsid",
            value_vars=cpic_data.columns[1:],
            value_name="allele",
        )
        .drop(columns="variable")
        .dropna(axis=0)
        .reset_index(drop=True)
        .groupby("rsid")
        .agg({"allele": lambda x: ", ".join(x)})
        .reset_index()
    )
    return gene_cpic_data


def check_output_path(output_path):
    dir_path = os.path.dirname(output_path)
    if len(dir_path) == 0:
        return
    if not os.path.isdir(dir_path):
        sys.exit("ERROR: Output file path is not valid.")


def check_overall_input(args):
    if not args.gene and not args.pos and not args.rsid:
        sys.exit("ERROR: Must supply one of gene, position, or rsid.")


def main():
    args = get_args()
    check_input_file(args.file)
    pscan_data = read_table(args.file)
    check_overall_input()
    if args.gene:
        check_gene_input(pscan_data, args.gene)
        pscan_data = filter_by_gene(pscan_data, args.gene)
        pscan_data = get_probe_count(pscan_data)
        gene_cpic_data = send_cpic_request(args.gene)
        pscan_data = pscan_data.merge(gene_cpic_data, on="rsid", how="left")
    if args.rsid:
        check_rsid_input(pscan_data, args.rsid)
        pscan_data = filter_by_rsid(pscan_data, args.rsid)
    if args.position:
        check_position_input(pscan_data, args.position)
        pscan_data = filter_by_position_input(pscan_data, args.position)
    check_output_path(args.output)
    pscan_data.to_csv(args.output, index=False)


if __name__ == "__main__":
    try:
        main()
    except:
        print("An unknown error as occurred.")
