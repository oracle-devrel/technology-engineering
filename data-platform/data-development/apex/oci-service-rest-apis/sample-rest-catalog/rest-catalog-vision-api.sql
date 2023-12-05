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
prompt --workspace/rest-source-catalogs//oci_vision
begin
wwv_web_src_catalog_api.create_catalog(
 p_id=>wwv_flow_imp.id(34885047319213275)
,p_name=>'OCI Vision'
,p_internal_name=>'OCI VISION'
,p_description=>'A collection of APIs to the OCI Vision AI service'
,p_format=>'APEX'
);
end;
/
prompt --workspace/rest-source-catalogs/services//oci_vision_analyze_image
begin
wwv_flow_imp.g_varchar2_table := wwv_flow_imp.empty_varchar2_table;
wwv_flow_imp.g_varchar2_table(1) := '{'||wwv_flow.LF||
'"data_profile":{'||wwv_flow.LF||
'"name":"OCI Vision"'||wwv_flow.LF||
',"format":"JSON"'||wwv_flow.LF||
',"has_header_row":"N"'||wwv_flow.LF||
',"row_selector":"items';
wwv_flow_imp.g_varchar2_table(2) := '"'||wwv_flow.LF||
',"is_single_row":"N"'||wwv_flow.LF||
',"columns":['||wwv_flow.LF||
']'||wwv_flow.LF||
'}'||wwv_flow.LF||
',"plugin_attributes":{'||wwv_flow.LF||
'}'||wwv_flow.LF||
',"operations":['||wwv_flow.LF||
'{'||wwv_flow.LF||
'"operation":"POST';
wwv_flow_imp.g_varchar2_table(3) := '"'||wwv_flow.LF||
',"name":"AnalyzeImage"'||wwv_flow.LF||
',"url_pattern":"."'||wwv_flow.LF||
',"request_body_template":"{\r\n     \"compartmentId\": \';
wwv_flow_imp.g_varchar2_table(4) := '"#COMPARTMENT_ID#\",\r\n     \"image\": {\r\n     \"source\": \"INLINE\",\r\n     \"data\": \"#FILE_';
wwv_flow_imp.g_varchar2_table(5) := 'DATA#\"\r\n   },\r\n  \"features\": [\r\n  {\r\n        \"featureType\": \"#FEATURE_TYPE#\",\r\n    ';
wwv_flow_imp.g_varchar2_table(6) := '    \"maxResults\": 5\r\n     }\r\n    ]\r\n  }"'||wwv_flow.LF||
',"allow_fetch_all_rows":"N"'||wwv_flow.LF||
',"parameters":['||wwv_flow.LF||
'{'||wwv_flow.LF||
'"name';
wwv_flow_imp.g_varchar2_table(7) := '":"COMPARTMENT_ID"'||wwv_flow.LF||
',"param_type":"BODY"'||wwv_flow.LF||
',"data_type":"VARCHAR2"'||wwv_flow.LF||
',"is_required":"N"'||wwv_flow.LF||
',"direction":"IN"';
wwv_flow_imp.g_varchar2_table(8) := ''||wwv_flow.LF||
',"is_static":"N"'||wwv_flow.LF||
',"is_array":"N"'||wwv_flow.LF||
',"omit_when_null":"N"'||wwv_flow.LF||
',"is_query_param":"N"'||wwv_flow.LF||
'}'||wwv_flow.LF||
',{'||wwv_flow.LF||
'"name":"Content-T';
wwv_flow_imp.g_varchar2_table(9) := 'ype"'||wwv_flow.LF||
',"param_type":"HEADER"'||wwv_flow.LF||
',"data_type":"VARCHAR2"'||wwv_flow.LF||
',"is_required":"N"'||wwv_flow.LF||
',"direction":"IN"'||wwv_flow.LF||
',"value":"a';
wwv_flow_imp.g_varchar2_table(10) := 'pplication\/json"'||wwv_flow.LF||
',"is_static":"Y"'||wwv_flow.LF||
',"is_array":"N"'||wwv_flow.LF||
',"omit_when_null":"N"'||wwv_flow.LF||
',"is_query_param":"N"'||wwv_flow.LF||
'}'||wwv_flow.LF||
',{'||wwv_flow.LF||
'';
wwv_flow_imp.g_varchar2_table(11) := '"name":"FEATURE_TYPE"'||wwv_flow.LF||
',"param_type":"BODY"'||wwv_flow.LF||
',"data_type":"VARCHAR2"'||wwv_flow.LF||
',"is_required":"N"'||wwv_flow.LF||
',"direction":"';
wwv_flow_imp.g_varchar2_table(12) := 'IN"'||wwv_flow.LF||
',"is_static":"N"'||wwv_flow.LF||
',"is_array":"N"'||wwv_flow.LF||
',"omit_when_null":"N"'||wwv_flow.LF||
',"is_query_param":"N"'||wwv_flow.LF||
'}'||wwv_flow.LF||
',{'||wwv_flow.LF||
'"name":"FILE_D';
wwv_flow_imp.g_varchar2_table(13) := 'ATA"'||wwv_flow.LF||
',"param_type":"BODY"'||wwv_flow.LF||
',"data_type":"VARCHAR2"'||wwv_flow.LF||
',"is_required":"N"'||wwv_flow.LF||
',"direction":"IN"'||wwv_flow.LF||
',"is_static":';
wwv_flow_imp.g_varchar2_table(14) := '"N"'||wwv_flow.LF||
',"is_array":"N"'||wwv_flow.LF||
',"omit_when_null":"N"'||wwv_flow.LF||
',"is_query_param":"N"'||wwv_flow.LF||
'}'||wwv_flow.LF||
',{'||wwv_flow.LF||
'"name":"RESPONSE"'||wwv_flow.LF||
',"param_type"';
wwv_flow_imp.g_varchar2_table(15) := ':"BODY"'||wwv_flow.LF||
',"is_required":"N"'||wwv_flow.LF||
',"direction":"OUT"'||wwv_flow.LF||
',"is_static":"N"'||wwv_flow.LF||
',"is_array":"N"'||wwv_flow.LF||
',"omit_when_null":"N"';
wwv_flow_imp.g_varchar2_table(16) := ''||wwv_flow.LF||
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
 p_id=>wwv_flow_imp.id(34885306125213277)
,p_catalog_id=>wwv_flow_imp.id(34885047319213275)
,p_name=>'OCI Vision Analyze Image'
,p_description=>wwv_flow_string.join(wwv_flow_t_varchar2(
'Use OCI Vision to upload images to detect and classify objects in them.',
'',
'The Rest Data Source is configured to analyse images inline, returning the analyis in the response.',
'',
'Update the Base URL to the region hosting the service.'))
,p_base_url=>'https://vision.aiservice.eu-frankfurt-1.oci.oraclecloud.com/20220125/actions/'
,p_service_path=>'analyzeImage'
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
