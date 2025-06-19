import fitz  # PyMuPDF
import json
import tempfile
from typing import Dict, Tuple, Any
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage
from pydantic import BaseModel
from typing_extensions import TypedDict

from oci_models import get_llm  # LLM loader
from utils import remove_triple_backtics  # Output cleaner

# Dummy API that simulates checking invoice value
def dummy_invoice_api_check(extracted_total: float) -> float:
    return extracted_total

# --- Data Models ---
class ExtractedPDFData(BaseModel):
    data: Dict[str, Any]

    def make_hashable(self):
        for key, value in self.data.items():
            if isinstance(value, list):
                self.data[key] = tuple(value)

class State(TypedDict):
    pdf_path: str
    declared_amount: float
    extracted_information: ExtractedPDFData
    validation_messages: list
    error: str

# --- Agent ---
class ExpenseValidationAgent:
    def extract_pdf_text(self, pdf_path: str) -> str:
        text = ""
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text("text") + "\n"
        return text.strip()

    def process_pdf(self, pdf_path: str) -> ExtractedPDFData:
        llm = get_llm()
        text = self.extract_pdf_text(pdf_path)

        # early check if PDF is unreadable
        if not text or text.strip() == "":
            raise Exception("❌ No readable text extracted from the uploaded PDF. It may be scanned badly or empty.")

        prompt = f"""
        Extract ONLY a valid JSON object from the following document.
        No explanations, no formatting, no triple backticks.

        Required fields:
        - employee_name (string)
        - claim_date (string)
        - items (list of dicts with keys: 'description' (string), 'amount' (float), 'category' (string))
        - total_amount (float)

        Output must be a single valid JSON object.

        Document:
        {text}
        """

        response = llm.invoke([{"role": "user", "content": prompt}])

        if not response or not response.content or not response.content.strip():
            raise Exception("❌ LLM returned an empty output. Cannot extract PDF information.")

        cleaned = remove_triple_backtics(response.content.strip())

        # early check if LLM output is blank
        if not cleaned or cleaned.strip() == "":
            raise Exception("❌ Cleaned LLM output is empty. No valid data to extract.")

        if not cleaned.startswith("{"):
            raise Exception(f"❌ LLM output does not start with a JSON object.\nRaw output:\n{cleaned}")

        try:
            data = json.loads(cleaned)
        except Exception as e:
            raise Exception(f"❌ Failed to parse LLM output as JSON.\nRaw output:\n{cleaned}\nError: {e}")

        structured = ExtractedPDFData(data=data)
        structured.make_hashable()
        return structured

    def llm_extract_node(self, state: State) -> Dict[str, Any]:
        pdf_path = state["pdf_path"]
        extracted_data = self.process_pdf(pdf_path)

        if not extracted_data or not extracted_data.data:
            return {"extracted_information": None, "error": "Failed to extract structured PDF content."}

        return {"extracted_information": extracted_data, "error": None}

    def check_policy_node(self, state: State) -> Dict[str, Any]:
        llm = get_llm(temperature=0.0)
        extracted = state["extracted_information"].data

        policy_text = """..."""
        prompt = f"""
        Given the company policy:
        {policy_text}

        And the following expense claim:
        {json.dumps(extracted, indent=2)}

        Return a JSON object with:
        - status: "pass" if the claim conforms, "fail" if it violates
        - reason: 1-2 sentences explaining why

        Respond ONLY with a valid JSON object. Do not add anything else.
        """

        response = llm.invoke([HumanMessage(content=prompt)])
        raw = response.content.strip()
        cleaned = raw.replace("```json", "").replace("```", "").strip()

        try:
            result = json.loads(cleaned)
        except Exception as e:
            raise Exception(f"❌ LLM policy check did not return valid JSON.\nRaw output:\n{cleaned}\nError: {e}")

        status = result.get("status", "").lower()
        reason = result.get("reason", "No reason provided.")

        label = "✅ Policy Check: " if status == "pass" else "❌ Policy Check: "
        return {
            "validation_messages": state.get("validation_messages", []) + [label + reason]
        }

    def check_category_node(self, state: State) -> Dict[str, Any]:
        llm = get_llm(temperature=0.0)
        extracted = state["extracted_information"].data

        prompt = f"""
        Given this expense data:
        {json.dumps(extracted, indent=2)}

        Are any of the expense items clearly mismatched? For example, if 'Bread' is categorized under 'Travel'.

        Return a JSON object with:
        - status: "pass" if all items are categorized correctly, "fail" if there are mismatches
        - reason: 1-2 sentences explaining if any mismatch exists.

        Respond ONLY with a valid JSON object.
        """

        response = llm.invoke([HumanMessage(content=prompt)])
        raw = response.content.strip()
        cleaned = raw.replace("```json", "").replace("```", "").strip()

        try:
            result = json.loads(cleaned)
        except Exception as e:
            raise Exception(f"❌ LLM category check did not return valid JSON.\nRaw output:\n{cleaned}\nError: {e}")

        status = result.get("status", "").lower()
        reason = result.get("reason", "No reason provided.")

        label = "✅ Category Check: " if status == "pass" else "❌ Category Check: "
        return {
            "validation_messages": state.get("validation_messages", []) + [label + reason]
        }

    def check_declared_amount_node(self, state: State) -> Dict[str, Any]:
        extracted_total = state["extracted_information"].data.get("total_amount", 0.0)
        api_total = dummy_invoice_api_check(extracted_total)
        declared = state["declared_amount"]

        if abs(api_total - declared) > 0.1:
            return {"validation_messages": state.get("validation_messages", []) + [
                f"⚠️ Declared amount mismatch. Declared: ${declared:.2f}, Backend Invoice: ${api_total:.2f}"
            ]}
        else:
            return {"validation_messages": state.get("validation_messages", []) + [
                "✅ Declared Amount Check: No significant mismatch"
            ]}

    def create_workflow(self):
        graph = StateGraph(State)

        graph.add_node("Extract", self.llm_extract_node)
        graph.add_node("PolicyCheck", self.check_policy_node)
        graph.add_node("CategoryCheck", self.check_category_node)
        graph.add_node("AmountCheck", self.check_declared_amount_node)

        graph.add_edge(START, "Extract")
        graph.add_edge("Extract", "PolicyCheck")
        graph.add_edge("PolicyCheck", "CategoryCheck")
        graph.add_edge("CategoryCheck", "AmountCheck")
        graph.add_edge("AmountCheck", END)

        return graph.compile()

# --- Public API ---
def process_expense_workflow(pdf_bytes: bytes, declared_amount: float) -> Tuple[Dict[str, Any], list]:
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    temp_file.write(pdf_bytes)
    temp_file.close()

    agent = ExpenseValidationAgent()
    workflow = agent.create_workflow()

    initial_state = {
        "pdf_path": temp_file.name,
        "declared_amount": declared_amount,
        "extracted_information": None,
        "validation_messages": [],
        "error": None
    }

    final_state = workflow.invoke(initial_state)

    if final_state.get("error"):
        raise Exception(final_state["error"])

    return final_state["extracted_information"].data, final_state["validation_messages"]