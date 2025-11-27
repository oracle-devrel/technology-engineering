"""
CSV Analyzer Agent implemented with LangGraph
Author: Luigi Saetta & Omar Salem

Updates:
- 12/03: added integration with APM
"""

import pandas as pd
from langchain_core.messages import SystemMessage, HumanMessage
from langchain.prompts import PromptTemplate
from langgraph.graph import StateGraph, START, END
# from pyzipkin.zipkin import zipkin_span

import json
import fitz
import re

from context import get_variable_info
from oci_models import get_llm
from prompts import (
    CHECK_REQUEST_PROMPT_TEMPLATE,
    PROMPT_GENERATE_ANSWER,
    PROMPT_GENERATE_CODE,
    ROUTE_TEMPLATE,
)
from secure_code import analyze_code
from utils import get_console_logger, remove_triple_backtics, extract_json_from_string
from config import DEBUG

from typing import Dict, Optional, Any
from pydantic import BaseModel
from typing_extensions import TypedDict

logger = get_console_logger()

class ExtractedPDFData(BaseModel):
    """
    Dynamic model for storing extracted information from a PDF.
    - stores key-value pairs dynamically.
    - ensures values are JSON-serializable & hashable.
    """

    data: Dict[str, Any]  # Holds any extracted fields (e.g., {"customer": "ABC Corp", "items": [...]})

    def make_hashable(self):
        """
        Convert lists into tuples to ensure hashability.
        """
        for key, value in self.data.items():
            if isinstance(value, list):
                self.data[key] = tuple(value)  # convert lists → tuples

class State(TypedDict):
    """
    The state of the graph
    """
    # this will contain the df
    input_df: type
    chat_history: list = []
    # the current user request
    user_request: str
    extracted_information: Optional[ExtractedPDFData]  #  supports dynamic fields
    pdf_path: Optional[str] = None  # Track uploaded PDF
    # the route decide for user_request
    route: Optional[str] = None

    # only used for correction (next release)
    previous_error: Optional[str] = None
    # the route decide for user_request
    route: Optional[str] = None
    # output for single tools
    code_generated: str
    execution_output: type
    final_output: type
    error: Optional[str] = None


AGENT_NAME = "AI_DATA_ANALYZER"

