# Oracle Graph Getting Started - Bank Graph

Use this asset as a reference for getting started with Property Graph capabilities available within the Oracle AI Database.
Reviewed: 2026.09.01

## When to use this asset?

Use this asset as a reference for combining Oracle Property Graph analytics and Oracle Machine Learning (OML) in a unified banking workflow. 

This asset is designed for scenarios where you want to:
- Build and analyze base property graphs from financial transfer data.
- Generate and validate synthetic transaction data using CTGAN to enrich demonstration environments without using sensitive or production records.
- Compute advanced graph metrics and algorithms (such as cycle metrics, SQL PageRank, PGX betweenness, and PGX closeness).
- Segment and cluster accounts using OML K-Means based on their graph-metric values and behavioral patterns.
- Push cluster results and enriched features back into the graph to empower deeper investigation and visualization using both topological relationships and behavioral similarity.

## How to use this asset?

This asset is provided as general-purpose material. Please tailor the content according to your context and needs.

The pipeline for this asset is executed through the following sequential steps:

1. **Create and analyze the base graph**: Open `1-bankgraph/demo_BANK_GRAPH_26ai_alg.dsnb` to create the banking property graph and run initial graph queries and algorithms.
2. **Augment transaction data**: Review `2_Python/config.json` and run `2_Python/ctgan_augment_bank_transfers.py` to generate synthetic transfers for demonstration and enrichment purposes only.
3. **Validate and create the augmented graph**: Open `1-bankgraph/demo_Check_synthetic.dsnb` to validate synthetic transfers and account references, create `BANK_TRANSFERS_AUGMENTED` and `BANK_GRAPH_AUGMENTED`, and calculate/normalize cycle metrics, SQL PageRank, PGX betweenness, and PGX closeness into `BANK_GRAPH_FEATURES_NORMALIZED`.
4. **Segment accounts with OML K-Means**: Open `3-OML/Graph_algorithms_git.dsnb` to train cycle-behavior and importance models, then save the resulting cluster assignments in `BANK_GRAPH_CLUSTER_RESULTS`.
5. **Create the enriched clustered graph**: Return to `1-bankgraph/demo_Check_synthetic.dsnb` to create `BANK_ACCOUNTS_CLUSTERED_V` and `BANK_GRAPH_AUGMENTED_CLUSTER`, combining all metrics and cluster IDs.

*Note: CTGAN-generated transactions are strictly synthetic and must not be treated as real customer activity or actual evidence of fraud.*

# License
 
Copyright (c) 2026 Oracle and/or its affiliates.
 
Licensed under the Universal Permissive License (UPL), Version 1.0.
 
See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
