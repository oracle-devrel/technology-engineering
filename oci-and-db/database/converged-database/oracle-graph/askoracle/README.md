# AskOracle chatbot-viz Graph Setup

This folder keeps the AskOracle chatbot-viz version 3.

03.09.2026

# When to use this asset?
Use this asset as a reference for setting up the AskOracle chatbot-viz (version 3) and exploring property graph capabilities using Select AI for Graph within your Autonomous Oracle AI Database.
This setup enables users to interact with banking graph schemas using natural language queries, combining Select AI capabilities with interactive visualization tools and customized notebooks.

# How to use this asset?
Note - Please check the demo_Bank_AI_Queries notebook located in 4-SELECTAIforGraph to set up and configure your profile before deploying the application.converged-database/oracle-graph/graphselectai

## Working App

Use the AskOracle / chatbot-viz app version.

For this version, graph works when these parts are present:

1. Import the AskOracle chatbot-viz app.
2. Install the Graph Visualization plug-in.
3. Create the graph SQL function in sql Commends:

```sql
CREATE OR REPLACE FUNCTION ask_oracle_graph_sql (
    p_prompt_id IN VARCHAR2
) RETURN CLOB
IS
BEGIN
    -- Function body goes here.
    -- This function must return the SQL query used by the Graph Visualization region.
    RETURN NULL;
END ask_oracle_graph_sql;
/
```
For example back_graph :
```sql
CREATE OR REPLACE FUNCTION ask_oracle_graph_sql (
    p_prompt_id IN VARCHAR2
) RETURN CLOB
AUTHID DEFINER
IS
    l_prompt       CLOB;
    l_prompt_low   VARCHAR2(32767);
    l_account_id   VARCHAR2(100);

    l_default_sql CLOB := q'[
SELECT v_id, e_id, p_id
FROM GRAPH_TABLE (
    bank_graph
    MATCH (src)-[e]->(dst)
    COLUMNS (
        VERTEX_ID(src) AS v_id,
        EDGE_ID(e)     AS e_id,
        VERTEX_ID(dst) AS p_id
    )
)
FETCH FIRST 150 ROWS ONLY
]';

BEGIN
    BEGIN
        SELECT prompt
          INTO l_prompt
          FROM user_cloud_ai_conversation_prompts
         WHERE conversation_prompt_id = p_prompt_id;
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            BEGIN
                SELECT prompt
                  INTO l_prompt
                  FROM adb_chat_prompts
                 WHERE conversation_prompt_id = p_prompt_id;
            EXCEPTION
                WHEN NO_DATA_FOUND THEN
                    RETURN l_default_sql;
            END;
    END;

    l_prompt_low := LOWER(DBMS_LOB.SUBSTR(l_prompt, 32767, 1));

    IF REGEXP_LIKE(l_prompt_low, '(receive|receiv|incoming)')
       AND INSTR(l_prompt_low, 'transfer') > 0
    THEN
        RETURN q'[
WITH edges AS (
    SELECT v_id, e_id, p_id, dst_id
    FROM GRAPH_TABLE (
        bank_graph
        MATCH (src)-[e]->(dst)
        COLUMNS (
            VERTEX_ID(src) AS v_id,
            EDGE_ID(e)     AS e_id,
            VERTEX_ID(dst) AS p_id,
            dst.ID         AS dst_id
        )
    )
),
top_recipients AS (
    SELECT dst_id
    FROM edges
    GROUP BY dst_id
    ORDER BY COUNT(*) DESC
    FETCH FIRST 20 ROWS ONLY
)
SELECT e.v_id, e.e_id, e.p_id
FROM edges e
JOIN top_recipients t
  ON t.dst_id = e.dst_id
]';
    END IF;

    l_account_id := REGEXP_SUBSTR(
        DBMS_LOB.SUBSTR(l_prompt, 32767, 1),
        '[0-9]+'
    );

    IF l_account_id IS NOT NULL
       AND REGEXP_LIKE(l_prompt_low, '(transfer|send|account|acct)')
    THEN
        RETURN
            'SELECT v_id, e_id, p_id ' ||
            'FROM GRAPH_TABLE ( ' ||
            '  bank_graph ' ||
            '  MATCH (src)-[e]->(dst) ' ||
            '  WHERE src.ID = ' || l_account_id || ' ' ||
            '  COLUMNS ( ' ||
            '    VERTEX_ID(src) AS v_id, ' ||
            '    EDGE_ID(e) AS e_id, ' ||
            '    VERTEX_ID(dst) AS p_id ' ||
            '  ) ' ||
            ')';
    END IF;

    RETURN l_default_sql;

EXCEPTION
    WHEN OTHERS THEN
        RETURN l_default_sql;
END ask_oracle_graph_sql;

```


4. Set the Graph page region source to:

```sql
RETURN ask_oracle_graph_sql(:P11_PROMPT_ID);
```

## Important Notes

- The Graph Visualization region reads SQL from `ASK_ORACLE_GRAPH_SQL`.
- The graph query must return graph plug-in columns such as `V_ID`, `E_ID`, and `P_ID`.


## Test Questions

Use these questions after setup:

```text
Which accounts receive the most transfers?
Show transfers from account 406 as a graph
Show transfers from account 934 as a graph
```

# License

Copyright (c) 2026 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
