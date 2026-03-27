import os

import pandas as pd
import streamlit as st

from src.agent import BIAgent
from src.utils import default_db_path, ensure_sample_database

st.set_page_config(page_title="BI Insight Agent", layout="wide")

st.title("BI Insight Agent")
st.caption("Natural language → SQL (SQLite) → results and a short insight.")

with st.sidebar:
    st.subheader("Settings")
    db_default = default_db_path()
    db_path = st.text_input("SQLite database path", value=db_default)
    if st.button("Create demo DB if missing"):
        ensure_sample_database(db_path)
        st.success(f"Ensured database at: {db_path}")
    st.text_input(
        "OpenAI API key",
        type="password",
        value=os.environ.get("OPENAI_API_KEY", ""),
        key="openai_key_input",
        help="Set OPENAI_API_KEY in .env or paste here for this session.",
    )
    if st.session_state.get("openai_key_input"):
        os.environ["OPENAI_API_KEY"] = st.session_state.openai_key_input
    model = st.text_input("Model", value=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"))
    if model:
        os.environ["OPENAI_MODEL"] = model
    with_insight = st.checkbox("Generate natural-language insight", value=True)

ensure_sample_database(db_path)

question = st.text_area("Your question", placeholder="e.g. What was total sales by region?")

if st.button("Run", type="primary") and question.strip():
    if not os.environ.get("GOOGLE_API_KEY"):
        st.error("Set GOOGLE_API_KEY in the sidebar or in a .env file.")
    else:
        with st.spinner("Thinking…"):
            agent = BIAgent(db_path)
            out = agent.ask(question.strip(), with_insight=with_insight)

        if out.get("error") and not out.get("ok"):
            st.error(out["error"])
            if out.get("sql"):
                st.code(out["sql"], language="sql")
        else:
            if out.get("sql"):
                st.subheader("SQL")
                st.code(out["sql"], language="sql")
            if out.get("insight"):
                st.subheader("Insight")
                st.write(out["insight"])
            rows = out.get("rows")
            if rows is not None:
                st.subheader("Results")
                if rows:
                    st.dataframe(pd.DataFrame(rows), use_container_width=True)
                else:
                    st.info("No rows returned.")
