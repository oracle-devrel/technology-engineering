# Playground test questions

Replace the bracketed text with values from your permitted test database and indexed files.

1. **Select AI only:** “Summarize feedback and ratings for [vendor].” Check the result against database rows.
2. **Vector search only:** “According to the uploaded [guide], what information should we ask for when [issue] happens?” Check that a matching passage is returned.
3. **Combined:** “Summarize the database feedback for [vendor], use the uploaded files to identify what information is missing, and write a short follow-up note in plain English. Do not decide whether to keep the vendor.” Check the trace shows both tools ran and that the answer keeps database facts separate from document guidance.
