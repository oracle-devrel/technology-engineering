import json
import logging
from typing import Annotated, List, Optional
from pydantic import BaseModel, ValidationError, Field, conint

from langchain_community.chat_models.oci_generative_ai import ChatOCIGenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from backend.utils import config
from backend.utils import prompts as prompts

logging.getLogger("oci").setLevel(logging.INFO)
logger = logging.getLogger(__name__)

class SummaryItem(BaseModel):
    id: str
    topic: str
    summary: str
    sentiment_score: Annotated[int, Field(ge=1, le=10)]

class CategoryItem(BaseModel):
    id: str
    primary_category: str
    secondary_category: str
    tertiary_category: str

class AgentState(BaseModel):
    messages_info: List[SummaryItem] = Field(default_factory=list)
    categories: List[CategoryItem] = Field(default_factory=list)
    reports: List[str] = Field(default_factory=list)

class FeedbackAgent:
    def __init__(self, data_list, thread_id: Optional[str] = None):
        self.model = self.initialize_model()
        self.memory = MemorySaver()
        self.builder = self.setup_graph()
        self.messages = data_list
        self.thread_id = thread_id or "session"  # avoid global '1'

    def initialize_model(self):
        return ChatOCIGenAI(
            model_id=config.GENERATE_MODEL_COHERE,
            service_endpoint=config.ENDPOINT,
            compartment_id=config.COMPARTMENT_ID,
            provider=config.PROVIDER_COHERE,
            auth_type=config.AUTH_TYPE,
            auth_profile=config.CONFIG_PROFILE,
            model_kwargs={"temperature": 0, "max_tokens": 4000},
        )

    def _parse_json_array(self, content: str, item_model):
        try:
            raw = json.loads(content)
            if not isinstance(raw, list):
                raise ValueError("Expected a JSON array.")
            items = [item_model(**elem) for elem in raw]
            return items
        except (json.JSONDecodeError, ValidationError, ValueError) as e:
            logger.error(f"Failed to parse/validate model output: {e}")
            raise

    def summarization_node(self, state: AgentState):
        response = self.model.invoke(
            [
                SystemMessage(content=prompts.SUMMARIZATION),
                HumanMessage(content=f"Messages: {self.messages}"),
            ]
        )
        items = self._parse_json_array(response.content, SummaryItem)
        state.messages_info = items
        return {"messages_info": state.messages_info}

    def categorization_node(self, state: AgentState):
        response = self.model.invoke(
            [
                SystemMessage(content=prompts.CATEGORIZATION_SYSTEM),
                HumanMessage(content=prompts.CATEGORIZATION_USER.format(MESSAGE_BATCH=[item.model_dump() for item in state.messages_info])),
            ]
        )
        state.categories = self._parse_json_array(response.content, CategoryItem)
        return {"categories": state.categories}

    def generate_report_node(self, state: AgentState):
        payload = {
            "categorized_messages": [c.model_dump() for c in state.categories],
            "summaries": [s.model_dump() for s in state.messages_info],
        }
        response = self.model.invoke(
            [
                SystemMessage(content=prompts.REPORT_GEN),
                HumanMessage(content=json.dumps(payload)),
            ]
        )
        state.reports = [response.content]
        return {"reports": state.reports}

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
        thread = {"configurable": {"thread_id": self.thread_id}}
        for s in self.builder.stream(config=thread):
            print(f"\\n\\n{s}")

    def run_step_by_step(self):
        thread = {"configurable": {"thread_id": self.thread_id}}
        initial_state = {"messages_info": [], "categories": [], "reports": []}
        for state in self.builder.stream(initial_state, thread):
            yield state