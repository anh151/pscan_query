import sys
import warnings


def install_dependencies(libraries):
    user_response = input(
        "Required libraries are not installed. Allow global installation? (y/n)"
    )
    if user_response.lower().strip() != "y":
        sys.exit("ERROR: Exiting due to missing libraries.")
    import subprocess

    command = subprocess.run(
        ["pip", "install"] + libraries + ["--quiet"],
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
    install_dependencies(["pandas", "requests", "openpyxl", "dash"])
    import pandas as pd
    import requests

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")


class SearchData:
    def __init__(self):
        self.data = None
        self.gene = None
        self.position = None
        self.rsid = None
        self.gene_cpic_data = None

    def filter_by_gene(self):
        self.data = self.data.loc[self.data["gene"] == self.gene]

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
