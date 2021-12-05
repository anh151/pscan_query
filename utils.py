import sys
import warnings
import os
import re


def install_dependencies():
    user_response = input(
        "Required libraries are not installed. Allow global installation? (y/n):"
    )
    if user_response.lower().strip() != "y":
        sys.exit("ERROR: Exiting due to missing libraries.")
    import subprocess

    command = subprocess.run(
        ["pip", "install", "-r", "requirements.txt"],
        capture_output=True,
        text=True,
    )
    if command.returncode != 0:
        sys.exit(
            f"ERROR: Attempt to install dependencies resulted in error:{command.stderr}.\nTry installing manually."
        )


try:
    import pandas as pd
    import requests
except ModuleNotFoundError:
    install_dependencies()
    import pandas as pd
    import requests

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")


class SearchData:
    def __init__(self, data=None):
        self.data = data
        self.gene = None
        self.position = None
        self.rsid = None
        self.gene_cpic_data = None

    def filter_by_gene(self):
        self.data = self.data.loc[self.data["gene"] == self.gene].copy()

    def filter_by_rsid(self):
        self.data = self.data.loc[self.data["rsid"] == self.rsid]

    def filter_by_position_input(self):
        self.data = self.data.loc[self.data["pos"] == self.position]

    def get_probe_count(self):
        self.data["probe_count"] = self.data.groupby("pos")["pos"].transform("count")
        self.data = self.data.drop(columns="probeset_id").drop_duplicates(
            ignore_index=True
        )

    def send_cpic_request(self):
        response = requests.get(
            f"https://api.pharmgkb.org/v1/download/file/attachment/{self.gene}_allele_definition_table.xlsx"
        )
        if response.ok:
            self.gene_cpic_data = SearchData._parse_cpic_response(response)

    @staticmethod
    def _parse_cpic_response(response):
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

    def merge_data(self):
        self.data = self.data.merge(self.gene_cpic_data, on="rsid", how="left")

    def check_gene_input(self):
        possible_genes = self.data["gene"].unique()
        if self.gene not in possible_genes:
            sys.exit("ERROR: Gene provided does not exist in the file.")

    def check_rsid_input(self):
        if re.match(r"^rs\d+$", self.rsid, flags=re.IGNORECASE) is None:
            sys.exit(
                "ERROR: Incorrect format provided for rsID. Must be in format of rs1234."
            )
        possible_rsids = self.data["rsid"].unique()
        if self.rsid not in possible_rsids:
            sys.exit("ERROR: The rsID provided does not have a corresponding probe.")

    def check_position_input(self):
        try:
            self.position = int(self.position)
        except ValueError:
            sys.exit(
                "ERROR: Incorrect format provided for position. Must be in format 123456789."
            )
        possible_positions = self.data["pos"].unique()
        if self.position not in possible_positions:
            sys.exit(
                "ERROR: The position provided does not have a corresponding_probe."
            )


def read_table(file_path):
    pscan_data = (
        pd.read_csv(
            file_path,
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


def check_input_file(file):
    if file is None:
        sys.exit("ERROR: Pharmacoscan input file is required.")
    if not os.path.isfile(file):
        sys.exit(
            "ERROR: Unable to find pharmacoscan input file.\nPath is either invalid or file does not exist."
        )


def check_output_path(output_path):
    dir_path = os.path.dirname(output_path)
    if len(dir_path) == 0:
        return
    if not os.path.isdir(dir_path):
        sys.exit("ERROR: Output file path is not valid.")


def check_overall_input(args):
    if not args.gene and not args.position and not args.rsid:
        sys.exit("ERROR: Must supply one of gene, position, or rsid.")
