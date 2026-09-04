# --- GenAI Agent + Knowledge Base + RAG Tool ---
# Everything needed for document search — fully self-contained.

# -- Knowledge Base (Object Storage backed, hybrid search) --

resource "oci_generative_ai_agent_knowledge_base" "kb" {
  compartment_id = var.compartment_ocid
  display_name   = "${var.prefix}-kb"
  description    = "Knowledge base for document search"
  index_config {
    index_config_type           = "DEFAULT_INDEX_CONFIG"
    should_enable_hybrid_search = true
  }
  freeform_tags = local.freeform_tags
}

# -- Data Source (points KB at the documents bucket) --

resource "oci_generative_ai_agent_data_source" "kb_datasource" {
  compartment_id    = var.compartment_ocid
  knowledge_base_id = oci_generative_ai_agent_knowledge_base.kb.id
  display_name      = "${var.prefix}-datasource"
  description       = "Object Storage data source for document ingestion"
  data_source_config {
    data_source_config_type = "OCI_OBJECT_STORAGE"
    object_storage_prefixes {
      bucket    = oci_objectstorage_bucket.documents_bucket.name
      namespace = local.object_storage_namespace
    }
  }
  freeform_tags = local.freeform_tags
}

# -- Initial Ingestion Job (runs once at deploy time) --

resource "oci_generative_ai_agent_data_ingestion_job" "initial_ingestion" {
  compartment_id = var.compartment_ocid
  data_source_id = oci_generative_ai_agent_data_source.kb_datasource.id
  display_name   = "${var.prefix}-initial-ingestion"
  description    = "Initial document ingestion at deploy time"
  freeform_tags  = local.freeform_tags
}

# -- Agent --

resource "oci_generative_ai_agent_agent" "agent" {
  compartment_id  = var.compartment_ocid
  display_name    = "${var.prefix}-agent"
  description     = "GenAI Agent for document search and report generation"
  welcome_message = "How can I help you?"
  freeform_tags   = local.freeform_tags
}

# -- RAG Tool (connects KB to Agent) --

resource "oci_generative_ai_agent_tool" "rag_tool" {
  agent_id       = oci_generative_ai_agent_agent.agent.id
  compartment_id = var.compartment_ocid
  display_name   = "rag-tool"
  description    = "Search uploaded documents for report data"
  tool_config {
    tool_config_type = "RAG_TOOL_CONFIG"
    knowledge_base_configs {
      knowledge_base_id = oci_generative_ai_agent_knowledge_base.kb.id
    }
  }
  freeform_tags = local.freeform_tags
}

# -- Agent Endpoint --

resource "oci_generative_ai_agent_agent_endpoint" "endpoint" {
  compartment_id         = var.compartment_ocid
  agent_id               = oci_generative_ai_agent_agent.agent.id
  display_name           = "${var.prefix}-endpoint"
  description            = "Agent endpoint for KB search"
  should_enable_citation = true
  should_enable_session  = true
  should_enable_trace    = true
  content_moderation_config {
    should_enable_on_input  = false
    should_enable_on_output = false
  }
  session_config {
    idle_timeout_in_seconds = 3600
  }
  freeform_tags = local.freeform_tags
}
