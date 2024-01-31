#  Network Path Analyser

Network Path Analyzer (NPA) provides a unified and intuitive capability you can use to identify virtual network configuration issues that impact connectivity. NPA collects and analyzes the network configuration to determine how the paths between the source and the destination function or fail. No actual traffic is sent, instead, the configuration is examined and used to confirm reachability.

NPA carefully examines routing and security configurations and identifies the potential network path your defined traffic traverses, along with information about virtual networking entities in the path. In addition to the path information, the output of these checks includes how routing rules and network access lists (security lists, NSGs, and so on) allow or deny traffic. The sources and destinations could be within OCI, across OCI and on-premises, or OCI and the internet. NPA analyzes all the standard OCI networking elements with their associated configuration.

Using NPA, you can:

    Troubleshoot routing and security misconfiguration that are causing connectivity issues
    Validate that the logical network paths match your intent
    Verify that the virtual network connectivity setup works as expected before starting to send traffic

To achieve any of these objectives, create a test that you think should work and then run the test. You can also save this test definition to run it again later. Saved tests are displayed in the Network Path Analyzer page for you to select.

The following source and destination scenarios are supported:

    OCI to OCI
    OCI to on-premises
    On-premises to OCI
    Internet to OCI
    OCI to internet

 
## Useful Links

- [Introducing NPA](https://blogs.oracle.com/cloud-infrastructure/post/introducing-oracle-cloud-network-path-analyzer)


### Reference Architectures & Step-by-step Guides

 - [NPA Steps guide](https://blogs.oracle.com/ateam/post/oci-network-path-analyzer)
 - [NPA Step by Step guide (external)](https://k21academy.com/1z0-1072/oracle-cloud-network-path-analyzer/)  

### Blogs
 
- [Speed up Network Troubleshooting with Oracle Cloud Network Path Analyzer](https://blogs.oracle.com/analytics/post/fast-track-network-troubleshooting-with-oracle-cloud-network-path-analyzer-for-oracle-analytics-cloud-oac)


### Videos & Podcasts

- [NPA in 5 mins](https://www.youtube.com/watch?v=vr8oitlkAvI)
- [Oracle Network Path Analyzer](https://videohub.oracle.com/media/Oracle+Network+Path+Analyzer.mov/1_dm81kp7i)
- [OCI Tips and Tricks - Troubleshooting with Oracle Cloud Infrastructure Network Path Analyzer](https://www.youtube.com/watch?v=AoTk4Aq-9Gw)


# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
