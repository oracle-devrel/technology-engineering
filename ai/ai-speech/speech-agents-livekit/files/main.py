import sys
import os
import asyncio
import logging
import json
import re
from datetime import date

import oracledb
import oci
from oci.base_client import BaseClient
from dotenv import load_dotenv
from openai import OpenAI
from oci_genai_auth import OciUserPrincipalAuth
import httpx

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions, function_tool, RunContext
from livekit.plugins import oracle, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from livekit.plugins.oracle.utils import AuthenticationType
from livekit.plugins.oracle.oracle_llm import BackEnd

load_dotenv()

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

plugin_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.append(plugin_path)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

REGION = ""
SEMANTIC_STORE_ID = ""
PROJECT_ID = ""
VECTOR_STORE_ID = ""
COMPARTMENT_ID = ""
INFERENCE_ENDPOINT = f"https://inference.generativeai.{REGION}.oci.oraclecloud.com"

DB_USER = os.getenv("DB_USER", "")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_DSN = os.getenv("DB_DSN",""),
WALLET_PASSWORD = os.getenv("WALLET_PASSWORD",""),

# Filler phrases spoken while tool calls are running (not added to LLM history)
TOOL_FILLERS = {
    "search_hotel_documents": "One moment while I check our hotel information.",
    "search_web": "Let me look that up for you.",
    "search_room_availability": "One moment while I check availability.",
    "create_booking": "Let me process that booking for you.",
}

DB_FILLER_MESSAGES = [
    "Still checking, thank you for your patience.",
    "I'm pulling up the latest availability for you.",
    "Almost done, just a few more seconds.",
    "Thank you for waiting, nearly there.",
]


config = oci.config.from_file(os.path.expanduser("~/.oci/config"), "DEFAULT")
signer = oci.signer.Signer(
    tenancy=config["tenancy"],
    user=config["user"],
    fingerprint=config["fingerprint"],
    private_key_file_location=config["key_file"],
)


def make_oci_client() -> BaseClient:
    return BaseClient(
        "generative_ai",
        config,
        signer,
        {},
        service_endpoint=INFERENCE_ENDPOINT,
        retry_strategy=None,
    )


# ---------------------------------------------------------------------------
# OCI OpenAI-compatible client (file search + web search)
# ---------------------------------------------------------------------------

oci_openai_client = OpenAI(
    base_url=f"https://inference.generativeai.{REGION}.oci.oraclecloud.com/openai/v1",
    api_key="not-used",
    project=PROJECT_ID,
    http_client=httpx.Client(auth=OciUserPrincipalAuth(profile_name="DEFAULT")),
)


# ---------------------------------------------------------------------------
# NL → SQL
# ---------------------------------------------------------------------------

FORBIDDEN_KEYWORDS = (
    "insert", "update", "delete", "drop", "alter", "truncate",
    "merge", "grant", "revoke", "create", "replace", "call", "execute",
)


def generate_sql(question: str) -> str:
    """Call the OCI NL2SQL endpoint and return the generated SQL string."""
    resp = make_oci_client().call_api(
        resource_path=f"/20260325/semanticStores/{SEMANTIC_STORE_ID}/actions/generateSqlFromNl",
        method="POST",
        header_params={"content-type": "application/json"},
        body={
            "displayName": "query",
            "description": "agent query",
            "inputNaturalLanguageQuery": question,
        },
        response_type="str",
    )
    data = resp.data
    if isinstance(data, bytes):
        data = data.decode("utf-8")
    data = json.loads(data)
    sql = data.get("jobOutput", {}).get("content", "")
    if not sql:
        raise ValueError(f"No SQL generated: {data}")
    return sql


def validate_readonly(sql: str) -> str:
    """Raise ValueError if the SQL is not a read-only SELECT/WITH statement."""
    s = sql.strip().lower()
    if not s.startswith(("select", "with")):
        raise ValueError("Only SELECT queries are allowed.")
    for keyword in FORBIDDEN_KEYWORDS:
        if re.search(rf"\b{keyword}\b", s):
            raise ValueError(f"Forbidden keyword: {keyword}")
    return sql


def run_sql(sql: str):
    """Execute a SQL query and return (columns, rows)."""
    db_cursor.execute(sql)
    cols = [c[0] for c in db_cursor.description] if db_cursor.description else []
    rows = db_cursor.fetchall()
    return cols, rows

def get_db():
    conn = oracledb.connect(
        user=DB_USER,
        password=DB_PASSWORD,
        dsn=DB_DSN,
        wallet_location="./Wallet",
        wallet_password=WALLET_PASSWORD,
    )
    return conn, conn.cursor()

# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

