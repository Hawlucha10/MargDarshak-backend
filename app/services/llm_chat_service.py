"""
LLM Chat Service for MargDarshak
================================
Orchestrates conversational AI powered by Groq LLM (Qwen 27B / GPT-OSS 20B) with native
tool calling. Grounded in real Indian Railways data, delay predictions, bus alternatives,
and upstream quota arbitrage.
"""

import json
import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional
import httpx

from app.config import get_settings
from app.services.nlp_search import STATION_ALIAS_MAP
from app.services.bus_service import get_connecting_buses
from app.ml.delay_predictor import get_predictor
from app.db.postgres import get_session_maker
from sqlalchemy import text

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are MargDarshak AI, an intelligent, multimodal travel assistant for Indian Railways and bus corridors.
You help passengers navigate complex journeys across India with practical, data-grounded advice.

Your Key Superpowers:
1. Multimodal Flexibility: If train direct seats are unavailable or layovers between connecting trains are too long (>2-3 hours), suggest hopping on a connecting bus (e.g. MSRTC, UPSRTC, Zingbus) from the transfer junction to reach faster.
2. Upstream Station Hacks: When seats are waitlisted from a passenger's origin station, check if booking from 1-3 stations upstream (earlier stop) provides confirmed General/Tatkal seats with minimal fare difference.
3. Predictive Delay Risk: Alert passengers if their train has a high historical delay risk and advise sufficient transfer buffer (>60-90 mins).
4. Direct & Concise: Keep answers clear, structured with bullet points or numbered steps, and actionable.
5. Multilingual: Speak naturally in English, Hindi, or Hinglish depending on what language the user uses.

