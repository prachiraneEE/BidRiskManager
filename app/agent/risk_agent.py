from langchain_core.messages import HumanMessage
from sqlalchemy.orm import Session

from app.agent.llm import get_llm
from app.agent.tools import (
    calculate_margin,
    check_deadline,
    get_bid_details,
    get_client_history,
)
from app.logger import logger
from app.schemas import RiskReport
from app.services.risk_scorer import calculate_risk_score


def run_risk_assessment(bid_id: int, db: Session) -> RiskReport:
    logger.info("[assess bid=%d] Starting risk assessment", bid_id)

    bid = get_bid_details(db, bid_id)
    logger.info(
        "[assess bid=%d] Fetched bid: %s (value=$%.0f)",
        bid_id, bid["title"], bid["value"],
    )

    client = get_client_history(db, bid["client_id"])
    logger.info(
        "[assess bid=%d] Fetched client: %s (W:%d / L:%d)",
        bid_id, client["name"], client["past_bids_won"], client["past_bids_lost"],
    )

    margin = calculate_margin(bid["value"], bid["estimated_cost"])
    logger.info("[assess bid=%d] Margin: %.1f%%", bid_id, margin["margin_pct"])

    deadline = check_deadline(bid["deadline"])
    logger.info(
        "[assess bid=%d] Deadline: %d days away", bid_id, deadline["days_until"]
    )

    risk = calculate_risk_score(
        margin_pct=margin["margin_pct"],
        days_until_deadline=deadline["days_until"],
        past_bids_lost=client["past_bids_lost"],
    )
    logger.info(
        "[assess bid=%d] Risk score: %d/100 (%s) — reasons: %s",
        bid_id, risk.score, risk.level.value, risk.reasons,
    )

    logger.info("[assess bid=%d] Calling LLM for recommendation...", bid_id)
    llm = get_llm()
    prompt = f"""You are a bid risk analyst. Based on this data, write a 2-3 sentence recommendation.

Bid: {bid['title']} (${bid['value']:,.0f})
Client: {client['name']} ({client['industry']})
Margin: {margin['margin_pct']:.1f}%
Days until deadline: {deadline['days_until']}
Client win/loss record: {client['past_bids_won']}W / {client['past_bids_lost']}L
Risk score: {risk.score}/100 ({risk.level.value})
Risk factors: {', '.join(risk.reasons) if risk.reasons else 'None identified'}

Provide a concise recommendation: should they proceed, proceed with caution, or reconsider?"""

    response = llm.invoke([HumanMessage(content=prompt)])
    logger.info(
        "[assess bid=%d] LLM recommendation received (%d chars)",
        bid_id, len(response.content),
    )

    logger.info(
        "[assess bid=%d] Assessment complete: score=%d level=%s",
        bid_id, risk.score, risk.level.value,
    )

    return RiskReport(
        score=risk.score,
        level=risk.level,
        reasons=risk.reasons,
        recommendation=response.content,
    )
