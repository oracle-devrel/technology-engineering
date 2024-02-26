prompt --application/set_environment
set define off verify off feedback off
whenever sqlerror exit sql.sqlcode rollback
--------------------------------------------------------------------------------
--
-- Oracle APEX export file
--
-- You should run this script using a SQL client connected to the database as
-- the owner (parsing schema) of the application or as a database user with the
-- APEX_ADMINISTRATOR_ROLE role.
--
-- This export file has been automatically generated. Modifying this file is not
-- supported by Oracle and can lead to unexpected application and/or instance
-- behavior now or in the future.
--
-- NOTE: Calls to apex_application_install override the defaults below.
--
--------------------------------------------------------------------------------
begin
wwv_flow_imp.import_begin (
 p_version_yyyy_mm_dd=>'2023.10.31'
,p_default_workspace_id=>7462517214675520
);
end;
/
prompt --workspace/rest-source-catalogs//oci_document_understanding
begin
wwv_web_src_catalog_api.create_catalog(
 p_id=>wwv_flow_imp.id(33178613734671841)
,p_name=>'OCI Document Understanding'
,p_internal_name=>'OCI DOCUMENT UNDERSTANDING'
,p_description=>'A collection of APIs to the OCI Document Understanding service'
,p_format=>'APEX'
);
end;
/
prompt --workspace/rest-source-catalogs/services//oci_analyze_document_for_key_value_extract_from_objectstorage_response_inline
begin
wwv_flow_imp.g_varchar2_table := wwv_flow_imp.empty_varchar2_table;
wwv_flow_imp.g_varchar2_table(1) := '{'||wwv_flow.LF||
'"data_profile":{'||wwv_flow.LF||
'"name":"OCI Analyze Document from Object Storage Results in Response"'||wwv_flow.LF||
',"format":"';
wwv_flow_imp.g_varchar2_table(2) := 'JSON"'||wwv_flow.LF||
',"has_header_row":"N"'||wwv_flow.LF||
',"row_selector":"items"'||wwv_flow.LF||
',"is_single_row":"N"'||wwv_flow.LF||
',"columns":['||wwv_flow.LF||
']'||wwv_flow.LF||
'}'||wwv_flow.LF||
',"plugin_a';
wwv_flow_imp.g_varchar2_table(3) := 'ttributes":{'||wwv_flow.LF||
'}'||wwv_flow.LF||
',"operations":['||wwv_flow.LF||
'{'||wwv_flow.LF||
'"operation":"POST"'||wwv_flow.LF||
',"name":"AnalyzeDocumentExtractKeyValFromObjectS';
wwv_flow_imp.g_varchar2_table(4) := 'torageResponseInline"'||wwv_flow.LF||
',"url_pattern":"."'||wwv_flow.LF||
',"request_body_template":"{\r\n   \"document\": {\r\n      ';
wwv_flow_imp.g_varchar2_table(5) := '\"source\": \"OBJECT_STORAGE\",\r\n      \"bucketName\": \"#IN_BUCKET_NAME#\",\r\n      \"namespaceN';
wwv_flow_imp.g_varchar2_table(6) := 'ame\": \"#NAMESPACE#\",\r\n      \"objectName\": \"#OBJECT_NAME#\"\r\n   },\r\n   \"features\": [{\r';
wwv_flow_imp.g_varchar2_table(7) := '\n      \"featureType\": \"#FEATURE#\",\r\n      \"modelId\": \"#MODEL_ID#\"\r\n   }],\r\n   \"compa';
wwv_flow_imp.g_varchar2_table(8) := 'rtmentId\": \"#COMPARTMENT_ID#\"\r\n}"'||wwv_flow.LF||
',"allow_fetch_all_rows":"N"'||wwv_flow.LF||
',"parameters":['||wwv_flow.LF||
'{'||wwv_flow.LF||
'"name":"COMPART';
wwv_flow_imp.g_varchar2_table(9) := 'MENT_ID"'||wwv_flow.LF||
',"param_type":"BODY"'||wwv_flow.LF||
',"data_type":"VARCHAR2"'||wwv_flow.LF||
',"is_required":"N"'||wwv_flow.LF||
',"direction":"IN"'||wwv_flow.LF||
',"is_stat';
wwv_flow_imp.g_varchar2_table(10) := 'ic":"N"'||wwv_flow.LF||
',"is_array":"N"'||wwv_flow.LF||
',"omit_when_null":"N"'||wwv_flow.LF||
',"is_query_param":"N"'||wwv_flow.LF||
'}'||wwv_flow.LF||
',{'||wwv_flow.LF||
'"name":"Content-Type"'||wwv_flow.LF||
',"par';
wwv_flow_imp.g_varchar2_table(11) := 'am_type":"HEADER"'||wwv_flow.LF||
',"data_type":"VARCHAR2"'||wwv_flow.LF||
',"is_required":"N"'||wwv_flow.LF||
',"direction":"IN"'||wwv_flow.LF||
',"value":"application';
wwv_flow_imp.g_varchar2_table(12) := '\/json"'||wwv_flow.LF||
',"is_static":"Y"'||wwv_flow.LF||
',"is_array":"N"'||wwv_flow.LF||
',"omit_when_null":"N"'||wwv_flow.LF||
',"is_query_param":"N"'||wwv_flow.LF||
'}'||wwv_flow.LF||
',{'||wwv_flow.LF||
'"name":"FE';
wwv_flow_imp.g_varchar2_table(13) := 'ATURE"'||wwv_flow.LF||
',"param_type":"BODY"'||wwv_flow.LF||
',"data_type":"VARCHAR2"'||wwv_flow.LF||
',"is_required":"N"'||wwv_flow.LF||
',"direction":"IN"'||wwv_flow.LF||
',"is_static';
wwv_flow_imp.g_varchar2_table(14) := '":"N"'||wwv_flow.LF||
',"is_array":"N"'||wwv_flow.LF||
',"omit_when_null":"N"'||wwv_flow.LF||
',"is_query_param":"N"'||wwv_flow.LF||
'}'||wwv_flow.LF||
',{'||wwv_flow.LF||
'"name":"IN_BUCKET_NAME"'||wwv_flow.LF||
',"par';
wwv_flow_imp.g_varchar2_table(15) := 'am_type":"BODY"'||wwv_flow.LF||
',"data_type":"VARCHAR2"'||wwv_flow.LF||
',"is_required":"N"'||wwv_flow.LF||
',"direction":"IN"'||wwv_flow.LF||
',"is_static":"N"'||wwv_flow.LF||
',"is_a';
wwv_flow_imp.g_varchar2_table(16) := 'rray":"N"'||wwv_flow.LF||
',"omit_when_null":"N"'||wwv_flow.LF||
',"is_query_param":"N"'||wwv_flow.LF||
'}'||wwv_flow.LF||
',{'||wwv_flow.LF||
'"name":"MODEL_ID"'||wwv_flow.LF||
',"param_type":"BODY"'||wwv_flow.LF||
',"';
wwv_flow_imp.g_varchar2_table(17) := 'data_type":"VARCHAR2"'||wwv_flow.LF||
',"is_required":"N"'||wwv_flow.LF||
',"direction":"IN"'||wwv_flow.LF||
',"is_static":"N"'||wwv_flow.LF||
',"is_array":"N"'||wwv_flow.LF||
',"omit_w';
wwv_flow_imp.g_varchar2_table(18) := 'hen_null":"N"'||wwv_flow.LF||
',"is_query_param":"N"'||wwv_flow.LF||
'}'||wwv_flow.LF||
',{'||wwv_flow.LF||
'"name":"NAMESPACE"'||wwv_flow.LF||
',"param_type":"BODY"'||wwv_flow.LF||
',"data_type":"VARCH';
wwv_flow_imp.g_varchar2_table(19) := 'AR2"'||wwv_flow.LF||
',"is_required":"N"'||wwv_flow.LF||
',"direction":"IN"'||wwv_flow.LF||
',"is_static":"N"'||wwv_flow.LF||
',"is_array":"N"'||wwv_flow.LF||
',"omit_when_null":"N"'||wwv_flow.LF||
',"i';
wwv_flow_imp.g_varchar2_table(20) := 's_query_param":"N"'||wwv_flow.LF||
'}'||wwv_flow.LF||
',{'||wwv_flow.LF||
'"name":"OBJECT_NAME"'||wwv_flow.LF||
',"param_type":"BODY"'||wwv_flow.LF||
',"data_type":"VARCHAR2"'||wwv_flow.LF||
',"is_requi';
wwv_flow_imp.g_varchar2_table(21) := 'red":"N"'||wwv_flow.LF||
',"direction":"IN"'||wwv_flow.LF||
',"is_static":"N"'||wwv_flow.LF||
',"is_array":"N"'||wwv_flow.LF||
',"omit_when_null":"N"'||wwv_flow.LF||
',"is_query_param":';
wwv_flow_imp.g_varchar2_table(22) := '"N"'||wwv_flow.LF||
'}'||wwv_flow.LF||
',{'||wwv_flow.LF||
'"name":"RESPONSE"'||wwv_flow.LF||
',"param_type":"BODY"'||wwv_flow.LF||
',"is_required":"N"'||wwv_flow.LF||
',"direction":"OUT"'||wwv_flow.LF||
',"is_static":"';
wwv_flow_imp.g_varchar2_table(23) := 'N"'||wwv_flow.LF||
',"is_array":"N"'||wwv_flow.LF||
',"omit_when_null":"N"'||wwv_flow.LF||
',"is_query_param":"N"'||wwv_flow.LF||
'}'||wwv_flow.LF||
']'||wwv_flow.LF||
'}'||wwv_flow.LF||
']'||wwv_flow.LF||
',"parameters":['||wwv_flow.LF||
']'||wwv_flow.LF||
'}'||wwv_flow.LF||
'';
wwv_web_src_catalog_api.create_catalog_service(
 p_id=>wwv_flow_imp.id(7370545384360636)
,p_catalog_id=>wwv_flow_imp.id(33178613734671841)
,p_name=>'OCI Analyze Document for Key Value Extract from ObjectStorage Response Inline'
,p_description=>wwv_flow_string.join(wwv_flow_t_varchar2(
'Analyze a Document using OCI Document Understanding AnalyzeDocument API to Extract Key Value pairs. ',
'',
'The Rest Data Source is configured to use Object Storage as the Input, returning the analysis in the response and supports all analysis types using the standard and customer models.',
'',
'Update the Base URL to the region hosting the service.'))
,p_base_url=>'https://document.aiservice.eu-frankfurt-1.oci.oraclecloud.com/'
,p_service_path=>'20221109/actions/analyzeDocument'
,p_plugin_internal_name=>'NATIVE_OCI'
,p_authentication_type=>'OCI'
,p_details_json=>wwv_flow_imp.g_varchar2_table
,p_version=>'20231117'
);
end;
/
prompt --workspace/rest-source-catalogs/services//oci_analyze_document_from_object_storage_results_on_object_storage
begin
wwv_flow_imp.g_varchar2_table := wwv_flow_imp.empty_varchar2_table;
wwv_flow_imp.g_varchar2_table(1) := '{'||wwv_flow.LF||
'"data_profile":{'||wwv_flow.LF||
'"name":"OCI Analyze Document from Object Storage"'||wwv_flow.LF||
',"format":"JSON"'||wwv_flow.LF||
',"has_header_r';
wwv_flow_imp.g_varchar2_table(2) := 'ow":"N"'||wwv_flow.LF||
',"row_selector":"items"'||wwv_flow.LF||
',"is_single_row":"N"'||wwv_flow.LF||
',"columns":['||wwv_flow.LF||
']'||wwv_flow.LF||
'}'||wwv_flow.LF||
',"plugin_attributes":{'||wwv_flow.LF||
'}'||wwv_flow.LF||
',"ope';
wwv_flow_imp.g_varchar2_table(3) := 'rations":['||wwv_flow.LF||
'{'||wwv_flow.LF||
'"operation":"POST"'||wwv_flow.LF||
',"name":"AnalyzeDocumentFromToObjectStorage"'||wwv_flow.LF||
',"url_pattern":"."'||wwv_flow.LF||
',"re';
wwv_flow_imp.g_varchar2_table(4) := 'quest_body_template":"{\r\n   \"document\": {\r\n      \"source\": \"OBJECT_STORAGE\",\r\n      \"bu';
wwv_flow_imp.g_varchar2_table(5) := 'cketName\": \"#IN_BUCKET_NAME#\",\r\n      \"namespaceName\": \"#NAMESPACE#\",\r\n      \"objectName';
wwv_flow_imp.g_varchar2_table(6) := '\": \"#OBJECT_NAME#\"\r\n   },\"outputLocation\": {\r\n     \"namespaceName\": \"#NAMESPACE#\",\r\n ';
wwv_flow_imp.g_varchar2_table(7) := '    \"bucketName\": \"#OUT_BUCKET_NAME#\",\r\n     \"prefix\": \"#FOLDER_PREFIX#\"\r\n   },\r\n   \"';
wwv_flow_imp.g_varchar2_table(8) := 'features\": [{\r\n      \"featureType\": \"#FEATURE#\",\r\n      \"maxResults\": 5\r\n   }],\r\n   \';
wwv_flow_imp.g_varchar2_table(9) := '"compartmentId\": \"#COMPARTMENT_ID#\"\r\n}"'||wwv_flow.LF||
',"allow_fetch_all_rows":"N"'||wwv_flow.LF||
',"parameters":['||wwv_flow.LF||
'{'||wwv_flow.LF||
'"name":"C';
wwv_flow_imp.g_varchar2_table(10) := 'OMPARTMENT_ID"'||wwv_flow.LF||
',"param_type":"BODY"'||wwv_flow.LF||
',"data_type":"VARCHAR2"'||wwv_flow.LF||
',"is_required":"N"'||wwv_flow.LF||
',"direction":"IN"'||wwv_flow.LF||
',"i';
wwv_flow_imp.g_varchar2_table(11) := 's_static":"N"'||wwv_flow.LF||
',"is_array":"N"'||wwv_flow.LF||
',"omit_when_null":"N"'||wwv_flow.LF||
',"is_query_param":"N"'||wwv_flow.LF||
'}'||wwv_flow.LF||
',{'||wwv_flow.LF||
'"name":"Content-Type"';
wwv_flow_imp.g_varchar2_table(12) := ''||wwv_flow.LF||
',"param_type":"HEADER"'||wwv_flow.LF||
',"data_type":"VARCHAR2"'||wwv_flow.LF||
',"is_required":"N"'||wwv_flow.LF||
',"direction":"IN"'||wwv_flow.LF||
',"value":"appli';
wwv_flow_imp.g_varchar2_table(13) := 'cation\/json"'||wwv_flow.LF||
',"is_static":"Y"'||wwv_flow.LF||
',"is_array":"N"'||wwv_flow.LF||
',"omit_when_null":"N"'||wwv_flow.LF||
',"is_query_param":"N"'||wwv_flow.LF||
'}'||wwv_flow.LF||
',{'||wwv_flow.LF||
'"nam';
wwv_flow_imp.g_varchar2_table(14) := 'e":"FEATURE"'||wwv_flow.LF||
',"param_type":"BODY"'||wwv_flow.LF||
',"data_type":"VARCHAR2"'||wwv_flow.LF||
',"is_required":"N"'||wwv_flow.LF||
',"direction":"IN"'||wwv_flow.LF||
',"is_';
wwv_flow_imp.g_varchar2_table(15) := 'static":"N"'||wwv_flow.LF||
',"is_array":"N"'||wwv_flow.LF||
',"omit_when_null":"N"'||wwv_flow.LF||
',"is_query_param":"N"'||wwv_flow.LF||
'}'||wwv_flow.LF||
',{'||wwv_flow.LF||
'"name":"FOLDER_PREFIX"'||wwv_flow.LF||
'';
wwv_flow_imp.g_varchar2_table(16) := ',"param_type":"BODY"'||wwv_flow.LF||
',"data_type":"VARCHAR2"'||wwv_flow.LF||
',"is_required":"N"'||wwv_flow.LF||
',"direction":"IN"'||wwv_flow.LF||
',"is_static":"N"'||wwv_flow.LF||
',';
wwv_flow_imp.g_varchar2_table(17) := '"is_array":"N"'||wwv_flow.LF||
',"omit_when_null":"N"'||wwv_flow.LF||
',"is_query_param":"N"'||wwv_flow.LF||
'}'||wwv_flow.LF||
',{'||wwv_flow.LF||
'"name":"IN_BUCKET_NAME"'||wwv_flow.LF||
',"param_type';
wwv_flow_imp.g_varchar2_table(18) := '":"BODY"'||wwv_flow.LF||
',"data_type":"VARCHAR2"'||wwv_flow.LF||
',"is_required":"N"'||wwv_flow.LF||
',"direction":"IN"'||wwv_flow.LF||
',"is_static":"N"'||wwv_flow.LF||
',"is_array":"';
wwv_flow_imp.g_varchar2_table(19) := 'N"'||wwv_flow.LF||
',"omit_when_null":"N"'||wwv_flow.LF||
',"is_query_param":"N"'||wwv_flow.LF||
'}'||wwv_flow.LF||
',{'||wwv_flow.LF||
'"name":"NAMESPACE"'||wwv_flow.LF||
',"param_type":"BODY"'||wwv_flow.LF||
',"data_t';
wwv_flow_imp.g_varchar2_table(20) := 'ype":"VARCHAR2"'||wwv_flow.LF||
',"is_required":"N"'||wwv_flow.LF||
',"direction":"IN"'||wwv_flow.LF||
',"is_static":"N"'||wwv_flow.LF||
',"is_array":"N"'||wwv_flow.LF||
',"omit_when_nu';
wwv_flow_imp.g_varchar2_table(21) := 'll":"N"'||wwv_flow.LF||
',"is_query_param":"N"'||wwv_flow.LF||
'}'||wwv_flow.LF||
',{'||wwv_flow.LF||
'"name":"OBJECT_NAME"'||wwv_flow.LF||
',"param_type":"BODY"'||wwv_flow.LF||
',"data_type":"VARCHAR2"';
wwv_flow_imp.g_varchar2_table(22) := ''||wwv_flow.LF||
',"is_required":"N"'||wwv_flow.LF||
',"direction":"IN"'||wwv_flow.LF||
',"is_static":"N"'||wwv_flow.LF||
',"is_array":"N"'||wwv_flow.LF||
',"omit_when_null":"N"'||wwv_flow.LF||
',"is_qu';
wwv_flow_imp.g_varchar2_table(23) := 'ery_param":"N"'||wwv_flow.LF||
'}'||wwv_flow.LF||
',{'||wwv_flow.LF||
'"name":"OUT_BUCKET_NAME"'||wwv_flow.LF||
',"param_type":"BODY"'||wwv_flow.LF||
',"data_type":"VARCHAR2"'||wwv_flow.LF||
',"is_requi';
wwv_flow_imp.g_varchar2_table(24) := 'red":"N"'||wwv_flow.LF||
',"direction":"IN"'||wwv_flow.LF||
',"is_static":"N"'||wwv_flow.LF||
',"is_array":"N"'||wwv_flow.LF||
',"omit_when_null":"N"'||wwv_flow.LF||
',"is_query_param":';
wwv_flow_imp.g_varchar2_table(25) := '"N"'||wwv_flow.LF||
'}'||wwv_flow.LF||
',{'||wwv_flow.LF||
'"name":"RESPONSE"'||wwv_flow.LF||
',"param_type":"BODY"'||wwv_flow.LF||
',"is_required":"N"'||wwv_flow.LF||
',"direction":"OUT"'||wwv_flow.LF||
',"is_static":"';
wwv_flow_imp.g_varchar2_table(26) := 'N"'||wwv_flow.LF||
',"is_array":"N"'||wwv_flow.LF||
',"omit_when_null":"N"'||wwv_flow.LF||
',"is_query_param":"N"'||wwv_flow.LF||
'}'||wwv_flow.LF||
']'||wwv_flow.LF||
'}'||wwv_flow.LF||
']'||wwv_flow.LF||
',"parameters":['||wwv_flow.LF||
']'||wwv_flow.LF||
'}'||wwv_flow.LF||
'';
wwv_web_src_catalog_api.create_catalog_service(
 p_id=>wwv_flow_imp.id(7369275687346481)
,p_catalog_id=>wwv_flow_imp.id(33178613734671841)
,p_name=>'OCI Analyze Document from Object Storage Results on Object Storage'
,p_description=>wwv_flow_string.join(wwv_flow_t_varchar2(
'Analyze a Document using OCI Document Understanding AnalyzeDocument API. ',
'',
'The Rest Data Source is configured to use Object Storage as the Input and Output location for all analysis types using the standard and customer models.',
'',
'Update the Base URL to the region hosting the service.'))
,p_base_url=>'https://document.aiservice.eu-frankfurt-1.oci.oraclecloud.com/'
,p_service_path=>'20221109/actions/analyzeDocument'
,p_plugin_internal_name=>'NATIVE_OCI'
,p_authentication_type=>'OCI'
,p_details_json=>wwv_flow_imp.g_varchar2_table
,p_version=>'20231117'
);
end;
/
prompt --workspace/rest-source-catalogs/services//oci_document_understanding
begin
wwv_flow_imp.g_varchar2_table := wwv_flow_imp.empty_varchar2_table;
wwv_flow_imp.g_varchar2_table(1) := '{'||wwv_flow.LF||
'"data_profile":{'||wwv_flow.LF||
'"name":"OCI_Documents"'||wwv_flow.LF||
',"format":"JSON"'||wwv_flow.LF||
',"has_header_row":"N"'||wwv_flow.LF||
',"row_selector":"it';
wwv_flow_imp.g_varchar2_table(2) := 'ems"'||wwv_flow.LF||
',"is_single_row":"N"'||wwv_flow.LF||
',"columns":['||wwv_flow.LF||
'{'||wwv_flow.LF||
'"name":"COMPARTMENT_ID"'||wwv_flow.LF||
',"sequence":1'||wwv_flow.LF||
',"is_primary_key":"N"';
wwv_flow_imp.g_varchar2_table(3) := ''||wwv_flow.LF||
',"data_type":"VARCHAR2"'||wwv_flow.LF||
',"max_length":4000'||wwv_flow.LF||
',"has_time_zone":"N"'||wwv_flow.LF||
',"is_hidden":"N"'||wwv_flow.LF||
',"is_filterable":"';
wwv_flow_imp.g_varchar2_table(4) := 'Y"'||wwv_flow.LF||
',"selector":"compartmentId"'||wwv_flow.LF||
'}'||wwv_flow.LF||
',{'||wwv_flow.LF||
'"name":"PROCESSOR_JOB_ID"'||wwv_flow.LF||
',"sequence":2'||wwv_flow.LF||
',"is_primary_key":"Y"'||wwv_flow.LF||
',"';
wwv_flow_imp.g_varchar2_table(5) := 'data_type":"VARCHAR2"'||wwv_flow.LF||
',"max_length":2000'||wwv_flow.LF||
',"has_time_zone":"N"'||wwv_flow.LF||
',"is_hidden":"N"'||wwv_flow.LF||
',"is_filterable":"Y"'||wwv_flow.LF||
'';
wwv_flow_imp.g_varchar2_table(6) := ',"selector":"processorJobId"'||wwv_flow.LF||
'}'||wwv_flow.LF||
']'||wwv_flow.LF||
'}'||wwv_flow.LF||
',"plugin_attributes":{'||wwv_flow.LF||
'}'||wwv_flow.LF||
',"operations":['||wwv_flow.LF||
'{'||wwv_flow.LF||
'"operation":"POST"'||wwv_flow.LF||
',"n';
wwv_flow_imp.g_varchar2_table(7) := 'ame":"CreateProcessorJob"'||wwv_flow.LF||
',"url_pattern":"."'||wwv_flow.LF||
',"request_body_template":"{\r\n     \"processorConfig\"';
wwv_flow_imp.g_varchar2_table(8) := ': {\r\n     \"processorType\": \"GENERAL\",\r\n     \"features\": [\r\n     {\r\n        \"featureTy';
wwv_flow_imp.g_varchar2_table(9) := 'pe\": \"#FEATURE_TYPE#\",\r\n        \"maxResults\": 5\r\n     }\r\n    ]\r\n    },\r\n     \"inputL';
wwv_flow_imp.g_varchar2_table(10) := 'ocation\": {\r\n     \"sourceType\": \"OBJECT_STORAGE_LOCATIONS\",\r\n     \"objectLocations\": [{\r';
wwv_flow_imp.g_varchar2_table(11) := '\n        \"bucketName\": \"#IN_BUCKET_NAME#\",\r\n        \"namespaceName\": \"#NAMESPACE#\",\r\n  ';
wwv_flow_imp.g_varchar2_table(12) := '      \"objectName\": \"#OBJECT_NAME#\"\r\n     }]\r\n   },\"outputLocation\": {\r\n     \"bucketNam';
wwv_flow_imp.g_varchar2_table(13) := 'e\": \"#OUT_BUCKET_NAME#\",\r\n     \"namespaceName\": \"#NAMESPACE#\",\r\n     \"prefix\": \"#FOLDE';
wwv_flow_imp.g_varchar2_table(14) := 'R_PREFIX#\"\r\n   },\r\n     \"compartmentId\": \"#COMPARTMENT_ID#\"\r\n}"'||wwv_flow.LF||
',"allow_fetch_all_rows":"';
wwv_flow_imp.g_varchar2_table(15) := 'N"'||wwv_flow.LF||
',"parameters":['||wwv_flow.LF||
'{'||wwv_flow.LF||
'"name":"Accept"'||wwv_flow.LF||
',"param_type":"HEADER"'||wwv_flow.LF||
',"data_type":"VARCHAR2"'||wwv_flow.LF||
',"is_required":"';
wwv_flow_imp.g_varchar2_table(16) := 'N"'||wwv_flow.LF||
',"direction":"IN"'||wwv_flow.LF||
',"value":"application\/json"'||wwv_flow.LF||
',"is_static":"Y"'||wwv_flow.LF||
',"is_array":"N"'||wwv_flow.LF||
',"omit_when_null"';
wwv_flow_imp.g_varchar2_table(17) := ':"N"'||wwv_flow.LF||
',"is_query_param":"N"'||wwv_flow.LF||
'}'||wwv_flow.LF||
',{'||wwv_flow.LF||
'"name":"COMPARTMENT_ID"'||wwv_flow.LF||
',"param_type":"BODY"'||wwv_flow.LF||
',"data_type":"VARCHAR2"';
wwv_flow_imp.g_varchar2_table(18) := ''||wwv_flow.LF||
',"is_required":"N"'||wwv_flow.LF||
',"direction":"IN"'||wwv_flow.LF||
',"is_static":"N"'||wwv_flow.LF||
',"is_array":"N"'||wwv_flow.LF||
',"omit_when_null":"N"'||wwv_flow.LF||
',"is_qu';
wwv_flow_imp.g_varchar2_table(19) := 'ery_param":"N"'||wwv_flow.LF||
'}'||wwv_flow.LF||
',{'||wwv_flow.LF||
'"name":"Content-Type"'||wwv_flow.LF||
',"param_type":"HEADER"'||wwv_flow.LF||
',"data_type":"VARCHAR2"'||wwv_flow.LF||
',"is_requir';
wwv_flow_imp.g_varchar2_table(20) := 'ed":"N"'||wwv_flow.LF||
',"direction":"IN"'||wwv_flow.LF||
',"value":"application\/json"'||wwv_flow.LF||
',"is_static":"Y"'||wwv_flow.LF||
',"is_array":"N"'||wwv_flow.LF||
',"omit_when_';
wwv_flow_imp.g_varchar2_table(21) := 'null":"N"'||wwv_flow.LF||
',"is_query_param":"N"'||wwv_flow.LF||
'}'||wwv_flow.LF||
',{'||wwv_flow.LF||
'"name":"FEATURE_TYPE"'||wwv_flow.LF||
',"param_type":"BODY"'||wwv_flow.LF||
',"data_type":"VARCHA';
wwv_flow_imp.g_varchar2_table(22) := 'R2"'||wwv_flow.LF||
',"is_required":"N"'||wwv_flow.LF||
',"direction":"IN"'||wwv_flow.LF||
',"is_static":"N"'||wwv_flow.LF||
',"is_array":"N"'||wwv_flow.LF||
',"omit_when_null":"N"'||wwv_flow.LF||
',"is';
wwv_flow_imp.g_varchar2_table(23) := '_query_param":"N"'||wwv_flow.LF||
'}'||wwv_flow.LF||
',{'||wwv_flow.LF||
'"name":"FOLDER_PREFIX"'||wwv_flow.LF||
',"param_type":"BODY"'||wwv_flow.LF||
',"data_type":"VARCHAR2"'||wwv_flow.LF||
',"is_requ';
wwv_flow_imp.g_varchar2_table(24) := 'ired":"N"'||wwv_flow.LF||
',"direction":"IN"'||wwv_flow.LF||
',"is_static":"N"'||wwv_flow.LF||
',"is_array":"N"'||wwv_flow.LF||
',"omit_when_null":"N"'||wwv_flow.LF||
',"is_query_param"';
wwv_flow_imp.g_varchar2_table(25) := ':"N"'||wwv_flow.LF||
'}'||wwv_flow.LF||
',{'||wwv_flow.LF||
'"name":"IN_BUCKET_NAME"'||wwv_flow.LF||
',"param_type":"BODY"'||wwv_flow.LF||
',"data_type":"VARCHAR2"'||wwv_flow.LF||
',"is_required":"N"'||wwv_flow.LF||
',"';
wwv_flow_imp.g_varchar2_table(26) := 'direction":"IN"'||wwv_flow.LF||
',"is_static":"N"'||wwv_flow.LF||
',"is_array":"N"'||wwv_flow.LF||
',"omit_when_null":"N"'||wwv_flow.LF||
',"is_query_param":"N"'||wwv_flow.LF||
'}'||wwv_flow.LF||
',{'||wwv_flow.LF||
'"n';
wwv_flow_imp.g_varchar2_table(27) := 'ame":"NAMESPACE"'||wwv_flow.LF||
',"param_type":"BODY"'||wwv_flow.LF||
',"data_type":"VARCHAR2"'||wwv_flow.LF||
',"is_required":"N"'||wwv_flow.LF||
',"direction":"IN"'||wwv_flow.LF||
',';
wwv_flow_imp.g_varchar2_table(28) := '"is_static":"N"'||wwv_flow.LF||
',"is_array":"N"'||wwv_flow.LF||
',"omit_when_null":"N"'||wwv_flow.LF||
',"is_query_param":"N"'||wwv_flow.LF||
'}'||wwv_flow.LF||
',{'||wwv_flow.LF||
'"name":"OBJECT_NAME';
wwv_flow_imp.g_varchar2_table(29) := '"'||wwv_flow.LF||
',"param_type":"BODY"'||wwv_flow.LF||
',"data_type":"VARCHAR2"'||wwv_flow.LF||
',"is_required":"N"'||wwv_flow.LF||
',"direction":"IN"'||wwv_flow.LF||
',"is_static":"N"';
wwv_flow_imp.g_varchar2_table(30) := ''||wwv_flow.LF||
',"is_array":"N"'||wwv_flow.LF||
',"omit_when_null":"N"'||wwv_flow.LF||
',"is_query_param":"N"'||wwv_flow.LF||
'}'||wwv_flow.LF||
',{'||wwv_flow.LF||
'"name":"OUT_BUCKET_NAME"'||wwv_flow.LF||
',"param_t';
wwv_flow_imp.g_varchar2_table(31) := 'ype":"BODY"'||wwv_flow.LF||
',"data_type":"VARCHAR2"'||wwv_flow.LF||
',"is_required":"N"'||wwv_flow.LF||
',"direction":"IN"'||wwv_flow.LF||
',"is_static":"N"'||wwv_flow.LF||
',"is_array';
wwv_flow_imp.g_varchar2_table(32) := '":"N"'||wwv_flow.LF||
',"omit_when_null":"N"'||wwv_flow.LF||
',"is_query_param":"N"'||wwv_flow.LF||
'}'||wwv_flow.LF||
',{'||wwv_flow.LF||
'"name":"RESPONSE"'||wwv_flow.LF||
',"param_type":"BODY"'||wwv_flow.LF||
',"is_r';
wwv_flow_imp.g_varchar2_table(33) := 'equired":"N"'||wwv_flow.LF||
',"direction":"OUT"'||wwv_flow.LF||
',"is_static":"N"'||wwv_flow.LF||
',"is_array":"N"'||wwv_flow.LF||
',"omit_when_null":"N"'||wwv_flow.LF||
',"is_query_pa';
wwv_flow_imp.g_varchar2_table(34) := 'ram":"N"'||wwv_flow.LF||
'}'||wwv_flow.LF||
']'||wwv_flow.LF||
'}'||wwv_flow.LF||
',{'||wwv_flow.LF||
'"operation":"GET"'||wwv_flow.LF||
',"name":"GetProcessorJob"'||wwv_flow.LF||
',"database_operation":"FETCH_COLLECTIO';
wwv_flow_imp.g_varchar2_table(35) := 'N"'||wwv_flow.LF||
',"url_pattern":"."'||wwv_flow.LF||
',"allow_fetch_all_rows":"N"'||wwv_flow.LF||
',"parameters":['||wwv_flow.LF||
'{'||wwv_flow.LF||
'"name":"processorJobId"'||wwv_flow.LF||
',"param_';
wwv_flow_imp.g_varchar2_table(36) := 'type":"URL_PATTERN"'||wwv_flow.LF||
',"data_type":"VARCHAR2"'||wwv_flow.LF||
',"is_required":"Y"'||wwv_flow.LF||
',"direction":"IN"'||wwv_flow.LF||
',"value":"1"'||wwv_flow.LF||
',"is_s';
wwv_flow_imp.g_varchar2_table(37) := 'tatic":"N"'||wwv_flow.LF||
',"is_array":"N"'||wwv_flow.LF||
',"omit_when_null":"N"'||wwv_flow.LF||
',"is_query_param":"N"'||wwv_flow.LF||
'}'||wwv_flow.LF||
']'||wwv_flow.LF||
'}'||wwv_flow.LF||
']'||wwv_flow.LF||
',"parameters":['||wwv_flow.LF||
']'||wwv_flow.LF||
'}'||wwv_flow.LF||
'';
wwv_web_src_catalog_api.create_catalog_service(
 p_id=>wwv_flow_imp.id(7373573703390835)
,p_catalog_id=>wwv_flow_imp.id(33178613734671841)
,p_name=>'OCI Document Understanding'
,p_description=>wwv_flow_string.join(wwv_flow_t_varchar2(
'Analyze a Document using OCI Document Understanding CreateProcessJob API. ',
'',
'The Rest Data Source is configured to use Object Storage as the Input and Output Location and supports all analysis types using the standard models.',
'',
'Update the Base URL to the region hosting the service.'))
,p_base_url=>'https://document.aiservice.eu-frankfurt-1.oci.oraclecloud.com/'
,p_service_path=>'20221109/processorJobs'
,p_plugin_internal_name=>'NATIVE_OCI'
,p_authentication_type=>'OCI'
,p_details_json=>wwv_flow_imp.g_varchar2_table
,p_version=>'20231117'
);
end;
/
prompt --workspace/rest-source-catalogs/services//oci_document_understanding_key_extraction
begin
wwv_flow_imp.g_varchar2_table := wwv_flow_imp.empty_varchar2_table;
wwv_flow_imp.g_varchar2_table(1) := '{'||wwv_flow.LF||
'"data_profile":{'||wwv_flow.LF||
'"name":"OCI_Document_Understanding_Key_Extraction"'||wwv_flow.LF||
',"format":"JSON"'||wwv_flow.LF||
',"has_header_';
wwv_flow_imp.g_varchar2_table(2) := 'row":"N"'||wwv_flow.LF||
',"row_selector":"items"'||wwv_flow.LF||
',"is_single_row":"N"'||wwv_flow.LF||
',"columns":['||wwv_flow.LF||
'{'||wwv_flow.LF||
'"name":"COMPARTMENT_ID"'||wwv_flow.LF||
',"seque';
wwv_flow_imp.g_varchar2_table(3) := 'nce":1'||wwv_flow.LF||
',"is_primary_key":"N"'||wwv_flow.LF||
',"data_type":"VARCHAR2"'||wwv_flow.LF||
',"max_length":4000'||wwv_flow.LF||
',"has_time_zone":"N"'||wwv_flow.LF||
',"is_hi';
wwv_flow_imp.g_varchar2_table(4) := 'dden":"N"'||wwv_flow.LF||
',"is_filterable":"Y"'||wwv_flow.LF||
',"selector":"compartmentId"'||wwv_flow.LF||
'}'||wwv_flow.LF||
',{'||wwv_flow.LF||
'"name":"PROCESSOR_JOB_ID"'||wwv_flow.LF||
',"sequence';
wwv_flow_imp.g_varchar2_table(5) := '":2'||wwv_flow.LF||
',"is_primary_key":"Y"'||wwv_flow.LF||
',"data_type":"VARCHAR2"'||wwv_flow.LF||
',"max_length":2000'||wwv_flow.LF||
',"has_time_zone":"N"'||wwv_flow.LF||
',"is_hidde';
wwv_flow_imp.g_varchar2_table(6) := 'n":"N"'||wwv_flow.LF||
',"is_filterable":"Y"'||wwv_flow.LF||
',"selector":"processorJobId"'||wwv_flow.LF||
'}'||wwv_flow.LF||
']'||wwv_flow.LF||
'}'||wwv_flow.LF||
',"plugin_attributes":{'||wwv_flow.LF||
'}'||wwv_flow.LF||
',"operations';
wwv_flow_imp.g_varchar2_table(7) := '":['||wwv_flow.LF||
'{'||wwv_flow.LF||
'"operation":"GET"'||wwv_flow.LF||
',"name":"GetProcessorJob"'||wwv_flow.LF||
',"database_operation":"FETCH_COLLECTION"'||wwv_flow.LF||
',"url_pat';
wwv_flow_imp.g_varchar2_table(8) := 'tern":"."'||wwv_flow.LF||
',"allow_fetch_all_rows":"N"'||wwv_flow.LF||
',"parameters":['||wwv_flow.LF||
'{'||wwv_flow.LF||
'"name":"processorJobId"'||wwv_flow.LF||
',"param_type":"URL_P';
wwv_flow_imp.g_varchar2_table(9) := 'ATTERN"'||wwv_flow.LF||
',"data_type":"VARCHAR2"'||wwv_flow.LF||
',"is_required":"Y"'||wwv_flow.LF||
',"direction":"IN"'||wwv_flow.LF||
',"value":"1"'||wwv_flow.LF||
',"is_static":"N"'||wwv_flow.LF||
',';
wwv_flow_imp.g_varchar2_table(10) := '"is_array":"N"'||wwv_flow.LF||
',"omit_when_null":"N"'||wwv_flow.LF||
',"is_query_param":"N"'||wwv_flow.LF||
'}'||wwv_flow.LF||
']'||wwv_flow.LF||
'}'||wwv_flow.LF||
',{'||wwv_flow.LF||
'"operation":"POST"'||wwv_flow.LF||
',"name":"Crea';
wwv_flow_imp.g_varchar2_table(11) := 'teProcessorJobExtractKeyValFromToObjectStorage"'||wwv_flow.LF||
',"url_pattern":"."'||wwv_flow.LF||
',"request_body_template":"{\r\n  ';
wwv_flow_imp.g_varchar2_table(12) := '   \"processorConfig\": {\r\n     \"processorType\": \"GENERAL\",\r\n     \"features\": [\r\n     {\';
wwv_flow_imp.g_varchar2_table(13) := 'r\n        \"featureType\": \"#FEATURE_TYPE#\",\r\n        \"modelId\": \"#MODEL_ID#\"\r\n     }\r\n';
wwv_flow_imp.g_varchar2_table(14) := '    ]\r\n    },\r\n     \"inputLocation\": {\r\n     \"sourceType\": \"OBJECT_STORAGE_LOCATIONS\",\r';
wwv_flow_imp.g_varchar2_table(15) := '\n     \"objectLocations\": [{\r\n        \"bucketName\": \"#IN_BUCKET_NAME#\",\r\n        \"namespa';
wwv_flow_imp.g_varchar2_table(16) := 'ceName\": \"#NAMESPACE#\",\r\n        \"objectName\": \"#OBJECT_NAME#\"\r\n     }]\r\n   },\"outputL';
wwv_flow_imp.g_varchar2_table(17) := 'ocation\": {\r\n     \"bucketName\": \"#OUT_BUCKET_NAME#\",\r\n     \"namespaceName\": \"#NAMESPACE#';
wwv_flow_imp.g_varchar2_table(18) := '\",\r\n     \"prefix\": \"#FOLDER_PREFIX#\"\r\n   },\r\n     \"compartmentId\": \"#COMPARTMENT_ID#\"';
wwv_flow_imp.g_varchar2_table(19) := '\r\n}"'||wwv_flow.LF||
',"allow_fetch_all_rows":"N"'||wwv_flow.LF||
',"parameters":['||wwv_flow.LF||
'{'||wwv_flow.LF||
'"name":"Accept"'||wwv_flow.LF||
',"param_type":"HEADER"'||wwv_flow.LF||
',"data_t';
wwv_flow_imp.g_varchar2_table(20) := 'ype":"VARCHAR2"'||wwv_flow.LF||
',"is_required":"N"'||wwv_flow.LF||
',"direction":"IN"'||wwv_flow.LF||
',"value":"application\/json"'||wwv_flow.LF||
',"is_static":"Y"'||wwv_flow.LF||
',';
wwv_flow_imp.g_varchar2_table(21) := '"is_array":"N"'||wwv_flow.LF||
',"omit_when_null":"N"'||wwv_flow.LF||
',"is_query_param":"N"'||wwv_flow.LF||
'}'||wwv_flow.LF||
',{'||wwv_flow.LF||
'"name":"COMPARTMENT_ID"'||wwv_flow.LF||
',"param_type';
wwv_flow_imp.g_varchar2_table(22) := '":"BODY"'||wwv_flow.LF||
',"data_type":"VARCHAR2"'||wwv_flow.LF||
',"is_required":"N"'||wwv_flow.LF||
',"direction":"IN"'||wwv_flow.LF||
',"is_static":"N"'||wwv_flow.LF||
',"is_array":"';
wwv_flow_imp.g_varchar2_table(23) := 'N"'||wwv_flow.LF||
',"omit_when_null":"N"'||wwv_flow.LF||
',"is_query_param":"N"'||wwv_flow.LF||
'}'||wwv_flow.LF||
',{'||wwv_flow.LF||
'"name":"Content-Type"'||wwv_flow.LF||
',"param_type":"HEADER"'||wwv_flow.LF||
',"d';
wwv_flow_imp.g_varchar2_table(24) := 'ata_type":"VARCHAR2"'||wwv_flow.LF||
',"is_required":"N"'||wwv_flow.LF||
',"direction":"IN"'||wwv_flow.LF||
',"value":"application\/json"'||wwv_flow.LF||
',"is_static":';
wwv_flow_imp.g_varchar2_table(25) := '"Y"'||wwv_flow.LF||
',"is_array":"N"'||wwv_flow.LF||
',"omit_when_null":"N"'||wwv_flow.LF||
',"is_query_param":"N"'||wwv_flow.LF||
'}'||wwv_flow.LF||
',{'||wwv_flow.LF||
'"name":"FEATURE_TYPE"'||wwv_flow.LF||
',"param_t';
wwv_flow_imp.g_varchar2_table(26) := 'ype":"BODY"'||wwv_flow.LF||
',"data_type":"VARCHAR2"'||wwv_flow.LF||
',"is_required":"N"'||wwv_flow.LF||
',"direction":"IN"'||wwv_flow.LF||
',"is_static":"N"'||wwv_flow.LF||
',"is_array';
wwv_flow_imp.g_varchar2_table(27) := '":"N"'||wwv_flow.LF||
',"omit_when_null":"N"'||wwv_flow.LF||
',"is_query_param":"N"'||wwv_flow.LF||
'}'||wwv_flow.LF||
',{'||wwv_flow.LF||
'"name":"FOLDER_PREFIX"'||wwv_flow.LF||
',"param_type":"BODY"'||wwv_flow.LF||
',';
wwv_flow_imp.g_varchar2_table(28) := '"data_type":"VARCHAR2"'||wwv_flow.LF||
',"is_required":"N"'||wwv_flow.LF||
',"direction":"IN"'||wwv_flow.LF||
',"is_static":"N"'||wwv_flow.LF||
',"is_array":"N"'||wwv_flow.LF||
',"omit_';
wwv_flow_imp.g_varchar2_table(29) := 'when_null":"N"'||wwv_flow.LF||
',"is_query_param":"N"'||wwv_flow.LF||
'}'||wwv_flow.LF||
',{'||wwv_flow.LF||
'"name":"IN_BUCKET_NAME"'||wwv_flow.LF||
',"param_type":"BODY"'||wwv_flow.LF||
',"data_type":';
wwv_flow_imp.g_varchar2_table(30) := '"VARCHAR2"'||wwv_flow.LF||
',"is_required":"N"'||wwv_flow.LF||
',"direction":"IN"'||wwv_flow.LF||
',"is_static":"N"'||wwv_flow.LF||
',"is_array":"N"'||wwv_flow.LF||
',"omit_when_null":"';
wwv_flow_imp.g_varchar2_table(31) := 'N"'||wwv_flow.LF||
',"is_query_param":"N"'||wwv_flow.LF||
'}'||wwv_flow.LF||
',{'||wwv_flow.LF||
'"name":"MODEL_ID"'||wwv_flow.LF||
',"param_type":"BODY"'||wwv_flow.LF||
',"data_type":"VARCHAR2"'||wwv_flow.LF||
',"is_re';
wwv_flow_imp.g_varchar2_table(32) := 'quired":"N"'||wwv_flow.LF||
',"direction":"IN"'||wwv_flow.LF||
',"is_static":"N"'||wwv_flow.LF||
',"is_array":"N"'||wwv_flow.LF||
',"omit_when_null":"N"'||wwv_flow.LF||
',"is_query_para';
wwv_flow_imp.g_varchar2_table(33) := 'm":"N"'||wwv_flow.LF||
'}'||wwv_flow.LF||
',{'||wwv_flow.LF||
'"name":"NAMESPACE"'||wwv_flow.LF||
',"param_type":"BODY"'||wwv_flow.LF||
',"data_type":"VARCHAR2"'||wwv_flow.LF||
',"is_required":"N"'||wwv_flow.LF||
',"dir';
wwv_flow_imp.g_varchar2_table(34) := 'ection":"IN"'||wwv_flow.LF||
',"is_static":"N"'||wwv_flow.LF||
',"is_array":"N"'||wwv_flow.LF||
',"omit_when_null":"N"'||wwv_flow.LF||
',"is_query_param":"N"'||wwv_flow.LF||
'}'||wwv_flow.LF||
',{'||wwv_flow.LF||
'"name';
wwv_flow_imp.g_varchar2_table(35) := '":"OBJECT_NAME"'||wwv_flow.LF||
',"param_type":"BODY"'||wwv_flow.LF||
',"data_type":"VARCHAR2"'||wwv_flow.LF||
',"is_required":"N"'||wwv_flow.LF||
',"direction":"IN"'||wwv_flow.LF||
',"';
wwv_flow_imp.g_varchar2_table(36) := 'is_static":"N"'||wwv_flow.LF||
',"is_array":"N"'||wwv_flow.LF||
',"omit_when_null":"N"'||wwv_flow.LF||
',"is_query_param":"N"'||wwv_flow.LF||
'}'||wwv_flow.LF||
',{'||wwv_flow.LF||
'"name":"OUT_BUCKET_N';
wwv_flow_imp.g_varchar2_table(37) := 'AME"'||wwv_flow.LF||
',"param_type":"BODY"'||wwv_flow.LF||
',"data_type":"VARCHAR2"'||wwv_flow.LF||
',"is_required":"N"'||wwv_flow.LF||
',"direction":"IN"'||wwv_flow.LF||
',"is_static":';
wwv_flow_imp.g_varchar2_table(38) := '"N"'||wwv_flow.LF||
',"is_array":"N"'||wwv_flow.LF||
',"omit_when_null":"N"'||wwv_flow.LF||
',"is_query_param":"N"'||wwv_flow.LF||
'}'||wwv_flow.LF||
',{'||wwv_flow.LF||
'"name":"RESPONSE"'||wwv_flow.LF||
',"param_type"';
wwv_flow_imp.g_varchar2_table(39) := ':"BODY"'||wwv_flow.LF||
',"is_required":"N"'||wwv_flow.LF||
',"direction":"OUT"'||wwv_flow.LF||
',"is_static":"N"'||wwv_flow.LF||
',"is_array":"N"'||wwv_flow.LF||
',"omit_when_null":"N"';
wwv_flow_imp.g_varchar2_table(40) := ''||wwv_flow.LF||
',"is_query_param":"N"'||wwv_flow.LF||
'}'||wwv_flow.LF||
']'||wwv_flow.LF||
'}'||wwv_flow.LF||
']'||wwv_flow.LF||
',"parameters":['||wwv_flow.LF||
']'||wwv_flow.LF||
'}'||wwv_flow.LF||
'';
wwv_web_src_catalog_api.create_catalog_service(
 p_id=>wwv_flow_imp.id(7372911482383983)
,p_catalog_id=>wwv_flow_imp.id(33178613734671841)
,p_name=>'OCI Document Understanding Key Extraction'
,p_description=>wwv_flow_string.join(wwv_flow_t_varchar2(
'Analyze a Document using OCI Document Understanding CreateProcessJob API to Extract Key Value pairs. ',
'',
'The Rest Data Source is configured to use Object Storage as the Input and Output Location and supports all analysis types using a custom model.',
'',
'Update the Base URL to the region hosting the service.'))
,p_base_url=>'https://document.aiservice.eu-frankfurt-1.oci.oraclecloud.com/'
,p_service_path=>'20221109/processorJobs'
,p_plugin_internal_name=>'NATIVE_OCI'
,p_authentication_type=>'OCI'
,p_details_json=>wwv_flow_imp.g_varchar2_table
,p_version=>'20231117'
);
end;
/
begin
wwv_flow_imp.import_end(p_auto_install_sup_obj => nvl(wwv_flow_application_install.get_auto_install_sup_obj, false));
commit;
end;
/
set verify on feedback on define on
prompt  ...done