SYSTEM_INSTRUCTIONS = (
    "Today's date is {today}. "
    "You are a friendly hotel reservation assistant for Harbor View Hotels & Suites, "
    "located in Chicago, Illinois. "
    "When a guest asks about hotel information — policies, amenities, rooms, pricing, "
    "pet rules, dining, or anything hotel-related — use search_hotel_documents. "
    "For room availability, bookings, or pricing queries — use search_room_availability. "
    "For anything about Chicago — weather, local attractions, things to do, restaurants, "
    "events, transportation, or anything about the city — use search_web and search specifically "
    "for Chicago. Always include 'Chicago' in your web search query. "
    "When presenting room availability results, summarize concisely — say how many rooms "
    "are available and mention room types and prices. Do NOT read out every row. "
    "When a booking is confirmed, tell the guest their booking ID and that a customer "
    "support agent will call them during business hours (9am-6pm) to follow up. "
    "Keep all responses to one or two short sentences. "
    "IMPORTANT: Always call the appropriate tool before responding. Never say 'one moment' "
    "or any filler phrase yourself — just call the tool directly. "
    "The initial greeting should be: Welcome to Harbor View Hotels and Suites, how can I help you?"
)


class Assistant(Agent):

    def __init__(self) -> None:
        super().__init__(
            instructions=SYSTEM_INSTRUCTIONS.format(today=date.today().strftime("%B %d, %Y"))
        )

    async def on_enter(self):
        """Called when the agent starts. We handle fillers via before_tool_call instead."""
        pass

    async def before_tool_call(self, tool_name: str, tool_args: dict) -> None:
        """
        Fires before each tool call. Say a filler phrase here so it is spoken
        as transient TTS — it does NOT get added to the LLM message history.
        """
        filler = TOOL_FILLERS.get(tool_name)
        if filler:
            await self.session.say(filler, allow_interruptions=True)

    @function_tool
    async def search_hotel_documents(self, context: RunContext, query: str) -> str:
        """
        Search the hotel knowledge base for policies, amenities, room descriptions,
        check-in/check-out times, pet policies, dining, and hotel-related information.

        Args:
            query: The question or topic to search for.
        """
        logger.debug("search_hotel_documents: %s", query)

        return await _run_with_filler(
            context,
            lambda: oci_openai_client.responses.create(
                model="openai.gpt-4.1-mini",
                instructions=(
                    "You are a hotel assistant. Answer concisely in one or two sentences "
                    "using only the hotel documents provided."
                ),
                input=query,
                tools=[{"type": "file_search", "vector_store_ids": [VECTOR_STORE_ID]}],
            ).output_text,
        )

    @function_tool
    async def search_web(self, context: RunContext, query: str) -> str:
        """
        Search the web for weather, local attractions, restaurants, events,
        transportation, or anything outside the hotel.

        Args:
            query: The question or topic to search for.
        """
        logger.debug("search_web: %s", query)

        return await _run_with_filler(
            context,
            lambda: oci_openai_client.responses.create(
                model="openai.gpt-4.1",
                instructions="You are a hotel concierge and local guide. Answer concisely in one or two sentences.",
                input=query,
                tools=[{"type": "web_search"}],
            ).output_text,
        )

    @function_tool
    async def search_room_availability(self, context: RunContext, query: str) -> str:
        """
        Check room availability, pricing, or existing bookings by querying the database.
        Use this for any question about available rooms, dates, prices, or reservations.

        Args:
            query: Natural language question about room availability or bookings.
        """
        logger.debug("search_room_availability: %s", query)

        async def _do_query():
            sql = await asyncio.to_thread(generate_sql, query)
            sql = validate_readonly(sql)
            cols, rows = await asyncio.to_thread(run_sql, sql)
            if not rows:
                return "No rooms found matching those criteria."
            return json.dumps(
                {"columns": cols, "rows": rows[:10], "total_found": len(rows)},
                default=str,
            )

        async def _do_fillers():
            await context.session.say(DB_FILLER_MESSAGES[0], allow_interruptions=True)
            for message in DB_FILLER_MESSAGES[1:]:
                await asyncio.sleep(5)
                await context.session.say(message, allow_interruptions=True)

        task = asyncio.create_task(_do_query())
        filler_task = asyncio.create_task(_do_fillers())

        try:
            result = await task
        finally:
            filler_task.cancel()

        return result

    @function_tool
    async def create_booking(
        self,
        context: RunContext,
        room_id: int,
        guest_name: str,
        guest_email: str,
        check_in_date: str,
        check_out_date: str,
    ) -> str:
        """
        Create a room booking for a guest. Call this only after confirming the guest
        wants to proceed with the booking.

        Args:
            room_id: The ID of the room to book (from availability search results).
            guest_name: Full name of the guest.
            guest_email: Email address of the guest.
            check_in_date: Check-in date in YYYY-MM-DD format.
            check_out_date: Check-out date in YYYY-MM-DD format.
        """
        logger.debug(
            "create_booking: room=%s guest=%s %s-%s",
            room_id, guest_name, check_in_date, check_out_date,
        )

        try:
            # Check room isn't already booked for these dates
            check_sql = """
                SELECT COUNT(*) FROM BOOKINGS
                WHERE ROOM_ID = :room_id
                AND STATUS = 'CONFIRMED'
                AND CHECK_IN_DATE < TO_DATE(:check_out, 'YYYY-MM-DD')
                AND CHECK_OUT_DATE > TO_DATE(:check_in, 'YYYY-MM-DD')
            """
            db_cursor.execute(check_sql, {
                "room_id": room_id,
                "check_in": check_in_date,
                "check_out": check_out_date,
            })
            count = db_cursor.fetchone()[0]
            if count > 0:
                return f"Sorry, room {room_id} is no longer available for those dates. Please choose another room."

            # Insert booking
            insert_sql = """
                INSERT INTO BOOKINGS (ROOM_ID, GUEST_NAME, GUEST_EMAIL, CHECK_IN_DATE, CHECK_OUT_DATE, STATUS)
                VALUES (
                    :room_id,
                    :guest_name,
                    :guest_email,
                    TO_DATE(:check_in, 'YYYY-MM-DD'),
                    TO_DATE(:check_out, 'YYYY-MM-DD'),
                    'CONFIRMED'
                )
                RETURNING BOOKING_ID INTO :booking_id
            """
            booking_id_var = db_cursor.var(int)
            db_cursor.execute(insert_sql, {
                "room_id": room_id,
                "guest_name": guest_name,
                "guest_email": guest_email,
                "check_in": check_in_date,
                "check_out": check_out_date,
                "booking_id": booking_id_var,
            })
            db_conn.commit()

            booking_id = booking_id_var.getvalue()[0]
            return json.dumps({
                "success": True,
                "booking_id": booking_id,
                "room_id": room_id,
                "guest_name": guest_name,
                "check_in": check_in_date,
                "check_out": check_out_date,
                "message": (
                    f"Booking confirmed! ID: {booking_id}. "
                    "A customer support agent will call you during business hours (9am-6pm) to follow up."
                ),
            })

        except Exception as e:
            db_conn.rollback()
            logger.error("Booking failed: %s", e)
            return "Sorry, I was unable to complete the booking. Please try again or contact us directly."


