# Oracle Spatial and AI Agents Getting Started - Den Haag Trees and Neighbourhoods
Use this asset as a reference for exploring Den Haag tree and green-neighbourhood data with Oracle Spatial, Select AI Agents, and Oracle Machine Learning (OML) in Oracle AI Database. The notebooks define SQL functions, procedures, tools, tasks, agents, and teams for natural-language analysis. Reviewed: 2026.11.04

## When to use this asset?

Use this asset to demonstrate how agents combine tree points and neighbourhood polygons, answer SQL and spatial questions, calculate neighbourhood tree density, group trees with OML K-means, flag unusual tree records with OML one-class SVM, and retrieve saved conversations. The analysis results can be returned as GeoJSON for the Ask Oracle map.

The two source tables are `BOMEN` (trees) and `GEZONDZH_GROEN_BUURT` (neighbourhoods). The translation notebook creates the English-named tables `BOMEN_TREES` and `GEZOND_GREEN_NEIGHBOURHOOD`. Source geometries use Amersfoort / RD New (EPSG:28992); map GeoJSON uses WGS 84 (EPSG:4326).

For more information check PDF file

## How to use this asset?

This asset is general-purpose demo material. Adapt the schema names, credentials, model access, and data to your environment. First import the `bomen-shape_denhaag` (trees) and `GEZONDZH_GROEN_BUURT` (neighbourhoods) ZIP files into Oracle Spatial as `BOMEN` and `GEZONDZH_GROEN_BUURT`. Configure the base Select AI profile in `0_2_bomen_NL2SQL.sqlnb`; the translation procedure uses it. Use `0_0_bomen_loadandcheck.sqlnb` to inspect the loaded data, and review its spatial metadata and index changes before running those cells. Replace `<your user/schema>` with your schema name wherever it occurs. Then run the implementation cells **in order and one at a time**:

1. **Translate the columns and prepare nonspatial views.** Run `0_1_bomen_OML_Trans.sqlnb` to create the English-named tables `BOMEN_TREES` and `GEZOND_GREEN_NEIGHBOURHOOD`. Compile `prepare_tree_density_storage` in `1-bomen_OML_final_density.sqlnb`. The first density tool call executes this procedure and creates `BOMEN_TREES_V` and `GEZOND_GREEN_NEIGHBOURHOOD_V` automatically. These `_V` views exclude `SDO_GEOMETRY` because OML cannot use that column as a model input; the source tables keep their geometry for spatial queries and maps.
2. Run the remaining cells in `1-bomen_OML_final_density.sqlnb` to define the density function, tool, task, agent, and initial team. On its first call, the function creates the missing storage and views, then saves measured neighbourhood results in `TREE_DENSITY_RESULTS`, including polygon geometry. It also creates the nonspatial `TREE_DENSITY_RESULTS_V` view.
3. Add `2-bomen_OML_discovery_1.sqlnb`, `3-bomen_OML_one_class_SVM.sqlnb`, and `2-bomen_OML_final_Kmeans_2.sqlnb` for data discovery, unusual-tree flags, and tree groups. The OML setup routines create `TREE_ANOMALY_INPUT_V` and `TREE_KMEANS_INPUT_V` without geometry. Their result tables retain geometry for maps; the model-input views contain the attributes needed for scoring.
4. Run `4-bomen_OML_greeting_NL2SQL.sqlnb` to add greeting and NL2SQL workers to the supervised team. Run `5-Boment_OML_History.sqlnb` if you also want the separate history team and vector search over saved questions and answers.
5. Use the separate `*_tests*.sqlnb` and `*_checkSQL.sqlnb` notebooks to inspect source data and verify tools, saved results, and routing.

The Ask Oracle APEX application and its static JavaScript assets are **not in this folder**. Deploy them separately to display returned GeoJSON on a map. The notebooks do not contain the source data, the application export, or database credentials.