Always use your tools when users ask for specific routes, bus alternatives, delays, or seat availability.
If no tool is needed for general queries or chit-chat, respond warmly and guide them on how MargDarshak can help.
"""

GROQ_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_routes",
            "description": "Search Pareto-optimal train routes and multimodal bus-train combinations between two stations or cities.",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {"type": "string", "description": "Origin station code or city (e.g. NDLS, Pune, Mumbai, GWL)"},
                    "destination": {"type": "string", "description": "Destination station code or city (e.g. PUNE, Delhi, Gwalior, AGC)"},
                    "travel_date": {"type": "string", "description": "Travel date in YYYY-MM-DD format (defaults to tomorrow if omitted)"},
                    "include_buses": {"type": "boolean", "description": "Whether to include connecting bus options to bridge transfers"}
                },
                "required": ["origin", "destination"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_bus_segments",
            "description": "Find direct bus services connecting two railway stations or cities to avoid train layovers or travel faster by road.",
            "parameters": {
                "type": "object",
                "properties": {
                    "from_station": {"type": "string", "description": "Origin station code or city (e.g. PUNE, CSTM, NDLS, AGC)"},
                    "to_station": {"type": "string", "description": "Destination station code or city (e.g. CSTM, PUNE, GWL)"},
                    "after_time": {"type": "string", "description": "Earliest departure time filter in HH:MM (e.g. '14:00')"}
                },
                "required": ["from_station", "to_station"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_train_delay",
            "description": "Check ML ensemble delay prediction and risk factors for a specific Indian Railway train number.",
            "parameters": {
                "type": "object",
                "properties": {
                    "train_number": {"type": "string", "description": "5-digit Indian Railway train number (e.g. 12138, 12952, 12626)"},
                    "station_code": {"type": "string", "description": "Optional station code along the route to evaluate delay at (e.g. AGC, GWL, BPL)"}
                },
                "required": ["train_number"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_upstream_seats",
            "description": "Check if booking from an upstream (previous) station unlocks confirmed seats on a waitlisted train.",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {"type": "string", "description": "Passenger boarding station code or city (e.g. GWL, AGC)"},
                    "destination": {"type": "string", "description": "Destination station code or city (e.g. PUNE, BPL)"},
                    "train_number": {"type": "string", "description": "5-digit train number"},
                    "travel_date": {"type": "string", "description": "Travel date in YYYY-MM-DD"}
                },
                "required": ["origin", "destination", "train_number"]
            }
        }
    }
]


def resolve_station_code(name_or_code: str) -> str:
    """Normalize city or station name to standard IRCTC uppercase code."""
    cleaned = name_or_code.strip()
    upper = cleaned.upper()
    if len(upper) in [2, 3, 4, 5] and upper.isalpha():
        # Check if already a code
        if upper in STATION_ALIAS_MAP.values():
            return upper
    lower = cleaned.lower()
    if lower in STATION_ALIAS_MAP:
        return STATION_ALIAS_MAP[lower]
    return upper


async def _execute_search_routes(args: Dict[str, Any], context: Dict[str, Any]) -> str:
    """Execute search pipeline and extract top options for LLM context."""
    from app.schemas.route import RouteSearchRequest
    from app.api.v1.search import search_routes

    orig = resolve_station_code(args.get("origin", ""))
    dest = resolve_station_code(args.get("destination", ""))
    travel_date = args.get("travel_date") or date.today().strftime("%Y-%m-%d")
    include_buses = args.get("include_buses", True)

    req = RouteSearchRequest(
        origin=orig,
        destination=dest,
        travel_date=travel_date,
        include_buses=include_buses,
        priority="balanced",
        max_transfers=2
    )
    res = await search_routes(req)

    context["routes_found"] = res.total_routes_found
    context["origin"] = orig
    context["destination"] = dest

    if not res.routes:
        return f"No direct or 1-transfer routes found between {orig} and {dest} for {travel_date}."

    previews = []
    summary_lines = [f"Found {res.total_routes_found} route options for {orig} -> {dest} on {travel_date}:"]
    for idx, r in enumerate(res.routes[:3], 1):
        legs_desc = []
        for l in r.legs:
            legs_desc.append(f"Train {l.train_number} ({l.train_name or 'Exp'}) from {l.from_station} ({l.departure_time}) to {l.to_station} ({l.arrival_time})")
        for b in r.bus_legs:
            legs_desc.append(f"Bus {b.operator_name} ({b.bus_type}) from {b.from_terminal} ({b.departure_time}) to {b.to_terminal} ({b.arrival_time})")

        dur_h = r.travel_time_min // 60
        dur_m = r.travel_time_min % 60
        summary_lines.append(
            f"Option {idx} [{r.pareto_label}]: Duration {dur_h}h {dur_m}m, Fare Rs.{r.total_fare}, "
            f"Transfers: {r.transfers}, Reliability: {int(r.reliability_score * 100)}%. "
            f"Legs: {' -> '.join(legs_desc)}"
        )
        previews.append({
            "id": r.route_id,
            "label": r.pareto_label,
            "duration": f"{dur_h}h {dur_m}m",
            "fare": r.total_fare,
            "transfers": r.transfers,
            "is_multimodal": r.is_multimodal,
            "legs_summary": " -> ".join(legs_desc)
        })

    context["routes_preview"] = previews
    return "\n".join(summary_lines)


async def _execute_get_bus_segments(args: Dict[str, Any], context: Dict[str, Any]) -> str:
    """Execute direct bus discovery between terminals."""
    from_stn = resolve_station_code(args.get("from_station", ""))
    to_stn = resolve_station_code(args.get("to_station", ""))
    after_time = args.get("after_time")

    buses = await get_connecting_buses(
        from_station_code=from_stn,
        to_station_code=to_stn,
        after_time=after_time,
        limit=4
    )

    if not buses:
        return f"No connecting buses registered in database between station corridors {from_stn} and {to_stn}."

    context["buses_preview"] = buses
    out = [f"Found {len(buses)} connecting buses between {from_stn} and {to_stn}:"]
    for b in buses:
        dur_h = b["duration_minutes"] // 60
        dur_m = b["duration_minutes"] % 60
        out.append(
            f"- {b['operator_name']} ({b['bus_type']}): Departs {b['departure']} -> Arrives {b['arrival']} "
            f"({dur_h}h {dur_m}m), Fare: Rs.{b['fare']}. Terminal: {b['from_terminal']} -> {b['to_terminal']}."
        )
    return "\n".join(out)


async def _execute_check_train_delay(args: Dict[str, Any], context: Dict[str, Any]) -> str:
    """Execute ML delay predictor for a train."""
    train_no = str(args.get("train_number", "")).strip()
    stn = resolve_station_code(args.get("station_code", "NDLS"))

    predictor = get_predictor()
    pred = predictor.predict_delay(
        train_number=train_no,
        station_code=stn,
        departure_hour=14,
        day_of_week=0
    )

    prob_pct = int(pred["delay_probability"] * 100)
    exp_delay = pred["predicted_delay_minutes"]
    p85 = pred["p85_delay_buffer_minutes"]
    risk = pred["risk_level"]
    explanations = ", ".join(pred["explanations"]) if pred["explanations"] else "Normal traffic conditions."

    return (
        f"Train {train_no} ML Delay Analysis at {stn}:\n"
        f"- Delay Probability: {prob_pct}%\n"
        f"- Expected Mean Delay: {exp_delay} minutes\n"
        f"- Recommended Safety Buffer (P85): {p85} minutes\n"
        f"- Risk Category: {risk.upper()}\n"
        f"- Contributing Factors: {explanations}"
    )


async def _execute_find_upstream_seats(args: Dict[str, Any], context: Dict[str, Any]) -> str:
    """Execute upstream seat check and return arbitrage savings."""
    from app.services.availability_service import check_availability
    from app.services.fare_service import calculate_official_fare

    orig = resolve_station_code(args.get("origin", ""))
    dest = resolve_station_code(args.get("destination", ""))
    train_no = str(args.get("train_number", "")).strip()
    t_date = args.get("travel_date") or date.today().strftime("%Y-%m-%d")

    session_maker = get_session_maker()
    async with session_maker() as session:
        # Fetch stops for train
        q = text("""
            SELECT s.code, s.name, ts.stop_number
            FROM train_stations ts
            JOIN stations s ON ts.station_id = s.id
            JOIN trains t ON ts.train_id = t.id
            WHERE t.number = :tno
            ORDER BY ts.stop_number ASC
        """)
        rows = (await session.execute(q, {"tno": train_no})).fetchall()
        if not rows:
            return f"Train {train_no} schedule not found in database."

        stop_codes = [r[0] for r in rows]
        if orig not in stop_codes:
            return f"Station {orig} is not on the route of train {train_no}."

        orig_idx = stop_codes.index(orig)
        upstream_candidates = stop_codes[max(0, orig_idx - 3):orig_idx]

        # Check origin availability
        orig_avail = await check_availability(train_no, orig, dest, t_date, "SL", "GN")
        orig_status = orig_avail.get("status", "AVAILABLE")
        orig_seats = orig_avail.get("available_seats", 10)

        # Check upstreams
        tips = []
        for u_code in reversed(upstream_candidates):
            u_avail = await check_availability(train_no, u_code, dest, t_date, "SL", "GN")
            u_seats = u_avail.get("available_seats", 0)
            if u_seats > 5 and orig_seats <= 0:
                fare_orig = calculate_official_fare(train_no, orig, dest, "SL")
                fare_u = calculate_official_fare(train_no, u_code, dest, "SL")
                diff = fare_u - fare_orig
                tips.append(
                    f"Book from {u_code} (previous stop) -> Confirmed {u_seats} seats! "
                    f"Extra cost: Rs.{diff}. Boarding can be set to {orig} on IRCTC."
                )

        if tips:
            return f"Upstream Quota Arbitrage for Train {train_no} (Origin {orig} currently {orig_status}):\n" + "\n".join(tips)
        else:
            return f"Train {train_no} from {orig} to {dest} has status: {orig_status} ({orig_seats} seats). No upstream advantage detected."


TOOL_EXECUTORS = {
    "search_routes": _execute_search_routes,
    "get_bus_segments": _execute_get_bus_segments,
    "check_train_delay": _execute_check_train_delay,
    "find_upstream_seats": _execute_find_upstream_seats,
}


async def run_chat_completion(
    message: str,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    current_origin: Optional[str] = None,
    current_destination: Optional[str] = None,
    travel_date: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Executes a complete LLM chat completion with tool-calling capabilities.
    Returns:
      {
        "reply": str,
        "suggested_actions": List[str],
        "routes_preview": List[Dict],
        "buses_preview": List[Dict]
      }
    """
    settings = get_settings()
    api_key = settings.groq_api_key
    model = settings.groq_model

    messages: List[Dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Inject page context if user is actively searching
    if current_origin and current_destination:
        context_note = (
            f"User is currently viewing routes for: {current_origin} -> {current_destination} "
            f"(Date: {travel_date or 'today'}). Keep this context in mind if they ask follow-up questions."
        )
        messages.append({"role": "system", "content": context_note})

    # Append history
    if conversation_history:
        for m in conversation_history[-6:]:  # Keep recent context
            messages.append({"role": m["role"], "content": m["content"]})

    messages.append({"role": "user", "content": message})

    context_state: Dict[str, Any] = {}

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "MargDarshak/1.0",
    }

    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            payload = {
                "model": model,
                "messages": messages,
                "tools": GROQ_TOOLS,
                "tool_choice": "auto",
                "temperature": 0.4,
                "max_tokens": 600,
            }

            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
            )

            if resp.status_code != 200:
                logger.error(f"Groq API error {resp.status_code}: {resp.text}")
                # Fallback to smart local response if Groq fails
                return _local_rule_fallback(message, current_origin, current_destination)

            data = resp.json()
            choice = data["choices"][0]
            bot_msg = choice["message"]

            tool_calls = bot_msg.get("tool_calls")
            if not tool_calls:
                # Direct answer
                content = bot_msg.get("content") or "I'm here to help you plan your journey across trains and buses!"
                return {
                    "reply": content,
                    "suggested_actions": _generate_suggested_actions(content, current_origin, current_destination),
                    "routes_preview": context_state.get("routes_preview"),
                    "buses_preview": context_state.get("buses_preview"),
                }

            # Execute tool calls
            messages.append(bot_msg)
            for tc in tool_calls:
                fn_name = tc["function"]["name"]
                try:
                    fn_args = json.loads(tc["function"]["arguments"])
                except Exception:
                    fn_args = {}

                executor = TOOL_EXECUTORS.get(fn_name)
                if executor:
                    try:
                        tool_result = await executor(fn_args, context_state)
                    except Exception as ex:
                        logger.exception(f"Error executing tool {fn_name}: {ex}")
                        tool_result = f"Error querying {fn_name}: {str(ex)}"
                else:
                    tool_result = f"Tool {fn_name} not found."

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": tool_result,
                })

            # Send back to LLM to formulate final conversational response
            second_payload = {
                "model": model,
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 600,
            }
            resp2 = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=second_payload,
            )

            if resp2.status_code == 200:
                final_data = resp2.json()
                final_content = final_data["choices"][0]["message"].get("content") or ""
                return {
                    "reply": final_content,
                    "suggested_actions": _generate_suggested_actions(final_content, current_origin, current_destination),
                    "routes_preview": context_state.get("routes_preview"),
                    "buses_preview": context_state.get("buses_preview"),
                }
            else:
                return {
                    "reply": "I retrieved the travel options for you. Please check the route and bus details attached!",
                    "suggested_actions": ["Search trains", "View bus options"],
                    "routes_preview": context_state.get("routes_preview"),
                    "buses_preview": context_state.get("buses_preview"),
                }

    except Exception as e:
        logger.exception(f"Exception during LLM chat execution: {e}")
        return _local_rule_fallback(message, current_origin, current_destination)