class MultiAgent:
    """
    This class encapsulate the multi-agent
    """

    def __init__(self, user_settings=None):
        # for now not used, in the future, to add context for user (who is...)

        self.user_settings = user_settings

    # @zipkin_span(service_name=AGENT_NAME, span_name="decide_route")
    def decide_route(self, state: State):
        """
        Based on the request and provided data (csv or not) decide what is the route to go for
        """
        if state["input_df"] is None:
            df_info = None
        else:
            df_info = get_variable_info("df", state["input_df"])

        pdf_present = state.get("pdf_path") is not None

        if pdf_present and state.get("extracted_information") is None:
            return {"route": "process_pdf", "error": None}

        user_request = state["user_request"]

        _prompt_template = PromptTemplate(
            input_variables=["df_info", "user_request"],
            template=ROUTE_TEMPLATE,
        )

        _prompt = _prompt_template.format(
            df_info=df_info, user_request=user_request
        )

        _llm_response = self.call_llm(prompt=_prompt, temperature=0.0, max_tokens=1024)

        dict_result = extract_json_from_string(
            # alredy cleaned from triple backt...
            _llm_response
        )

        if DEBUG:
            logger.info("Output for routing: %s", dict_result)

        return {"route": dict_result["action"], "error": None}

    def conditional_routing0(self, state: State):
        """
        conditional node to check which route to follow
        """

        return state["route"]

    # @zipkin_span(service_name=AGENT_NAME, span_name="check_if_is_secure")
    def check_if_is_secure(self, state: State):
        """
        Check that the request is allowed

        Called before code generation.
        Apply a check to the request from the user, to avoid harmful code generation
        """
        user_request = state["user_request"]

        # first, a check based on keyword detection
        forbidden_keywords = {
            "delete",
            "drop",
            "update",
            "truncate",
            "exec",
            "system",
            "subprocess",
        }

        if any(word in user_request.lower() for word in forbidden_keywords):
            # block and exit
            return {"error": "Request contains forbidden operations."}

        llm = get_llm(temperature=0.0, max_tokens=1024)

        _prompt_template = PromptTemplate(
            input_variables=["user_request"], template=CHECK_REQUEST_PROMPT_TEMPLATE
        )

        _prompt = _prompt_template.format(user_request=user_request)

        messages = [HumanMessage(content=_prompt)]
        _response = llm.invoke(messages)

        dict_result = extract_json_from_string(
            remove_triple_backtics(_response.content)
        )

        if dict_result["result_check"] == "not_allowed":
            error = "Request not allowed."
            logger.info("Security risk detected!")
            logger.info(error)
            logger.info(dict_result["reason"])
        else:
            error = None

        # each function must return error = None if everything goes ok
        return {"error": error}

    def conditional_routing1(self, state: State):
        """
        conditional node to check if request is allowed
        """
        if state["error"] is not None:
            return "end"

        return "request_ok"

    # @zipkin_span(service_name=AGENT_NAME, span_name="generate_code")
    def generate_code(self, state: State):
        """
        Generate the code to be executed on the df, incorporating extracted PDF data if available.
        """

        llm = get_llm(temperature=0.0, max_tokens=2048)

        df_info = get_variable_info("df", state["input_df"])
        extracted_pdf = state.get("extracted_information")
        pdf_info = extracted_pdf.data if isinstance(extracted_pdf, ExtractedPDFData) else {}

        logger.info(f"📄 Extracted PDF Info Available in Code Generator: {pdf_info}")

        context_and_request = f"""
        Context: {df_info}\n
        Extracted Information: {pdf_info if pdf_info else "No PDF Data"}\n
        Chat history: {state["chat_history"]}\n
        Question: {state["user_request"]}
        """

        messages = [
            SystemMessage(content=PROMPT_GENERATE_CODE),
            HumanMessage(content=context_and_request),
        ]

        _response = llm.invoke(messages)
        _code = remove_triple_backtics(_response.content)

        logger.debug("📝 Generated Code:\n{_code}")

        return {"code_generated": _code, "error": None}

    # @zipkin_span(service_name=AGENT_NAME, span_name="analyze_code")
    def analyze_code(self, state: State):
        """
        Analyze the code to find security issues
        """
        sec_analysis_result = analyze_code(state["code_generated"])

        if "No security issues" in sec_analysis_result:
            logger.info("No security issues!")
            error = None
        else:
            error = "Security issues detected. No code execution !"
            logger.info(error)
            logger.info(sec_analysis_result)

        return {"error": error}

    def conditional_routing2(self, state: State):
        """
        conditional node to check if security issues
        """
        if state["error"] is not None:
            return "end"

        return "code_ok"

    # @zipkin_span(service_name=AGENT_NAME, span_name="exec_code")
    def exec_code(self, state: State):
        """
        Execute the generated code in a constrained environment.
        """
        import pandas as pd
        from tabulate import tabulate

        # ensure df is available
        df = state["input_df"].copy() if state["input_df"] is not None else None

        # extract PDF data if available
        extracted_pdf = state.get("extracted_information")
        extracted_information = extracted_pdf.data if isinstance(extracted_pdf, ExtractedPDFData) else {}

        try:
            # ensure execution context includes extracted PDF data only if needed
            context = {
                "df": df,
                "pd": pd,
                "tabulate": tabulate,
                "result": None,
            }

            # add extracted information ONLY if the generated code references it
            if "extracted_information" in state["code_generated"]:
                context["extracted_information"] = extracted_information
                logger.info("📄 Including extracted_information in execution context.")

            # execute the generated code
            exec(state["code_generated"], context)

            # retrieve execution result
            output = context.get("result", None)
            error = None

        except Exception as e:
            logger.error(f"Error in exec code: {e}")
            error = str(e)
            output = None  # Ensure output is always defined

        return {"execution_output": output, "error": error}

    # @zipkin_span(service_name=AGENT_NAME, span_name="generate_answer")
    def generate_answer(self, state: State):
        """
        Generate the final answer from execution results.
        """
        logger.info(f"📊 Execution Output Before Answer Generation: {state['execution_output']}")

        extracted_pdf = state.get("extracted_information")
        df_info = get_variable_info("df", state["input_df"])
        pdf_info = extracted_pdf.data if isinstance(extracted_pdf, ExtractedPDFData) else {}

        # Execution Output: {json.dumps(state["execution_output"], indent=2)}
        if not isinstance(state["execution_output"], pd.DataFrame):
            _human_prompt = f"""
            Context: {df_info}\n
            Results: {state['execution_output']}
            Extracted Information: {pdf_info if pdf_info else "No PDF Data"}\n
            Question: {state['user_request']}
            """

            final_output = self.call_llm(
                prompt=_human_prompt,
                system_prompt=PROMPT_GENERATE_ANSWER,
                temperature=0.1,
                max_tokens=2048,
            )
        else:
            final_output = state["execution_output"]

        return {"final_output": final_output, "error": None}

    def extract_pdf_text(self, pdf_path: str) -> str:
        """
        Extracts raw text from a given PDF file.
        Returns a string containing the text.
        """
        text = ""
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text("text") + "\n"
        return text.strip()

    def process_pdf(self, pdf_path: str) -> ExtractedPDFData:
        """
        Extracts structured information from a PDF and ensures it is JSON-compliant.
        """
        llm = get_llm()
        text = self.extract_pdf_text(pdf_path)

        if not text:
            logger.info("No text extracted from the PDF.")
            return ExtractedPDFData(data={})

        logger.info(f"Extracted PDF Text: {text[:500]}...")

        prompt = f"""
        Extract key information from the document **and return only a valid JSON object**.
        **Do not include explanations, headers, or formatting like triple backticks.**

        **Instructions:**
        - Identify and extract:
          - **title** (string)
          - **department** (string)
          - **requested_items** (dictionary: keys = item names, values = {{"quantity": int}})
          - **justification** (string)
          - **requested_info** (list of strings)
        - Ensure `"requested_info"` is a **list (`[]`)**, NOT a tuple (`()`).
        - The response **must be a valid JSON object**.

        **Example Output Format:**
        {{
          "title": "Purchase Request",
          "department": "Future Computing Lab",
          "requested_items": {{
            "Quantum Neural Processing Units (QNPU-X)": {{"quantity": 3}},
            "Self-Learning Algorithmic Frameworks (SLA-Fusion)": {{"quantity": 5}}
          }},
          "justification": "Research on AI and quantum computing",
          "requested_info": ["estimated delivery timeline", "total cost"]
        }}

        **Extracted Information from Document:**
        {text}
        """


        response = llm.invoke([{"role": "user", "content": prompt}])

        if not response or not response.content.strip():
            logger.info("LLM returned an empty response.")
            return ExtractedPDFData(data={})

        # ensure JSON content is extracted correctly
        try:
            json_text = re.search(r"\{.*\}", response.content, re.DOTALL).group(0).strip()
        except AttributeError:
            logger.error("Failed to extract JSON from LLM response.")
            return ExtractedPDFData(data={})  # return empty if extraction fails

        try:
            # ensure tuple values are converted to lists for JSON compatibility
            extracted_data = json.loads(json_text, object_hook=lambda d: {
                k: list(v) if isinstance(v, tuple) else v for k, v in d.items()
            })

            structured_data = ExtractedPDFData(data=extracted_data)
            structured_data.make_hashable()

            logger.info(f"✅ Successfully Extracted PDF Data: {structured_data.data}")

            return structured_data

        except json.JSONDecodeError:
            logger.error(f"Failed to parse cleaned LLM response as JSON. Response: {json_text}")
            return ExtractedPDFData(data={})

    def process_pdf_node(self, state: State):
        """
        Calls the process_pdf function and updates the extracted information in state.
        """
        pdf_path = state.get("pdf_path")

        if not pdf_path:
            logger.error("No PDF path provided.")
            return {"extracted_information": None, "error": "No PDF uploaded."}

        extracted_data = self.process_pdf(pdf_path)  # ✅ Process PDF

        if not extracted_data or not extracted_data.data:
            logger.warning("⚠️ No structured data extracted from PDF.")
            return {"extracted_information": None, "error": "Failed to extract PDF content."}

        # store the entire ExtractedPDFData object, NOT just `.data`
        state["extracted_information"] = extracted_data

        logger.info(f"📄 Successfully Stored PDF Data in State: {state['extracted_information'].data}")
        return {"extracted_information": extracted_data, "error": None}

    def create_workflow(self):
        """
        Create the entire workflow
        """
        workflow = StateGraph(State)

        # Add nodes
        workflow.add_node("Router", self.decide_route)
        workflow.add_node("ProcessPDF", self.process_pdf)
        workflow.add_node("RequestAnalyzer", self.check_if_is_secure)
        workflow.add_node("CodeGenerator", self.generate_code)
        workflow.add_node("CodeAnalyzer", self.analyze_code)
        workflow.add_node("CodeExecutor", self.exec_code)
        workflow.add_node("AnswerGenerator", self.generate_answer)

        # second branch
        # workflow.add_node("AnswerDirectly", self.answer_directly)

        # define edges
        workflow.add_edge(START, "Router")

        workflow.add_conditional_edges(
            "Router",
            self.conditional_routing0,
            {
                "analyze_csv": "RequestAnalyzer",
                "process_pdf": "ProcessPDF",
                # "answer_directly": "AnswerDirectly",
            },
        )

        workflow.add_conditional_edges(
            "RequestAnalyzer",
            self.conditional_routing1,
            {"request_ok": "CodeGenerator", "end": END},
        )

        workflow.add_edge("CodeGenerator", "CodeAnalyzer")

        workflow.add_conditional_edges(
            "CodeAnalyzer",
            self.conditional_routing2,
            {"code_ok": "CodeExecutor", "end": END},
        )

        workflow.add_edge("CodeExecutor", "AnswerGenerator")
        workflow.add_edge("AnswerGenerator", END)
        workflow.add_edge("ProcessPDF", END)


        # workflow.add_edge("AnswerDirectly", END)

        # create workflow executor
        workflow_app = workflow.compile()

        return workflow_app

    #
    # helper functions
    #
    def call_llm(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 1024,
    ):
        """
        Helper function to call LLM with structured logging and error handling.

        :param prompt: The main user prompt.
        :param system_prompt: Optional system message to provide context.
        :param temperature: LLM creativity level.
        :param max_tokens: Maximum response length.
        :return: The processed LLM response or an error message.
        """
        try:
            llm = get_llm(temperature=temperature, max_tokens=max_tokens)

            # construct message history
            messages = []
            if system_prompt:
                messages.append(SystemMessage(content=system_prompt))
            messages.append(HumanMessage(content=prompt))

            # invoke the LLM
            response = llm.invoke(messages)

            # extract clean response (triple... is for code and json)
            clean_response = remove_triple_backtics(response.content)

            # log LLM interaction
            if DEBUG:
                logger.info(
                    "LLM Call",
                    extra={
                        "prompt": prompt,
                        "system_prompt": system_prompt,
                        "response": clean_response,
                    },
                )

            return clean_response

        except Exception as e:
            logger.error(f"LLM call failed: {str(e)}")
            return f"LLM error: {str(e)}"
