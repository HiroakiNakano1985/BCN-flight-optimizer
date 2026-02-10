import streamlit as st

st.title("Barcelona Flight Optimizer")

st.subheader("UC1: Search flights arriving in Barcelona")

date = st.date_input("Arrival date")
if st.button("Search"):
    st.write("Searching flights for:", date)