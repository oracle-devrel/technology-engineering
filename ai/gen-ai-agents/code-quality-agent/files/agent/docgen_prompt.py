"""
File name: docgen_prompt.py
Author: L. Saetta
Date last modified: 2026-01-12
Python Version: 3.11
License: MIT

Description:
  Prompt for documentation generation of Python files.

  You can customize the documentation style and content by modifying the DOC_PROMPT variable below.

"""

DOC_PROMPT = """
You are a senior Python engineer.

You must generate documentation for the following Python file.
The user request below specifies what to emphasize. Follow it carefully when relevant.

IMPORTANT SAFETY / COMPLIANCE RULES (highest priority):
- Never include secrets, credentials, API keys, tokens, private keys, or passwords.
- Never include or reproduce personal data (PII). This includes (non-exhaustive):
  emails, phone numbers, IBAN, credit card numbers, tax IDs, personal addresses.
- If the source contains sensitive-looking values or PII-like strings, DO NOT reproduce them.
  Instead, describe them generically and mention that values were redacted.

USER REQUEST (high priority):
{request}

Output format:
- Markdown
- Title: the file path
- Sections:
  - Overview (what it does, in 3-6 bullet points)
  - Public API (functions/classes likely intended for import/use)
  - Key behaviors and edge cases
  - Inputs/outputs and side effects
  - Usage examples (short, realistic) - IMPORTANT: use placeholders, never real identifiers
  - Risks/TODOs (brief)

Keep it practical and concise.

FILE PATH: {relpath}

PYTHON SOURCE:
```python
{source}
```
"""

# This is the prompt with instructions for the final report
REPORT_PROMPT = """
You are a senior Python engineer.

Today is: {now_datetime}.

Generate a final report in markdown based on the following inputs.

## Inputs
- Root directory: {root_dir}
- Processed: {num_files}
- Header issues found: {header_issues}
- Secrets issues found: {secret_issues}
- License check (repository license file): {license_check}
- Dependency license failures (requirements.txt direct deps): {dep_license_failures}
- Dependency license warnings (unknown/not installed/ambiguous): {dep_license_warnings}
- PII hard failures (direct identifiers): {pii_hard_failures}
- PII warnings (structured name/address): {pii_warnings}
- requirements.txt check: {requirements_check}

## Policies
### PII Policy
Explain the policy outcome clearly:
- HARD FAIL: direct identifiers (email, phone, IBAN, credit card, tax id, etc.)
- WARN: possible names/addresses only when in structured form

### Dependency license policy
- A dependency is NON-COMPLIANT if its detected license is not in the accepted allow-list.
- If a dependency license is UNKNOWN or NOT_INSTALLED, treat it as a WARNING unless configured otherwise.
- If requirements.txt is missing at repository root, dependency checks are incomplete and this must be a STRONG WARNING.

## Pass/Fail rules (must be explicit)
The overall outcome is FAIL if any of the following are true:
- Any secrets issues are found
- Any PII hard failures exist
- Repository license check indicates non-compliance or missing/invalid license (if applicable)
- Any dependency license failures exist

The overall outcome is WARN (not FAIL) if any of the following are true and none of the FAIL conditions hold:
- requirements.txt is missing at repository root
- Any dependency license warnings exist (UNKNOWN / NOT_INSTALLED / ambiguous like "BSD")
- Any PII warnings exist

## Output requirements
- Title: Code Compliance & Risk Assessment Report
- Analysis made on root directory: {root_dir}
- Organize the report into dedicated sections with proper headings:
  1) Executive summary (Outcome: PASS/FAIL/WARN + key numbers + strongest issues first)
  2) Requirements & dependency visibility (requirements.txt presence + what was checked)
  3) License compliance (repository license file)
  4) Dependency license compliance (failures and warnings)
  5) Secrets scan results
  6) PII compliance (separate subsections for HARD FAIL and WARN)
  7) Header compliance
  8) Recommendations (actionable, prioritized)

## Safety rules for the report (highest priority)
- Never include secrets or credentials.
- Never include raw PII. If excerpts are present in the inputs, assume they are already masked;
  do not attempt to reconstruct or infer the original values.
- Do not paste any third-party license text. Refer to licenses by name only.
- When providing examples, always use placeholders.

Keep it concise, practical, and suitable for a CI compliance artifact.
"""
