"""
CSV Analyzer backend
"""

from langchain_core.messages import SystemMessage, HumanMessage

from prompts import PROMPT_GENERATE_ANSWER, PROMPT_GENERATE_CODE
from context import get_variable_info
from oci_models import get_llm
from utils import get_console_logger, remove_triple_backtics
from config import DEBUG


logger = get_console_logger()


def generate_code(df, question, chat_history=None, previous_error=None):
    """
    generate the code, to be executed on the df, to answer to the question
    """
    llm = get_llm(temperature=0.0, max_tokens=2048)

    # get metadata and samples about the df
    df_info = get_variable_info("df", df)

    if DEBUG:
        logger.info("df metadata: %s", df_info)

    # this will be added to system prompt
    context_and_request = f"""
    Context: {df_info}\n
    Chat history: {chat_history}\n
    Question: {question}
    """

    # if error correction is requested
    if previous_error:
        context_and_request += f"\nTry to correct this error: {previous_error}"

    # prepare messages and send to LL
    messages = [
        SystemMessage(content=PROMPT_GENERATE_CODE),
        HumanMessage(content=context_and_request),
    ]

    _response = llm.invoke(messages)

    _code = remove_triple_backtics(_response.content)

    if DEBUG:
        logger.debug("Generated code:\n{_code}")

    return _code


def exec_code(_df, code):
    """
    execute the code in a constrained environment
    """
    import pandas as pd
    from tabulate import tabulate

    # since the exec work on df, we need to have it here
    # and we want to work on a copy, to avoid "side effects"
    df = _df.copy()

    # create a context dict (a limited context)
    context = {"df": df, "pd": pd, "tabulate": tabulate, "result": None}

    # exec the code
    exec(code, context)

    output = context.get("result", None)

    #  output can be or not a dataframe
    return output


def generate_answer(question, code_output):
    """
    generate the answer to the question
    """
    llm = get_llm(max_tokens=2048)

    messages = [
        SystemMessage(content=PROMPT_GENERATE_ANSWER),
        HumanMessage(content=f"Context: {code_output}\nQuestion: {question}\n"),
    ]

    return llm.invoke(messages).content
