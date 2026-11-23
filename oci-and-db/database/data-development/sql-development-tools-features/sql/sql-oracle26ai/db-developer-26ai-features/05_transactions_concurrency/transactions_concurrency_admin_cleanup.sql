-- Restore transaction priority configuration in the SAME target PDB used for setup.
-- Suggested values below are the ORIGINAL values observed on one tested ADB Free instance,
-- NOT universal defaults. Override them when your original settings differ.
-- Run only if the configuration notebook executed ALTER SYSTEM.
-- SQLcl / SQL*Plus prompts: press Enter to accept the shown value, or type an override.
PROMPT Restoring transaction priority configuration.
PROMPT Suggested original values from the tested ADB Free instance:
PROMPT   PRIORITY_TXNS_HIGH_WAIT_TARGET   = 2147483647
PROMPT   PRIORITY_TXNS_MEDIUM_WAIT_TARGET = 2147483647
PROMPT   PRIORITY_TXNS_MODE               = ROLLBACK
PROMPT Check the values recorded before setup; these may differ on your instance.
ACCEPT PREV_HIGH_WAIT NUMBER DEFAULT '2147483647' PROMPT 'Original HIGH wait target [2147483647]: '
ACCEPT PREV_MEDIUM_WAIT NUMBER DEFAULT '2147483647' PROMPT 'Original MEDIUM wait target [2147483647]: '
ACCEPT PREV_MODE CHAR DEFAULT 'ROLLBACK' PROMPT 'Original mode (ROLLBACK or TRACK) [ROLLBACK]: '
PROMPT The selected values will be applied using ALTER SYSTEM.
ALTER SYSTEM SET priority_txns_high_wait_target = &PREV_HIGH_WAIT;
ALTER SYSTEM SET priority_txns_medium_wait_target = &PREV_MEDIUM_WAIT;
ALTER SYSTEM SET priority_txns_mode = &PREV_MODE;
PROMPT Verify restored values:
SELECT name, value FROM v$parameter
WHERE name IN ('priority_txns_mode', 'priority_txns_high_wait_target',
               'priority_txns_medium_wait_target') ORDER BY name;
UNDEFINE PREV_HIGH_WAIT PREV_MEDIUM_WAIT PREV_MODE
