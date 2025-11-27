Copyright (c) 2025 Oracle and/or its affiliates.
"""
By Omar Salem
state.py - stores the state that tools update and maintain.
"""

from typing_extensions import TypedDict, NotRequired, List

# define an Email structure
class Email(TypedDict):
    """Represents an email"""
    id: str
    from_email: str
    subject: str
    summary: str

# define a base state structure
class BaseState(TypedDict):
    """Defines common properties for all states"""
    input: str
    decision: str
    output: str

# define Gmail-specific state
class GmailState(BaseState):
    """Stores Gmail-related state"""
    emails: NotRequired[List[Email]]
    selected_email: NotRequired[Email]
    recipient: NotRequired[str]
    subject: NotRequired[str]
    body: NotRequired[str]

# define AI Agent-specific state
class AIState(BaseState):
    """Stores AI agent-related state"""
    ai_response: NotRequired[str]
    citations: NotRequired[List[str]]

# define the main state that supports both Gmail & AI Agent
class State(GmailState, AIState):
    """Combines Gmail & AI Agent states"""
    pass

