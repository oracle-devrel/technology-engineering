REM  Load the ONNX model into the database with DBMS_VECTOR

connect vector_user/Oracle_4U@FREEPDB1

col model_name format a12
col mining_function format a12
col algorithm format a12
col attribute_name format a20
col data_type format a30
col vector_info format a30
set lines 120

SELECT model_name, mining_function, algorithm,
algorithm_type, model_size
FROM user_mining_models
WHERE model_name = 'DOC_MODEL'
ORDER BY model_name;


SELECT model_name, attribute_name, attribute_type, data_type, vector_info
FROM user_mining_model_attributes
WHERE model_name = 'DOC_MODEL'
ORDER BY attribute_name;