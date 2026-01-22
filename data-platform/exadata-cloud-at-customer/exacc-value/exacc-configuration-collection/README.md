# Exadata Cloud@Customer Configuration Collection Scripts

A script utilising the OCI Python SDK to collect the information on an existing ExaDB-C@C or ExaDB-D configuration. 

# When to use this asset?
 
The asset is designed to collect configuration options and settings of resources on an ExaDB-C@C and/or ExaDB-D environment. This configuration options include Exadata Infrastructure and VM cluster related settings mainly. 
 
# How to use this asset?
 
To be able to run the scripts you have to have a working Python 3.7 or higher environment installed with the Oracle Cloud Infrastructure Python SDK installed. 

To run the script you have to setup up the following:

- working API Keys for your OCI account
- a minimum READ policy set for the resources, we need collecting information on
- configuration file under the following path by default: $HOME/.oci/config
- the above configuration file is the same as the one used by OCI CLI

Run the script with the following command:

``` 
python exccbb_iude.py 
```
The script has a help functionality included as the following:

```
exccbb_iude.py -h
usage: exccbb_iude.py [-h] [--oconfigf OCONFIGF] [--oproname OPRONAME] [--custname CUSTNAME] [--restype {CS,CC,ALL}]

options:
  -h, --help            show this help message and exit
  --oconfigf, -of OCONFIGF
                        OCI Configuration File Path
  --oproname, -on OPRONAME
                        OCI Profile Name [profile_name, DEFAULT]
  --custname, -cn CUSTNAME
                        Customer Name
  --restype, -rt {CS,CC,ALL}
                        Exadata Cloud Service Type [CS, CC, ALL]
```
The above script is creating JSON file with all the configuration information which can be shared with Oracle for further analysis. 

Reviewed:

# License
 
Copyright (c) 2026 Oracle and/or its affiliates.
 
Licensed under the Universal Permissive License (UPL), Version 1.0.
 
See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