async def _run_with_filler(context: RunContext, search_fn) -> str:
    search_task = asyncio.create_task(asyncio.to_thread(search_fn))

    async def _maybe_filler():
        await asyncio.sleep(1.5)
        if not search_task.done():
            await context.session.say("One moment please.", allow_interruptions=True)

    filler_task = asyncio.create_task(_maybe_filler())
    try:
        response = await search_task
    finally:
        filler_task.cancel()
    return response


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

async def entrypoint(ctx: agents.JobContext):
    global db_conn, db_cursor
    db_conn, db_cursor = get_db()
    await ctx.connect()

    session = AgentSession(
        stt=oracle.STT(
            authentication_type=AuthenticationType.API_KEY,
            authentication_configuration_file_spec="~/.oci/config",
            authentication_profile_name="DEFAULT",
            base_url=f"wss://realtime.aiservice.{REGION}.oci.oraclecloud.com",
            compartment_id=COMPARTMENT_ID,
            partial_silence_threshold_milliseconds=750,
            final_silence_threshold_milliseconds=750,
        ),
        llm=oracle.LLM(
            authentication_type=AuthenticationType.API_KEY,
            authentication_configuration_file_spec="~/.oci/config",
            authentication_profile_name="DEFAULT",
            base_url=f"https://inference.generativeai.{REGION}.oci.oraclecloud.com",
            back_end=BackEnd.GEN_AI_LLM,
            compartment_id=COMPARTMENT_ID,
            model_name="openai.gpt-4.1-mini",
            model_type="GENERIC",
        ),
        tts=oracle.TTS(
            authentication_type=AuthenticationType.API_KEY,
            authentication_configuration_file_spec="~/.oci/config",
            authentication_profile_name="DEFAULT",
            base_url=f"https://speech.aiservice.{REGION}.oci.oraclecloud.com",
            compartment_id=COMPARTMENT_ID,
            voice="Victoria",
        ),
        allow_interruptions=True,
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
        max_tool_steps=20,
    )

    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_input_options=RoomInputOptions(),
    )

    await session.generate_reply(instructions="Greet the user and offer your assistance.")


if __name__ == "__main__":
    agents.cli.run_app(
        agents.WorkerOptions(
            entrypoint_fnc=entrypoint,
            job_executor_type=agents.JobExecutorType.THREAD,
            initialize_process_timeout=60.0,
        )
    )