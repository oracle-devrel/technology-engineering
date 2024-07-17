# MongoDB compatibility advisor for Autonomous MongoDB API

This tool helps you to identify which MongoDB queries are supported when using the Oracle Autonomous MongoDB API. 

Reviewed: 20.03.2024

# When to use this asset?

This tool generates a report which indicates the percentage of compatibility. There is an example in this repository. This advisor has been tested for the 19c version.

# How to use this asset?

You need to provide the MongoDB log as an argument.

```
python3 advisor.py --file mongod.log
```

You need to enable logging in the MongoDB by running the following command. It is recommended to run it in non-production environments.
```
db.setProfilingLevel(0, -1)
```

The script generates a report in a file called report_advisor.txt

# License
 
Copyright (c) 2024 Oracle and/or its affiliates.
 
Licensed under the Universal Permissive License (UPL), Version 1.0.
 
See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