def _generate_suggested_actions(content: str, orig: Optional[str], dest: Optional[str]) -> List[str]:
    """Generate dynamic follow-up prompt chips for the user."""
    actions = []
    content_lower = content.lower()

    if "bus" in content_lower:
        actions.append("Show bus schedule & fares")
    if "delay" in content_lower or "late" in content_lower:
        actions.append("Check safe transfer buffer")
    if "waitlist" in content_lower or "seat" in content_lower or "upstream" in content_lower:
        actions.append("Find confirmed upstream seats")
    if orig and dest:
        actions.append(f"Search all routes {orig} to {dest}")
    else:
        actions.append("Fastest train + bus route")
        actions.append("Check train delay risk")

    return actions[:3]


def _local_rule_fallback(message: str, orig: Optional[str], dest: Optional[str]) -> Dict[str, Any]:
    """Smart fallback if API is unavailable."""
    msg = message.lower()
    if "bus" in msg:
        reply = (
            "You can take connecting buses between major railway hubs (like Pune, Mumbai, Agra, Delhi) "
            "to bridge long train layovers. MargDarshak supports 1,138 bus corridors with state and private operators."
        )
        actions = ["Check Pune-Mumbai buses", "View multimodal options"]
    elif "delay" in msg or "late" in msg:
        reply = (
            "MargDarshak uses a 3-model ensemble (CatBoost + LightGBM + XGBoost) to predict train delays "
            "and compute a statistical P85 safety buffer to protect transfers."
        )
        actions = ["Predict train delay", "Search reliable trains"]
    else:
        reply = (
            f"Hello! I am MargDarshak AI assistant. Ask me about finding fastest routes between cities, "
            f"taking buses to bypass train delays or layovers, and finding confirmed seats using upstream booking."
        )
        actions = ["Delhi to Pune options", "How does upstream booking work?", "Check train delay"]

    return {
        "reply": reply,
        "suggested_actions": actions,
        "routes_preview": None,
        "buses_preview": None,
    }
