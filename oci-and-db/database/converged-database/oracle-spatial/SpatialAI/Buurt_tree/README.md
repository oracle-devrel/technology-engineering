# Oracle Spatial and AI Agents Getting Started - Den Haag Trees and Neighbourhoods
Use this asset as a reference for exploring Den Haag tree and green-neighbourhood data with Oracle Spatial, Select AI Agents, and Oracle Machine Learning (OML) in Oracle AI Database. The notebooks define SQL functions, procedures, tools, tasks, agents, and teams for natural-language analysis. Reviewed: 2026.11.16

## When to use this asset?

Use this asset to demonstrate how agents combine tree points and neighbourhood polygons, answer SQL and spatial questions, calculate neighbourhood tree density, group trees with OML K-means, flag unusual tree records with OML one-class SVM, and retrieve saved conversations. The analysis results can be returned as GeoJSON for the Ask Oracle map.

The two source tables are `BOMEN` (trees) and `GEZONDZH_GROEN_BUURT` (neighbourhoods). The translation notebook creates the English-named tables `BOMEN_TREES` and `GEZOND_GREEN_NEIGHBOURHOOD`. Source geometries use Amersfoort / RD New (EPSG:28992); map GeoJSON uses WGS 84 (EPSG:4326).

For more information check PDF file

## How to use this asset?

This is a demo workflow. Adapt the schema names, credentials, AI model access, and data to your environment. Run notebook cells one at a time and in the order below, checking the result of each cell before continuing.:

1. Load and inspect the source data. Import bomen_shape.zip and GEZONDZH_GROEN_BUURT.zip through Spatial Studio as BOMEN and GEZONDZH_GROEN_BUURT. Use 0_0_bomen_loadandcheck.sqlnb to inspect the tables and check their spatial metadata and indexes.

2. Configure Select AI. Set up the base profile in 0_2_bomen_NL2SQL.sqlnb. Replace <your user/schema> with your schema name wherever it appears.
3. Translate the columns. Run 0_1_bomen_OML_Trans.sqlnb to create the English-named tables BOMEN_TREES and GEZOND_GREEN_NEIGHBOURHOOD.
4. Set up tree density. Run the implementation cells in 1-bomen_OML_final_density.sqlnb to create the storage procedure, density function, tool, task, agent, and initial team. On the first density tool call, the storage procedure creates the required result table and nonspatial views. The source and result tables retain geometry for spatial queries and maps; the _V views provide attributes for OML.
5.Add the other analysis workers. Run 2-bomen_OML_discovery_1.sqlnb, 3-bomen_OML_one_class_SVM.sqlnb, and 2-bomen_OML_final_Kmeans_2.sqlnb to add data discovery, unusual-tree review, and tree grouping.
6. Add greeting and SQL questions. Run 4-bomen_OML_greeting_NL2SQL.sqlnb to add these workers to the supervised team. Optionally, run 5-Boment_OML_History.sqlnb to create the separate history team and vector search over saved questions and answers.
Use the separate *tests*.sqlnb and *checkSQL.sqlnb notebooks to verify the data, tools, saved results, and agent routing. The AskOracle APEX application and its static JavaScript files are provided separately in the app folder.
