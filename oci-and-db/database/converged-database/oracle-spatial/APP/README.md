
# AskOracle: Spatial, Graph, and AI Agents

This version extends AskOracle 5.0.1 with interactive Spatial and Graph toolkits, the Graph Visualization plug-in, map styling, and Select AI Agent team support. It is a general-purpose APEX application: the questions it can answer depend on the data, profiles, and agents configured in your database.

**Reviewed:** 2026-11-16

## When to use this asset?

Use this application when you want to ask questions in natural language and inspect the results in chat, on a map, or as a graph.

- **Spatial visualization:** Display returned points, lines, and polygons. Style map features using attributes in the query results.
- **Graph visualization:** Explore graph results through the Graph Visualization plug-in and Export PDF file on plugin.
- **Agent teams:** Select a database-defined Agent team to route questions to specialized tools and agents.
- **Toolkits:** Use the Spatial and Graph toolkits to check and enable their application components.


## How to use this asset?

For more details, check out the [AskOracle Medium blog post](https://medium.com/@maryam.oracle2025/askoracle-part-two-from-graph-and-spatial-visualization-to-interactive-toolkits-and-ai-agents-c702f1cabb44?postPublishedType=initial).

1. Import `f121/f121.sql` into Oracle APEX and select the intended parsing schema.
2. Review and install the application's supporting objects. Confirm that its application processes, static files, and Graph Visualization plug-in are present.
3. Check **Graph Toolkit → Component checks**. Open **Spatial Toolkit → Install** if the spatial components are not yet installed, then install it.
4. Configure the Select AI profiles and/or Agent teams you intend to use. These database objects and their source data must be prepared separately; importing the APEX application does not create your datasets or OML models.
5. Run the application. Ask a spatial question, check that the returned features appear on the map, and try the map styling controls. Then test a graph question and an Agent team question.

`f121_static_application_files.zip` is a separate backup of the application's JavaScript, CSS, and other static files. Use it if any static files are missing after import.

For maps, return geometry as **GeoJSON in WGS 84 (EPSG:4326)**. Source geometry may remain in its original coordinate system in the database; transform it when producing the map result.

Sample datasets and agent, follow the [Den Haag dataset and notebook workflow](https://github.com/oracle-devrel/technology-engineering/tree/main/oci-and-db/database/converged-database/oracle-spatial/SpatialAI/Buurt_tree).

## Sample questions

These examples require suitable datasets and configured profiles or agents:

- “Show me 11 trees close to tree ID 5811455, including 5811455.”
- “Which five Den Haag neighbourhoods have the highest tree density despite having less than 30% green area?”
- “Group Quercus robur trees into three clusters by age and trunk-diameter class.”
- “Which tree records have unusual age and trunk-diameter combinations?”

For graph visualization, load the [Bank Graph sample data](https://github.com/oracle-devrel/technology-engineering/blob/main/oci-and-db/database/converged-database/oracle-graph/askoracle/sampledata.zip) and configure its graph profile. Then try:

- “Which accounts receive the most transfers?”
- “Show transfers from account 406 as a graph.”
- “Show transfers from account 934 as a graph.”

## License

Copyright (c) 2026 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0. See [LICENSE.txt](LICENSE.txt). Third-party components retain their respective licenses.
