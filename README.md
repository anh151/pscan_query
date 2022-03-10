# Pharmascoan Query

Pharmacoscan query tool allows for fast querying of pharmacoscan annot library files. Current library version is r9. 

Pharmacoscan library files can be found at the bottom of the pharmsocan page on the Thermo Fisher website provided below:

[Pharmacoscan](https://www.thermofisher.com/order/catalog/product/903026)

## Installation (Only needed if you intend to run using the source code)
Requirements:
- Python >= 3.6

Dependencies:
- pandas==1.3.2
- requests==2.22.0
- openpyxl==3.0.7


Installation can be done by either cloning the repository as shown below or by downloading the files into a directory
```sh
git clone https://github.com/anh151/pscan_query 
cd pscan_query  
```

## Launching the GUI

This query tool can be run using two different methods. The first method is using the single file executable. The second option is running from source code.

### Method 1 from exe:
Note: Currently this is only supported on Windows. Windows 11 has not been tested but may work. 

The GUI can be launched by running the single file excutable provided here:

[Download](https://pitt-my.sharepoint.com/:u:/g/personal/anh151_pitt_edu/EY-Hu7ZF0GxMlNXyeRRbeGEBW2N0N5-IxDn4bEG36-8HYw?download=1)

### Method 2 from source code:

The GUI can be launched by running the app.py file. 

Note: You must have the dependencies installed and also download the pscan_table_r9.csv file if you are using this method.

[Table](https://pitt-my.sharepoint.com/:x:/g/personal/anh151_pitt_edu/EZuJUU5vYHBCswn3UNj_bhAB76MB1uM3YgtkUf-CMLot9A?download=1)

## Running Queries
Current queries options include by rsID or by gene. Future updates will add an option to query by allele for common PGx genes. Running a query can be achieved by entering rsIDs/genes in the text box or selecting a file that has one gene/rsid on each line or separated by commas on the same line. I.e

```sh
CYP2C19
CYP2D6
```

or

```sh
CYP2C19,CYP2D6
```

File input options:

- Input file must be a plain text file such as csv/tsv/txt. Excel or other binary files types are not supported.

File export options:
- csv
- tsv
- xlsx (xls is no longer supported and will be exported as xlsx)
- All other extensions will be defaulted to a tab delimited file

## Bugs and desired features
Please report any bugs and/or desired features to either the github issues page or to andrew.haddad@pitt.edu