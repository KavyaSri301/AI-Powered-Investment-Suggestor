import pandas as pd
from fetch_yahoo import (
    fetch_today_90min_data_single_csv,
    fetch_nse_stocks,
    fetch_yahoo_etfs_mfs
)

from prompts import (
    PROFILE_PROMPT, PROFILE_SYSTEM,
    RESEARCH_PROMPT, RESEARCH_SYSTEM,
    RANK_PROMPT, RANK_SYSTEM,
    RECOMMEND_PROMPT, RECOMMEND_SYSTEM,
    FINAL_PROMPT, FINAL_SYSTEM
)

from llm_client import call_llm
class OrchestratorAgent:
    """
    Multi-turn orchestrator that routes queries between profile, research, rank, and recommend agents.
    It also manages a FinalAgent that summarizes or explains responses contextually.
    """

    def __init__(self):
        # Each user_id maintains its own session of facts, outputs, and recommendations
        self.sessions = {}  # user_id -> conversation/session context

    # -----------------------------
    # Session Initialization
    # -----------------------------
    def _init_session(self, user_id):
        if user_id not in self.sessions:
            self.sessions[user_id] = {
                "facts": None,
                "profile": None,
                "research": None,
                "ranked": None,
                "recommendation": None
            }

    # -----------------------------
    # Handle Query (Main Entry Point)
    # -----------------------------
    def handle_query(self, user_id, query):
        """
        Handles user queries sequentially, progressing through the agents
        and calling the final summarization agent after each step.
        """
        self._init_session(user_id)
        session = self.sessions[user_id]

        # STEP 1 → PROFILE AGENT
        if not session["profile"]:
            session["facts"] = query
            profile_json = call_llm(PROFILE_SYSTEM, PROFILE_PROMPT.format(facts=query))
            session["profile"] = profile_json
            return self._final_agent(session, "ProfileAgent", profile_json, query)

        # STEP 2 → RESEARCH AGENT
        if not session["research"]:
            tickers = ["AAPL", "MSFT", "GOOG"]
            market_data = fetch_today_90min_data_single_csv(tickers)
            research_json = call_llm(
                RESEARCH_SYSTEM,
                RESEARCH_PROMPT.format(
                    profile=session["profile"],
                    market_data=market_data.to_csv(index=False)
                ),
            )
            session["research"] = research_json
            return self._final_agent(session, "ResearchAgent", research_json, query)

        # STEP 3 → RANK AGENT
        if not session["ranked"]:
            nse_tickers = fetch_nse_stocks()
            yahoo_tickers = fetch_yahoo_etfs_mfs()
            all_tickers = nse_tickers + yahoo_tickers
            combined_data = fetch_today_90min_data_single_csv(
                all_tickers, top_n=20, output_file="intraday_all_tickers.csv"
            )

            ranked_json = call_llm(
                RANK_SYSTEM,
                RANK_PROMPT.format(
                    profile=session["profile"],
                    research=combined_data.to_csv(index=False)
                ),
            )
            session["ranked"] = ranked_json
            return self._final_agent(session, "RankAgent", ranked_json, query)

        # STEP 4 → RECOMMEND AGENT
        if not session["recommendation"]:
            recommendation_json = call_llm(
                RECOMMEND_SYSTEM,
                RECOMMEND_PROMPT.format(
                    profile=session["profile"],
                    ranked=session["ranked"]
                ),
            )
            session["recommendation"] = recommendation_json
            return self._final_agent(session, "RecommendAgent", recommendation_json, query)

        # STEP 5 → COMPLETED SESSION / FOLLOW-UP QUERIES
        # If all agents have already produced outputs, respond contextually
        return self._final_agent(session, "Completed", session["recommendation"], query)

    # -----------------------------
    # FINAL AGENT — Contextual Summarizer / Explainer
    # -----------------------------
    def _final_agent(self, session, current_agent, current_response, query=None):
        """
        Produces a natural, human-readable response considering all past context.
        Handles follow-up questions (like 'What is Apple?') intelligently.
        """

        # Build conversation history context
        history_text = ""
        if session.get("facts"):
            history_text += f"User initial facts: {session['facts']}\n"
        if session.get("profile"):
            history_text += f"ProfileAgent Output: {session['profile']}\n"
        if session.get("research"):
            history_text += f"ResearchAgent Output: {session['research']}\n"
        if session.get("ranked"):
            history_text += f"RankAgent Output: {session['ranked']}\n"
        if session.get("recommendation"):
            history_text += f"RecommendAgent Output: {session['recommendation']}\n"

        # Build prompt dynamically
        final_prompt = FINAL_PROMPT.format(
            history=history_text,
            query=query or "",
            facts=session.get("facts"),
            profile=session.get("profile"),
            research=session.get("research"),
            ranked=session.get("ranked"),
            recommendation=session.get("recommendation")
        )

        # Generate contextual summary/explanation
        summary_text = call_llm(FINAL_SYSTEM, final_prompt)

        return {
            "agent": current_agent,
            "response": summary_text
        }
