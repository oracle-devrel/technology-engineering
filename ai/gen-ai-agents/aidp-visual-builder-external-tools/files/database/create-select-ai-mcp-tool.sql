-- Run this after creating and testing your Select AI profile.
-- Replace YOUR_SELECT_AI_PROFILE with the profile name you created.
-- This registers a database MCP tool; it does not create or insert table data.

BEGIN
  DBMS_CLOUD_AI_AGENT.CREATE_TOOL(
    tool_name  => 'SUPPLIER_FEEDBACK_SQL',
    attributes => '{
      "tool_type": "SQL",
      "instruction": "Answer natural-language questions using only the tables allowed by the configured Select AI profile. Use the runsql action to return query results. Do not modify data.",
      "tool_params": {
        "profile_name": "YOUR_SELECT_AI_PROFILE"
      }
    }'
  );
END;
/

-- Confirm the tool is registered for this database user.
SELECT tool_name, description, status
FROM USER_AI_AGENT_TOOLS
WHERE tool_name = 'SUPPLIER_FEEDBACK_SQL';
