# Example: Invalid Objects and Compile Errors

## User prompt

Show invalid objects and compile errors.

## Expected response style

Source: `ALL_OBJECTS`, `ALL_ERRORS` or DBA equivalents when available.

Start with aggregate evidence:

- total invalid objects visible;
- invalid objects by owner/schema and object type;
- total objects with compile errors;
- most affected schemas or object types.

Do not list hundreds of objects by default. Offer drill-down by owner, object type, object name, or error text.
