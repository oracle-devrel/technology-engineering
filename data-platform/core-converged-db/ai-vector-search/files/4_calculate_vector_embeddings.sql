REM  Calculate embeddings directly in the database

-- connect to the VECTOR_USER 

connect vector_user/Oracle_4U@FREEPDB1

-- create table CCNEWS
create table if not exists CCNEWS (
    id number(10) not null,
    info VARCHAR2(4000),
    vec VECTOR
);


-- Use the doc_model previously loaded to calculate the vector embeddings
-- Please plan additional time to complete this statement 

insert into CCNEWS (id, info, vec)
select rownum,
       sentence,
       TO_VECTOR(VECTOR_EMBEDDING(doc_model USING sentence as data))
from CCNEWS_TMP;


commit;
