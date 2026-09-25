from decimal import Decimal
from sqlmodel import Session
import json
from app.models.conversation import SearchHistory, SearchSession
from datetime import datetime, timezone

def _utc_now() -> datetime:
    return datetime.now(timezone.utc)



def _load_memory_from_session(search_session: SearchSession) -> list[dict[str, str]]:
    raw = search_session.memory or "[]"

    try:
        data = json.loads(raw)

        if not isinstance(data, list):
            return []

        cleaned: list[dict[str, str]] = []

        for item in data:
            if not isinstance(item, dict):
                continue

            role = item.get("role")
            content = item.get("content")

            if role in {"user", "assistant"} and isinstance(content, str):
                cleaned.append(
                    {
                        "role": role,
                        "content": content,
                    }
                )

        return cleaned

    except json.JSONDecodeError:
        return []


def _save_memory_to_session(
    session_db: Session,
    search_session: SearchSession,
    messages: list[dict[str, str]],
) -> None:
    search_session.memory = json.dumps(messages, ensure_ascii=False)
    search_session.updated_at = _utc_now()

    session_db.add(search_session)
    session_db.commit()
    session_db.refresh(search_session)


def _save_search_history(
    session_db: Session,
    search_session: SearchSession,
    current_user_id: int,
    user_message: str,
    reply_text: str,
    input_tokens: int,
    output_tokens: int,
    total_tokens: int,
    estimated_cost: float,
) -> None:
    history = SearchHistory(
        session_id=search_session.id,
        owner_id=current_user_id,
        query=user_message,
        result=reply_text,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        estimated_cost=Decimal(str(round(estimated_cost, 6))),
    )

    session_db.add(history)
    session_db.commit()


def _append_and_trim_memory(
    existing: list[dict[str, str]],
    user_message: str,
    assistant_message: str,
    max_messages: int = 20,
) -> list[dict[str, str]]:
    updated = [
        *existing,
        {
            "role": "user",
            "content": user_message,
        },
        {
            "role": "assistant",
            "content": assistant_message,
        },
    ]

    return updated[-max_messages:]


def format_chat_history_for_prompt(
    messages: list[dict[str, str]],
    max_messages: int = 10,
) -> str:
    """
    Only last N messages, 10 by default to avoid context overload, are included in the prompt context for the LLM.
    """
    recent = messages[-max_messages:]

    if not recent:
        return "No previous conversation."

    lines = []

    for msg in recent:
        role = msg["role"]
        content = msg["content"]
        lines.append(f"{role}: {content}")

    return "\n".join(lines)