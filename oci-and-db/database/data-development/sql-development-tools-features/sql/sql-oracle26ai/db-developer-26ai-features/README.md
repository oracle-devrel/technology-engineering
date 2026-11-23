# Oracle Database Developer Story Content
Reviewed: 23.11.2026

## Audience

The primary audience is the Oracle Database Developer (SQL + PL/SQL). The story set can support secondary application-language audiences where the existing content provides a useful developer conversation.

## Content order

01. Write Better SQL
02. Model Data Better
03. Modern Application Data
04. Program the Database
05. Transactions & Concurrency
06. Developer Productivity
07. AI & Search
08. Deep Data Security

## Story content standard

Each story defines the developer/application problem, the scope of the story, why the topic matters to developers, the story arc, the capabilities covered, how each capability changes development, developer and application outcomes, and authoritative documentation.

For features primarily implemented outside the database, the material stays at overview level and explicitly identifies the database developer's preparation/role. The notebooks do not spend demo time on external application implementation. MLE receives a small hands-on example because it is a genuine database programming capability.

Before/after examples are used when they make the development improvement visible. They are not required where a capability is genuinely new or where a comparison would be artificial.

Each capability in a notebook is kept focused on its own purpose. A notebook may include verification when behavior, metadata, or enforcement needs to be established; verification is not used as a duplicate execution of the same SQL.

Cleanup is maintained separately from the walkthrough notebooks.

## Environment setup

The two setup scripts are in `00_setup` in the final content archive: one administrator script and one schema script. No setup notebook is required. The schema setup also performs an MLE readiness check because MLE execution can be disabled at CDB/PDB/session scope.

## AI and embeddings

The core AI & Search story focuses on semantic and hybrid retrieval. The related `in_database_embeddings` material is an additional path for importing a compatible ONNX embedding model and generating embeddings inside Oracle AI Database.
