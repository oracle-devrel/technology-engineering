-- required privileges
-- SODA_APP, CONNECT, RESOURCE
-- execute on DBMS_CLOUD, DBMS_VECTOR, DBMS_DATA_MINING
-- CREATE MINIG MODEL

drop table if exists DEPT_EMP_COL;
create json collection table DEPT_EMP_COL;

declare
	dept_de DocElement;
	jd JSON;	
begin
	for rd in (select JSON{*} dept from hr.departments) loop
		dept_de := DocElement(doc_conv.json2json_element_t(rd.dept));
		dept_de.setRootKey('DEPARTMENT');
		dept_de.aggregate('EMPLOYEES','DEPARTMENT_ID');
		jd := doc_conv.json_element_t2json(dept_de.getAsJSON);
		insert into DEPT_EMP_COL values (jd);
	end loop;	
end;
/

create search index DEPT_EMP_COL_SEARCH_IDX on DEPT_EMP_COL(DATA) for json;

select *
from DEPT_EMP_COL
where json_textcontains(DATA, '$.DEPARTMENT.DEPARTMENT_NAME', 'Retail');

select * from DEPT_EMP_COL
where contains (DATA, 'fuzzy(Retail)' ) > 0;

select * from DEPT_EMP_COL
where contains (DATA, 'about(IT)' ) > 0;


drop view if exists news_j_e_view
drop table if exists news;

begin
    dbms_cloud.drop_credential(credential_name=>'DBMS_CLOUD_CREDENTIAL');
end;
/

begin
    dbms_cloud.create_credential(credential_name=>'DBMS_CLOUD_CREDENTIAL',
                                      username=>'<cloud_username>',
                                      password=>'<authentication_token>');
end;
/

begin
  dbms_cloud.create_external_table(
  		 table_name      => 'NEWS',
         credential_name => 'DBMS_CLOUD_CREDENTIAL',
         file_uri_list   => 'https://objectstorage.../o/dataset_200K.txt',
         column_list     => 'SENTENCE VARCHAR2(4000)',
         format          => json_object( 'readsize' value '100000000',
                                         'rejectlimit' value 'unlimited',
                                         'recorddelimiter' value 'X''A''')
     );
end;
/

create or replace json collection view news_json_view
as
select json{*}
from news;

begin
   dbms_vector.load_onnx_model_cloud ( model_name => 'minilm_l12_v2_01',
                                       credential => 'DBMS_CLOUD_CREDENTIAL',
                                       uri => 'https://objectstorage.../o/all_MiniLM_L12_v2.onnx',
									   metadata => JSON('{"function" : "embedding", "embeddingOutput" : "embedding" , "input": {"input": ["DATA"]}}')
									  );
end;
/									  

SELECT model_name, mining_function, algorithm,
algorithm_type, model_size
FROM user_mining_models
WHERE model_name like 'MINILM_L12_V2_01'
ORDER BY model_name;

create or replace json collection view news_j_e_v
as
select json{sentence,
            'embedding' : vector_embedding(minilm_l12_v2_01 using sentence as data)}
from news

create json collection table news_j_e_t;

insert into news_j_e_t
select *
from news_j_e_v;

select t.data."_id", substr(t.data.sentence,1,100)
from news_j_e_t t
order by vector_distance(t.data.embedding.vector(), 
                         TO_VECTOR(VECTOR_EMBEDDING(minilm_l12_v2_01 USING 'little red corvette' as data)), 
                         COSINE)
fetch approx first 5 rows only;
