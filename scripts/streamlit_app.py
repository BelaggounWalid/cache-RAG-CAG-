"""Q&A UI for the SAPA catalog.

Run: streamlit run scripts/streamlit_app.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import streamlit as st
from sapa_rag.rag.qa import answer
from sapa_rag.config import settings

st.set_page_config(page_title="SAPA Perf70 GTI — Q&A", page_icon="🚪", layout="wide")
st.title("Catalogue SAPA Performance 70 GTI/GTI+ — Assistant")

with st.sidebar:
    st.markdown("**Index**")
    qdrant_path = settings.output_dir / "qdrant_local"
    st.caption(f"`{qdrant_path}`")
    st.caption(f"Indexé: {'oui' if qdrant_path.exists() else 'non'}")
    top_k = st.slider("top_k", 3, 20, 8)

q = st.text_input(
    "Question",
    placeholder="Ex: Quel est le Ud d'une porte 1 vantail 1.06×2.18 avec isolation we ?",
)

if q:
    with st.spinner("Recherche + génération..."):
        try:
            res = answer(q, top_k=top_k)
        except Exception as e:
            st.error(f"Erreur: {e}")
            st.stop()

    st.markdown("### Réponse")
    st.markdown(res["answer"])

    with st.expander("Routing"):
        st.json(res["routing"])

    st.markdown("### Citations")
    for c in res["citations"]:
        st.markdown(
            f"- **p.{c['page']}** — {c.get('section_l1') or '?'} > {c.get('section_l2') or '?'} "
            f"(score {c.get('score'):.3f})"
        )
