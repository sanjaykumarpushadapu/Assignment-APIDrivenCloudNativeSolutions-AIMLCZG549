import streamlit as st

st.set_page_config(page_title="Diabetes Risk Pipeline", layout="wide")
st.title("Diabetes Risk Screening")
st.caption("Pipeline activity dashboard skeleton")

left, right = st.columns(2)
with left:
    st.metric("Latest run", "Not started")
with right:
    st.metric("Processed rows", "-")

st.info("Connect this view to the selected cloud platform's run history and EDA outputs.")