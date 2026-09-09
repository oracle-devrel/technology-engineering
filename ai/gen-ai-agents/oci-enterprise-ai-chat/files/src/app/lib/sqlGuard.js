// Safety guard before executing NL2SQL-generated SQL through DBTools `sql_run`.
// Mirrors the reference Streamlit demo's `is_read_only_sql`: allow exactly ONE
// read-only statement (SELECT or WITH), reject anything that writes or runs
// procedural code, and reject multiple statements. It is a defensive net — the
// generated SQL should already be a clean SELECT, but execution runs arbitrary
// SQL so we gate it.
export function isReadOnlySql(sql) {
  const normalized = String(sql || '').trim().replace(/;+\s*$/, '').trim();
  if (!normalized || normalized.includes(';')) return false;
  if (!/^(select|with)\b/i.test(normalized)) return false;
  const blocked = /\b(insert|update|delete|merge|create|alter|drop|truncate|grant|revoke|call|exec|execute|begin|declare)\b/i;
  return !blocked.test(normalized);
}
