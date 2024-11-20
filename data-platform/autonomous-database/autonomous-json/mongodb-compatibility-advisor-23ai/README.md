# MongoDB compatibility advisor for Autonomous MongoDB API

This tool helps you to identify which MongoDB queries are supported when using the Oracle Autonomous MongoDB API. 
**IMPORANT NOTE:** This tool is not an official product and is provided as a community-driven resource to assist in expediting the process of checking compatibility. While it aims to be helpful, it is not guaranteed to cover all scenarios or provide complete accuracy. Users are strongly encouraged to consult the official documentation for definitive guidance and support. 
Reviewed: 04.11.2024

# When to use this asset?

This tool generates a report which indicates the percentage of compatibility. There is an example in this repository. This advisor has been tested for the 23ai version.

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
