# Oracle Digital Assistant AI Agent with document groups
 
This template is an ODA-skill for using AI Agent with different document-groups.
This limits AI Agent to only use a specific group of documents when answering a prompt

Reviewed: 21.01.2026

# When to use this asset?
 
There are several scenario's with ODA how this can be used:
- Limit a skill to a certain subject
- Define document groups per intent/flow
- Define document groups based on users role
 
# How to use this asset?
 
  Import the mdAgent1 skill in ODA
  In the skill configuration you can define one or more document groups
  In the sample flow you can pass the document group in the API call
  In AI Agent you have to define document groups by:
    [adding meta-data when uploading docs](https://docs.oracle.com/en-us/iaas/Content/generative-ai-agents/RAG-tool-object-storage-guidelines.htm#add-metadata-header)
    set metaData type in _all.metadata.json in the root of your object storage bucket
	  (re)run ingestion job in Knowledge bases

# License

Copyright (c) 2026 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](../../LICENSE.txt) for more details.