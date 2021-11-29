# pscan_query

Pharmacoscan query tool allows for fast querying of pharmacoscan annot library files. 

## Installation
Requirements:
- Python >= 3.6

Dependencies:
- pandas
- requests
- openpyxl

If dependencies are not already preinstalled, pscan_query will attempt to install these on the first run with user permission.

Installation can be done by either cloning the repository as shown below or by downloading the files into a directory
```sh
git clone https://github.com/anh151/pscan_query 
cd pscan_query  
```

## Running

```
Arguments:
  -f, --file       Path to pharmacoscan file input
  -g, --gene       Gene to search for in the file.
  -r, --rsid       rsID to search for in the file. Format accepted is rs1234
  -p, --position   Position in chromosome to search for. Format accepted is "123456789".
  -o, --output     Path to output file as a .csv.
```

Pharmacoscan input file is supplied with the tool. If a different file needs to be used, this can be passed in via the -f option.

One of -g, -r, or -p must be supplied.
 
Default output file will be the current working directory with file name output.csv.

Examples:

```sh
python3 pscan_query.py -g CYP2C19 -o /path/to/directory/cyp2c19_output.csv
```
```sh
python3 pscan_query.py -g CYP2C19 -p 123456789 -o /path/to/directory/cyp2c19_output.csv
```
```sh
python3 pscan_query.py -g CYP2C19 -p rs12345 -o /path/to/directory/cyp2c19_output.csv
```