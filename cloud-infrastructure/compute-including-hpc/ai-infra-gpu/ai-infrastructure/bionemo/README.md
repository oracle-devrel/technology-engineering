# Using NVIDIA BioNeMo on Oracle Cloud Infrastructure (OCI)

This repository showcases how to deploy NVIDIA NIM's from the BioNeMo suite on OCI at scale in order to tackle a practical problem of drug discovery. 

Reviewed: 16.10.2025

# Table of Contents

1. [Use case overview](#use-case-overview)
2. [Objective](#objective)
3. [Protein Structure Prediction for DHFR Inhibitor Discovery](#protein-structure-prediction-for-dhfr-inhibitor-discovery)

*More steps to follow soon*

# Use case overview

Dihydrofolate reductase (DHFR) is a crucial enzyme in cellular metabolism, playing a vital role in DNA synthesis and cell proliferation. DHFR catalyzes the NADPH-dependent reduction of dihydrofolate to tetrahydrofolate (THF), an essential cofactor for several one-carbon transfer reactions in purine and pyrimidine synthesis. This reaction is critical for maintaining the intracellular pool of THF, which is necessary for the de novo synthesis of purines, thymidylate, and certain amino acids.

The importance of DHFR in DNA synthesis stems from its role in producing THF, which is required for the synthesis of nucleic acid precursors. Without sufficient THF, cells cannot efficiently produce the building blocks needed for DNA replication and cell division. This makes DHFR essential for rapidly dividing cells, such as cancer cells and bacteria.

DHFR has become a common target for antimicrobial and anticancer drugs due to its critical role in cell proliferation. By inhibiting DHFR, these drugs deplete the THF pool within cells, leading to disruption of DNA synthesis, slowed cell proliferation, and eventually cell death. This mechanism of action is particularly effective against rapidly dividing cells, making DHFR inhibitors valuable in treating cancer and bacterial infections.

Antifolate medications, which target DHFR, have been widely used in cancer treatment. For example, methotrexate is a well-known DHFR inhibitor used in cancer therapy and for treating rheumatoid arthritis. In antimicrobial applications, trimethoprim is a classic DHFR inhibitor used to combat bacterial infections.

The effectiveness of DHFR as a drug target has led to ongoing research into developing new inhibitors with improved efficacy and the ability to overcome resistance mechanisms. This includes efforts to design compounds that can inhibit both wild-type and mutant forms of DHFR, potentially leading to antibiotics less prone to resistance development.

# Objective

To develop a novel inhibitor for dihydrofolate reductase (DHFR), we are using NVIDIA BioNeMo and other open-source tools.

# [Protein Structure Prediction for DHFR Inhibitor Discovery](./alphafold2-oke/README.md)

This step makes use of the Alphafold2 NIM. The detailed explanation is availbale [here](./alphafold2-oke/README.md)

# Useful links

- [Build a Generative Protein Binder Design Pipeline](https://build.nvidia.com/nvidia/protein-binder-design-for-drug-discovery)
- [Protein structure prediction with Alphafold2 NIM](https://github.com/NVIDIA/bionemo-examples/blob/62aef816070399814e478234dc47eb2ccddfd1a0/examples/nims/alphafold2/AlphaFold2-NIM-example.ipynb)
- [Overview of Kubernetes Engine in OCI](https://docs.oracle.com/en-us/iaas/Content/ContEng/Concepts/contengoverview.htm) 

# Acknowledgments

- **Authors** - Bruno Garbaccio (GPU Specialist), Wajahat Aziz (GPU Specialist leader)

# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
