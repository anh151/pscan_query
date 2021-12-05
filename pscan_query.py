import argparse
import os
import utils


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


def main():
    args = get_args()
    utils.check_input_file(args.file)
    pscan_data = utils.read_table(args.file)
    utils.check_overall_input(args)
    search_data = utils.SearchData(pscan_data)
    if args.gene:
        search_data.gene = args.gene.strip().upper()
        search_data.check_gene_input()
        search_data.filter_by_gene()
        search_data.get_probe_count()
        search_data.send_cpic_request()
        search_data.merge_data()
    if args.rsid:
        search_data.rsid = args.rsid.lower().strip()
        search_data.check_rsid_input()
        search_data.filter_by_rsid()
    if args.position:
        search_data.position = args.position.strip()
        search_data.check_position_input()
        search_data.filter_by_position_input()
    utils.check_output_path(args.output)
    search_data.data.to_csv(args.output, index=False)


if __name__ == "__main__":
    try:
        main()
    except:
        print("An unknown error as occurred.")
