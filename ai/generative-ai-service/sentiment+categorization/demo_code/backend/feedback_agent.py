import json
import logging
from typing import List

from langchain_community.chat_models.oci_generative_ai import ChatOCIGenAI
from langchain_community.embeddings import OCIGenAIEmbeddings
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.pydantic_v1 import BaseModel
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

import backend.message_handler as handler
import backend.utils.llm_config as llm_config

# Set up logging
logging.getLogger("oci").setLevel(logging.DEBUG)
messages_path = "ai/generative-ai-service/sentiment+categorization/demo_code/backend/data/complaints_messages.csv"


class AgentState(BaseModel):
    messages_info: List = []
    categories: List = []
    reports: List = []


class FeedbackAgent:
    def __init__(self, model_name: str = "cohere_oci"):
        self.model_name = model_name
        self.model = self.initialize_model()
        self.memory = MemorySaver()
        self.builder = self.setup_graph()
        self.messages = self.read_messages()

    def initialize_model(self):
        if self.model_name not in llm_config.MODEL_REGISTRY:
            raise ValueError(f"Unknown model: {self.model_name}")

        model_config = llm_config.MODEL_REGISTRY[self.model_name]

        return ChatOCIGenAI(
            model_id=model_config["model_id"],
            service_endpoint=model_config["service_endpoint"],
            compartment_id=model_config["compartment_id"],
            provider=model_config["provider"],
            auth_type=model_config["auth_type"],
            auth_profile=model_config["auth_profile"],
            model_kwargs=model_config["model_kwargs"],
        )

    def initialize_embeddings(self):
        if self.model_name not in llm_config.MODEL_REGISTRY:
            raise ValueError(f"Unknown model: {self.model_name}")

        model_config = llm_config.MODEL_REGISTRY[self.model_name]

        embeddings = OCIGenAIEmbeddings(
            model_id=model_config["embedding_model"],
            service_endpoint=model_config["service_endpoint"],
            truncate="NONE",
            compartment_id=model_config["compartment_id"],
            auth_type=model_config["auth_type"],
            auth_profile=model_config["auth_profile"],
        )
        return embeddings

    def read_messages(self):
        messages = handler.read_messages(filepath=messages_path)
        return handler.batchify(messages, 30)

    def summarization_node(self, state: AgentState):
        batch = self.messages
        response = self.model.invoke(
            [
                SystemMessage(
                    content=llm_config.get_prompt(self.model_name, "SUMMARIZATION")
                ),
                HumanMessage(content=f"Message batch: {batch}"),
            ]
        )
        state.messages_info = state.messages_info + [json.loads(response.content)]
        return {"messages_info": state.messages_info}

    def categorization_node(self, state: AgentState):
        batch = state.messages_info
        response = self.model.invoke(
            [
                SystemMessage(
                    content=llm_config.get_prompt(
                        self.model_name, "CATEGORIZATION_SYSTEM"
                    )
                ),
                HumanMessage(
                    content=llm_config.get_prompt(
                        self.model_name, "CATEGORIZATION_USER"
                    ).format(MESSAGE_BATCH=batch)
                ),
            ]
        )
        content = [json.loads(response.content)]
        state.categories = state.categories + handler.match_categories(batch, content)
        return {"categories": state.categories}

    def generate_report_node(self, state: AgentState):
        response = self.model.invoke(
            [
                SystemMessage(
                    content=llm_config.get_prompt(self.model_name, "REPORT_GEN")
                ),
                HumanMessage(content=f"Message info: {state.categories}"),
            ]
        )
        state.reports = response.content
        return {"reports": [response.content]}

    def setup_graph(self):
        builder = StateGraph(AgentState)
        builder.add_node("summarize", self.summarization_node)
        builder.add_node("categorize", self.categorization_node)
        builder.add_node("generate_report", self.generate_report_node)

        builder.set_entry_point("summarize")
        builder.add_edge("summarize", "categorize")
        builder.add_edge("categorize", "generate_report")

        builder.add_edge("generate_report", END)
        return builder.compile(checkpointer=self.memory)

    def get_graph(self):
        return self.builder.get_graph()

    def run(self):
        thread = {"configurable": {"thread_id": "1"}}
        for s in self.builder.stream(
            config=thread,
        ):
            print(f"\n \n{s}")

    def run_step_by_step(self):
        thread = {"configurable": {"thread_id": "1"}}
        initial_state = {
            "messages_info": [],
            "categories": [],
            "reports": [],
        }
        for state in self.builder.stream(initial_state, thread):
            yield state  # Yield each intermediate step to allow step-by-step execution
