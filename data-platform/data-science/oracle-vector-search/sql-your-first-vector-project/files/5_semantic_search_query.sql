REM  Use semantic search query using vectors


-- connect to the VECTOR_USER 

connect vector_user/Oracle_4U@FREEPDB1

-- use "COSINE" parameter in VECTOR_DISTANCE to calculate the distance between two vectors

set timing on
col info format a90
set lines 120

select id, info
from CCNEWS
order by vector_distance(vec, TO_VECTOR(VECTOR_EMBEDDING(doc_model USING 'little red corvette' as data)), COSINE)
fetch approx first 5 rows only;


-- Check the execution plan

set autotrace traceonly explain

select id, info
from CCNEWS
order by vector_distance(vec, TO_VECTOR(VECTOR_EMBEDDING(doc_model USING 'little red corvette' as data)), COSINE)
fetch approx first 5 rows only;