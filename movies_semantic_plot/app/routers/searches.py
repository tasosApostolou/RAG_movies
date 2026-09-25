## Schema -> response_model -> API's output validation
## Model -> DB table inference

import uuid
from typing import Any
from fastapi import APIRouter, HTTPException, Request
from sqlmodel import func, select

from app.core.error_handler import RateLimitError, RequestLimitError
from app.core.rate_limiter import RateLimitConfig, RateLimiter
from app.rag.graph import run_agent_on_session
from app.dependencies import CurrentUser, SessionDep
from app.models.conversation import (
    SearchSession,
    SearchSessionCreate,
    SearchSessionPublic,
    SearchSessionWithHistoryPublic,
    SearchSessionsPublic,
    SearchHistory,
    SearchHistoryCreate,
    SearchHistoryPublic,
    SearchHistoriesPublic,
    AgentChatRequest,
    AgentChatResponse,
)

from app.dependencies import SessionDep, CurrentUser

router = APIRouter(prefix="/searches", tags=["searches"])

rate_limiter = RateLimiter(
    RateLimitConfig(requests_per_minute=3)
)

## Get all sessions
@router.get("/", response_model=SearchSessionsPublic)
def read_searches(
    session: SessionDep, 
    current_user: CurrentUser, 
    skip: int = 0,
    limit: int = 100
):

    if current_user.is_superuser:
        count_statement = select(func.count()).select_from(SearchSession)
        count = session.exec(count_statement).one()
        statement = select(SearchSession).offset(skip).limit(limit)
        sessions = session.exec(statement).all()
    else:
        count_statement = (
            select(func.count())
            .select_from(SearchSession)
            .where(SearchSession.owner_id == current_user.id)
        )
        count = session.exec(count_statement).one()
        statement = (
            select(SearchSession)
            .where(SearchSession.owner_id == current_user.id)
            .offset(skip)
            .limit(limit)
        )
        sessions = session.exec(statement).all()

    return SearchSessionsPublic(data=sessions, count=count)

@router.get("/{id}", response_model=SearchSessionWithHistoryPublic)
def read_search_by_id(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
) -> Any:
    search_session = session.get(SearchSession, id)

    if not search_session:
        raise HTTPException(status_code=404, detail="Search session not found")

    if search_session.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to access this search session",
        )

    history_statement = (
        select(SearchHistory)
        .where(SearchHistory.session_id == id)
        .where(SearchHistory.owner_id == search_session.owner_id)
        .order_by(SearchHistory.created_at.asc())
    )

    histories = session.exec(history_statement).all()

    return SearchSessionWithHistoryPublic(
        id=search_session.id,
        title=search_session.title,
        owner_id=search_session.owner_id,
        created_at=search_session.created_at,
        updated_at=search_session.updated_at,
        history=histories,
    )    


## Create new search session
@router.post("/", response_model=SearchSessionPublic)
def create_search(
    *, session: SessionDep, current_user: CurrentUser, search_in: SearchSessionCreate
) -> Any:

    search_session = SearchSession.model_validate(
        search_in, update={"owner_id": current_user.id}
    )
    session.add(search_session)
    session.commit()
    session.refresh(search_session)
    return search_session


## Continue Search with Agent (use previous memory)


@router.post("/{id}/chat", response_model=AgentChatResponse)
async def chat_with_agent_on_search(
    *,
    request: Request,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    chat_in: AgentChatRequest,
) -> Any:
    
    client_id = request.client.host
    allowed, error = rate_limiter.check_rate_limit(client_id)
    if not allowed:
        # raise RateLimitError(message=error,limit="REQUEST_LIMIT",case="AI_CALL")
        raise RequestLimitError(message=error,case="AI_CALL")

    search_session = session.get(SearchSession, id)
    if not search_session:
        raise HTTPException(status_code=404, detail="Search session not found")

    if (search_session.owner_id != current_user.id):
        raise HTTPException(
            status_code=403, detail="Not authorized to access this search session"
        )

    if not chat_in.message or not chat_in.message.strip():
        raise HTTPException(
            status_code=400,
            detail="Message is required. It cannot be empty or whitespace",
        )

    reply = await run_agent_on_session(
        session_db=session,
        search_session=search_session,
        current_user_id=current_user.id,
        user_message=chat_in.message,
        cost_tracker=request.app.state.cost_tracker
    )

    return AgentChatResponse(session_id=search_session.id, reply=reply)



@router.delete("/{id}")
def delete_search(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
) -> dict[str, str]:
    search_session = session.get(SearchSession, id)

    if not search_session:
        raise HTTPException(status_code=404, detail="Search session not found")

    if search_session.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to delete this search session",
        )

    session.delete(search_session)
    session.commit()

    return {"message": "Search session deleted successfully"}
