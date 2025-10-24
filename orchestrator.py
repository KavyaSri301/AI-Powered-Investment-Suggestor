# orchestrator.py
import pandas as pd
from fetch_yahoo import fetch_today_90min_data_single_csv, fetch_nse_stocks, fetch_yahoo_etfs_mfs
from prompts import (
    PROFILE_PROMPT, PROFILE_SYSTEM,
    RESEARCH_PROMPT, RESEARCH_SYSTEM,
    RANK_PROMPT, RANK_SYSTEM,
    RECOMMEND_PROMPT, RECOMMEND_SYSTEM,
    ORCHESTRATOR_PROMPT, ORCHESTRATOR_SYSTEM
)
from llm_client import call_llm
from fetch_yahoo import fetch_today_90min_data_single_csv

class OrchestratorAgent:
    """
    Routes queries to agents based on session context.
    """
    def __init__(self):
        self.sessions = {}  # user_id -> conversation context

    def _init_session(self, user_id):
        if user_id not in self.sessions:
            self.sessions[user_id] = {
                "facts": None,
                "profile": None,
                "research": None,
                "ranked": None,
                "recommendation": None
            }

    def handle_query(self, user_id, query):
        self._init_session(user_id)
        session = self.sessions[user_id]

        # Step 1: ProfileAgent
        if not session["profile"]:
            facts = query
            session["facts"] = facts
            profile_json = call_llm(PROFILE_SYSTEM, PROFILE_PROMPT.format(facts=facts))
            session["profile"] = profile_json
            return {"agent": "ProfileAgent", "response": profile_json}

        # Step 2: ResearchAgent
        if not session["research"]:
            # Fetch market data
            tickers = ["AAPL", "MSFT", "GOOG"]  # example top tickers
            market_data = fetch_today_90min_data_single_csv(tickers)
            research_json = call_llm(RESEARCH_SYSTEM, RESEARCH_PROMPT.format(
                profile=session["profile"],
                market_data=market_data.to_csv(index=False)
            ))
            session["research"] = research_json
            return {"agent": "ResearchAgent", "response": research_json}

        # Step 3: RankAgent
        if not session["ranked"]:
            nse_tickers = fetch_nse_stocks()
            yahoo_tickers = fetch_yahoo_etfs_mfs()
            all_tickers = nse_tickers + yahoo_tickers
            combined_data = fetch_today_90min_data_single_csv(all_tickers, top_n=20, output_file="intraday_all_tickers.csv")

            ranked_json = call_llm(RANK_SYSTEM, RANK_PROMPT.format(
                profile=session["profile"],
                research=combined_data.to_csv(index=False)
            ))
            session["ranked"] = ranked_json
            return {"agent": "RankAgent", "response": ranked_json}

        # Step 4: RecommendAgent
        if not session["recommendation"]:
            recommendation_json = call_llm(RECOMMEND_SYSTEM, RECOMMEND_PROMPT.format(
                profile=session["profile"],
                ranked=session["ranked"]
            ))
            session["recommendation"] = recommendation_json
            return {"agent": "RecommendAgent", "response": recommendation_json}

        # If all steps done
        return {"agent": "Completed", "response": session["recommendation"]}
