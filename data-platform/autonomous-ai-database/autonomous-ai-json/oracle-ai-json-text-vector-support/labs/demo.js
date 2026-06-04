db.aggregate([{ $sql: "select * from DEPT_EMP_COL where json_textcontains(DATA, '$.DEPARTMENT.DEPARTMENT_NAME', 'Retail')" }])
db.aggregate([{ $sql: "select * from DEPT_EMP_COL where contains (DATA, 'fuzzy(Account)' ) > 0" }])
db.aggregate([{ $sql: "select * from DEPT_EMP_COL where contains (DATA, 'fuzzy(William)' ) > 0" }])
db.aggregate([{ $sql: "select * from DEPT_EMP_COL where contains (DATA, 'about(IT)' ) > 0" }])
db.aggregate([{ $sql: "select * from DEPT_EMP_COL where contains (DATA, 'about(support)' ) > 0" }])

db.aggregate([{ $sql: "select substr(t.data.sentence,1,100) from news_j_e_t t order by vector_distance(t.data.embedding.vector(), TO_VECTOR(VECTOR_EMBEDDING(minilm_l12_v2_01 USING 'little red corvette' as data)), COSINE) fetch approx first 5 rows only;" }])

