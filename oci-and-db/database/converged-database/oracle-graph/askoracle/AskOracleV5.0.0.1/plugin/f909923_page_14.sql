--------------------------------------------------------------------------------
-- Copyright © 2025, Oracle and/or its affiliates. All rights reserved.
--------------------------------------------------------------------------------
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
 p_version_yyyy_mm_dd=>'2026.03.30'
,p_release=>'26.1.4'
,p_default_workspace_id=>7701153768570624
,p_default_application_id=>909923
,p_default_id_offset=>59956130743206924
,p_default_owner=>'MARYAMSAJJADIAN'
);
end;
/
 
prompt APPLICATION 909923 - Ask Oracle Select AI
--
-- Application Export:
--   Application:     909923
--   Name:            Ask Oracle Select AI
--   Exported By:     MARYAMSAJJADIAN
--   Flashback:       0
--   Export Type:     Page Export
--   Manifest
--     PAGE: 14
--   Manifest End
--   Version:         26.1.4
--   Instance ID:     7700914145086164
--

begin
null;
end;
/
prompt --application/pages/delete_00014
begin
wwv_flow_imp_page.remove_page (p_flow_id=>wwv_flow.g_flow_id, p_page_id=>14);
end;
/
prompt --application/pages/page_00014
begin
wwv_flow_imp_page.create_page(
 p_id=>14
,p_name=>'Graph'
,p_alias=>'GRAPH'
,p_step_title=>'Graph'
,p_autocomplete_on_off=>'OFF'
,p_javascript_code_onload=>wwv_flow_string.join(wwv_flow_t_varchar2(
'(function () {',
'  "use strict";',
'',
'  function getGraphSvg() {',
'    return document.querySelector("#graphContent svg");',
'  }',
'',
'  function prepareSvg() {',
'    const source = getGraphSvg();',
'',
'    if (!source) {',
'      apex.message.alert("The graph is not ready yet.");',
'      return null;',
'    }',
'',
'    const clone = source.cloneNode(true);',
'    const box = source.getBoundingClientRect();',
'    const width = Math.max(1, Math.round(box.width));',
'    const height = Math.max(1, Math.round(box.height));',
'',
'    clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");',
'    clone.setAttribute("width", width);',
'    clone.setAttribute("height", height);',
'',
'    if (!clone.getAttribute("viewBox")) {',
'      clone.setAttribute("viewBox", `0 0 ${width} ${height}`);',
'    }',
'',
'    const sourceElements = [source, ...source.querySelectorAll("*")];',
'    const cloneElements = [clone, ...clone.querySelectorAll("*")];',
'',
'    const properties = [',
'      "fill",',
'      "fill-opacity",',
'      "stroke",',
'      "stroke-width",',
'      "stroke-opacity",',
'      "opacity",',
'      "font-family",',
'      "font-size",',
'      "font-weight",',
'      "font-style",',
'      "text-anchor",',
'      "dominant-baseline",',
'      "visibility",',
'      "display",',
'      "marker-start",',
'      "marker-mid",',
'      "marker-end"',
'    ];',
'',
'    sourceElements.forEach(function (element, index) {',
'      const target = cloneElements[index];',
'      if (!target) return;',
'',
'      const computed = window.getComputedStyle(element);',
'',
'      properties.forEach(function (property) {',
'        const value = computed.getPropertyValue(property);',
'        if (value) target.style.setProperty(property, value);',
'      });',
'    });',
'',
'    return {',
'      svg: clone,',
'      width: width,',
'      height: height',
'    };',
'  }',
'',
'  function downloadBlob(blob, filename) {',
'    const url = URL.createObjectURL(blob);',
'    const link = document.createElement("a");',
'',
'    link.href = url;',
'    link.download = filename;',
'    document.body.appendChild(link);',
'    link.click();',
'    link.remove();',
'',
'    window.setTimeout(function () {',
'      URL.revokeObjectURL(url);',
'    }, 1000);',
'  }',
'',
'  function exportGraphSvg() {',
'    const prepared = prepareSvg();',
'    if (!prepared) return;',
'',
'    const content =',
'      ''<?xml version="1.0" encoding="UTF-8"?>\n'' +',
'      new XMLSerializer().serializeToString(prepared.svg);',
'',
'    downloadBlob(',
'      new Blob([content], {',
'        type: "image/svg+xml;charset=utf-8"',
'      }),',
'      "oracle-property-graph.svg"',
'    );',
'  }',
'',
'  function exportGraphPng() {',
'    const prepared = prepareSvg();',
'    if (!prepared) return;',
'',
'    const content = new XMLSerializer().serializeToString(prepared.svg);',
'    const svgBlob = new Blob([content], {',
'      type: "image/svg+xml;charset=utf-8"',
'    });',
'    const url = URL.createObjectURL(svgBlob);',
'    const image = new Image();',
'',
'    image.onload = function () {',
'      const scale = 2;',
'      const canvas = document.createElement("canvas");',
'',
'      canvas.width = prepared.width * scale;',
'      canvas.height = prepared.height * scale;',
'',
'      const context = canvas.getContext("2d");',
'      context.scale(scale, scale);',
'      context.fillStyle = "#ffffff";',
'      context.fillRect(0, 0, prepared.width, prepared.height);',
'      context.drawImage(',
'        image,',
'        0,',
'        0,',
'        prepared.width,',
'        prepared.height',
'      );',
'',
'      URL.revokeObjectURL(url);',
'',
'      canvas.toBlob(function (blob) {',
'        if (blob) {',
'          downloadBlob(blob, "oracle-property-graph.png");',
'        }',
'      }, "image/png");',
'    };',
'',
'    image.onerror = function () {',
'      URL.revokeObjectURL(url);',
'      apex.message.alert("Could not create the PNG.");',
'    };',
'',
'    image.src = url;',
'  }',
'',
'  function addExportButtons() {',
'  if (document.getElementById("graph-export-toolbar")) {',
'    return true;',
'  }',
'',
'  const graphContent = document.getElementById("graphContent");',
'  const statusRow = document.querySelector(',
'    ''footer [data-testid="datafetcher"]''',
'  );',
'',
'  if (!graphContent || !statusRow) {',
'    return false;',
'  }',
'',
'  const host = graphContent.parentNode;',
'  host.style.position = "relative";',
'',
'  const toolbar = document.createElement("div");',
'  toolbar.id = "graph-export-toolbar";',
'  toolbar.style.position = "absolute";',
'toolbar.style.right = "200px";',
'toolbar.style.bottom = "8px";',
'  toolbar.style.display = "flex";',
'  toolbar.style.alignItems = "center";',
'  toolbar.style.gap = "6px";',
'  toolbar.style.zIndex = "20";',
'',
'  const svgButton = document.createElement("button");',
'  svgButton.type = "button";',
'  svgButton.className = "t-Button t-Button--small";',
'  svgButton.textContent = "SVG";',
'  svgButton.addEventListener("click", exportGraphSvg);',
'',
'  const pngButton = document.createElement("button");',
'  pngButton.type = "button";',
'  pngButton.className = "t-Button t-Button--small";',
'  pngButton.textContent = "PNG";',
'  pngButton.addEventListener("click", exportGraphPng);',
'',
'  toolbar.appendChild(svgButton);',
'  toolbar.appendChild(pngButton);',
'  host.appendChild(toolbar);',
'',
'',
'  return true;',
'}',
'',
'  if (!addExportButtons()) {',
'    const observer = new MutationObserver(function () {',
'      if (addExportButtons()) observer.disconnect();',
'    });',
'',
'    observer.observe(document.body, {',
'      childList: true,',
'      subtree: true',
'    });',
'  }',
'',
'  window.askOraclePrepareGraphSvg = prepareSvg;',
'})();'))
,p_inline_css=>wwv_flow_string.join(wwv_flow_t_varchar2(
'/* ask-oracle-embedded-graph-page */',
'.t-Header,',
'.t-Body-nav,',
'.t-Body-actions,',
'.t-Footer,',
'.t-BreadcrumbRegion,',
'.t-Body-title {',
'  display: none !important;',
'}',
'',
'.t-Body-main {',
'  margin: 0 !important;',
'}',
'',
'.t-Body-content {',
'  margin: 0 !important;',
'  padding: 0 !important;',
'}',
'',
'',
'.llm-conv-show-graph-btn {',
'  box-sizing: border-box !important;',
'  width: auto !important;',
'  min-width: 0 !important;',
'  height: 24px !important;',
'  min-height: 24px !important;',
'  padding: 2px 6px !important;',
'  font-size: 10px !important;',
'  line-height: 1.1 !important;',
'}'))
,p_step_template=>wwv_flow_imp.id(648594757704526590)
,p_page_template_options=>'#DEFAULT#'
,p_protection_level=>'C'
,p_page_component_map=>'17'
);
wwv_flow_imp_page.create_page_plug(
 p_id=>wwv_flow_imp.id(118569625235142363)
,p_plug_name=>'Breadcrumb'
,p_static_id=>'breadcrumb'
,p_region_template_options=>'#DEFAULT#:t-BreadcrumbRegion--useBreadcrumbTitle'
,p_component_template_options=>'#DEFAULT#'
,p_escape_on_http_output=>'N'
,p_plug_template=>wwv_flow_imp.id(648798169719526763)
,p_plug_display_sequence=>10
,p_plug_display_point=>'REGION_POSITION_01'
,p_plug_item_display_point=>'ABOVE'
,p_menu_id=>wwv_flow_imp.id(50581573347173374050)
,p_plug_source_type=>'NATIVE_BREADCRUMB'
,p_menu_template_id=>wwv_flow_imp.id(648959233643526905)
,p_plug_query_headings_type=>'COLON_DELMITED_LIST'
);
wwv_flow_imp_page.create_page_plug(
 p_id=>wwv_flow_imp.id(118359069250009738)
,p_plug_name=>'Graph View'
,p_static_id=>'graph-view'
,p_region_name=>'graph'
,p_region_template_options=>'#DEFAULT#:t-Region--scrollBody'
,p_plug_template=>wwv_flow_imp.id(648766490610526737)
,p_plug_display_sequence=>40
,p_plug_item_display_point=>'ABOVE'
,p_query_type=>'FUNC_BODY_RETURNING_SQL'
,p_function_body_language=>'PLSQL'
,p_plug_source=>wwv_flow_string.join(wwv_flow_t_varchar2(
'RETURN ask_oracle_graph_sql(:P14_PROMPT_ID);',
''))
,p_plug_source_type=>'PLUGIN_GRAPHVIZ'
,p_attributes=>wwv_flow_t_plugin_attributes(wwv_flow_t_varchar2(
  'attribute_05', 'N',
  'attribute_06', '100',
  'attribute_10', 'modes:exploration',
  'attribute_14', 'Y',
  'attribute_16', '400',
  'bind_variable_pgql', 'N',
  'custom_theme', 'N',
  'darktheme', 'N',
  'default_legend_enabled', 'Y',
  'defaults_for_modes', 'fitToScreenActive:stickyActive:evolutionActive',
  'enable_evolution', 'N',
  'enable_expand', 'N',
  'escapehtml', 'N',
  'exploration_options', 'expand:focus:group:ungroup:drop:undo:redo:reset',
  'legend_state', 'expanded',
  'livesearch', 'N',
  'modes_options', 'interaction:fitToScreen:sticky:evolution',
  'schema_visualization', 'N',
  'showtitle', 'Y',
  'visibility_toggle_mode', 'hideWhenAnyUnchecked')).to_clob
);
wwv_flow_imp_page.create_region_column(
 p_id=>wwv_flow_imp.id(118359311568009740)
,p_name=>'E_ID'
,p_data_type=>'CLOB'
,p_is_visible=>true
,p_display_sequence=>20
,p_use_as_row_header=>false
,p_include_in_export=>true
,p_escape_on_http_output=>true
);
wwv_flow_imp_page.create_region_column(
 p_id=>wwv_flow_imp.id(118359411122009741)
,p_name=>'P_ID'
,p_data_type=>'CLOB'
,p_is_visible=>true
,p_display_sequence=>30
,p_use_as_row_header=>false
,p_include_in_export=>true
,p_escape_on_http_output=>true
);
wwv_flow_imp_page.create_region_column(
 p_id=>wwv_flow_imp.id(118359165425009739)
,p_name=>'V_ID'
,p_data_type=>'CLOB'
,p_is_visible=>true
,p_display_sequence=>10
,p_use_as_row_header=>false
,p_include_in_export=>true
,p_escape_on_http_output=>true
);
wwv_flow_imp_page.create_page_item(
 p_id=>wwv_flow_imp.id(59963747031668901)
,p_name=>'P14_GRAPH_LAYOUT'
,p_item_sequence=>30
,p_item_default=>'force'
,p_prompt=>'Graph Layout'
,p_source_type=>'ALWAYS_NULL'
,p_display_as=>'NATIVE_SELECT_LIST'
,p_lov=>'STATIC:Force;force,Radial;radial,Hierarchical;hierarchical,Concentric;concentric,Circle;circle,Grid;grid,Random;random'
,p_lov_display_null=>'YES'
,p_cHeight=>1
,p_field_template=>wwv_flow_imp.id(648947062524526892)
,p_item_template_options=>'#DEFAULT#'
,p_lov_display_extra=>'YES'
,p_attributes=>wwv_flow_t_plugin_attributes(wwv_flow_t_varchar2(
  'page_action_on_selection', 'NONE')).to_clob
);
wwv_flow_imp_page.create_page_item(
 p_id=>wwv_flow_imp.id(118359003072009737)
,p_name=>'P14_PROMPT_ID'
,p_item_sequence=>20
,p_source_type=>'ALWAYS_NULL'
,p_display_as=>'NATIVE_HIDDEN'
,p_attributes=>wwv_flow_t_plugin_attributes(wwv_flow_t_varchar2(
  'value_protected', 'Y')).to_clob
);
wwv_flow_imp_page.create_page_da_event(
 p_id=>wwv_flow_imp.id(59963848115668902)
,p_name=>'New'
,p_static_id=>'new'
,p_event_sequence=>10
,p_triggering_element_type=>'ITEM'
,p_triggering_element=>'P14_GRAPH_LAYOUT'
,p_bind_type=>'bind'
,p_execution_type=>'IMMEDIATE'
,p_bind_event_type=>'change'
);
wwv_flow_imp_page.create_page_da_action(
 p_id=>wwv_flow_imp.id(59963997511668903)
,p_event_id=>wwv_flow_imp.id(59963848115668902)
,p_event_result=>'TRUE'
,p_action_sequence=>10
,p_execute_on_page_init=>'Y'
,p_static_id=>'native-javascript-code'
,p_action=>'NATIVE_JAVASCRIPT_CODE'
,p_attributes=>wwv_flow_t_plugin_attributes(wwv_flow_t_varchar2(
  'js_code', wwv_flow_string.join(wwv_flow_t_varchar2(
    'const region = apex.region("graph");',
    '',
    'if (region && region.self) {',
    '  const { self } = region;',
    '  self.settings = {',
    '    ...self.settings,',
    '    layout: $v("P14_GRAPH_LAYOUT")',
    '  };',
    '}')))).to_clob
);
end;
/
prompt --application/end_environment
begin
wwv_flow_imp.import_end(p_auto_install_sup_obj => nvl(wwv_flow_application_install.get_auto_install_sup_obj, false)
);
commit;
end;
/
set verify on feedback on define on
prompt  ...done
