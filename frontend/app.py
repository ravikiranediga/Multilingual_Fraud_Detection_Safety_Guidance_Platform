import streamlit as st
import requests
import pandas as pd
import os

# Point at the deployed Render API in production, localhost in development
API_URL = os.getenv(
    "API_URL",
    "http://127.0.0.1:8000"
).rstrip("/")

st.set_page_config(
    page_title="ScamShield AI",
    page_icon="🛡️",
    layout="wide"
)

st.markdown("""
<style>
.block-container {padding-top: 2rem; padding-bottom: 2rem;}
.stButton > button {
    width: 100%;
    height: 50px;
    border-radius: 10px;
    font-weight: bold;
}
.risk-box {
    background-color:#1f2937;
    padding:20px;
    border-radius:12px;
    border-left:6px solid #3b82f6;
}
.flag-box {
    background-color:#450a0a;
    padding:20px;
    border-radius:12px;
    border-left:6px solid #ef4444;
}
.advice-box {
    background-color:#052e16;
    padding:20px;
    border-radius:12px;
    border-left:6px solid #22c55e;
}
.explanation-box {
    background-color:#111827;
    padding:25px;
    border-radius:12px;
    border-left:6px solid #10b981;
    margin-top:20px;
}
</style>
""", unsafe_allow_html=True)

st.title("🛡️ ScamShield AI")
st.subheader("Multilingual Fraud Detection & Safety Guidance Platform")

with st.sidebar:
    st.header("System Status")

    try:
        health = requests.get(
            f"{API_URL}/health",
            timeout=10
        )

        if health.status_code == 200:
            st.success("API connected")
            st.caption(API_URL)
        else:
            st.error(
                f"API returned {health.status_code}"
            )

    except requests.exceptions.RequestException:
        st.error("API unreachable")
        st.warning(
            "The backend is not responding. "
            "On Render free tier the service sleeps after "
            "15 minutes idle and takes a few minutes to wake."
        )

tab1, tab2, tab3, tab4 = st.tabs(
    ["Analyze Text", "Analyze Image", "History", "Analytics"]
)

with tab1:

    message = st.text_area(
        "Enter suspicious message",
        height=180
    )

    response_language = st.selectbox(
        "Response Language",
        ["English", "Hindi", "Telugu"]
    )

    if st.button("Analyze Scam"):

        if not message.strip():
            st.warning("Enter a message first.")
            st.stop()

        payload = {
            "message": message,
            "response_language": response_language
        }

        with st.spinner("Analyzing..."):
            try:
                response = requests.post(
                    f"{API_URL}/analyze-text",
                    json=payload,
                    timeout=180
                )
            except requests.exceptions.RequestException:
                st.error("Could not reach the API.")
                st.stop()

        if response.status_code == 200:

            result = response.json()

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown(f"""
                <div class="risk-box">
                <h3>📊 Risk Analysis</h3>
                <b>Risk Score:</b> {result["risk_score"]}<br>
                <b>Risk Level:</b> {result["risk_level"]}<br>
                <b>Category:</b> {result["category"]}
                </div>
                """, unsafe_allow_html=True)

            with col2:
                flags_html = "<br>".join(
                    [f"🚩 {flag}" for flag in result["flags"]]
                )

                st.markdown(f"""
                <div class="flag-box">
                <h3>⚠️ Flags</h3>
                {flags_html}
                </div>
                """, unsafe_allow_html=True)

            with col3:
                st.markdown(f"""
                <div class="advice-box">
                <h3>🛡️ Safety Advice</h3>
                {result["advice"]}
                </div>
                """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="explanation-box">
            <h3>🤖 AI Explanation</h3>
            {result["explanation"].replace(chr(10), "<br>")}
            </div>
            """, unsafe_allow_html=True)

        else:
            st.error("Failed to analyze message.")

with tab2:

    uploaded_file = st.file_uploader(
        "Upload Scam Screenshot",
        type=["png", "jpg", "jpeg"]
    )

    image_language = st.selectbox(
        "Response Language",
        ["English", "Hindi", "Telugu"],
        key="image_language"
    )

    if uploaded_file is not None:

        st.image(
            uploaded_file,
            caption="Uploaded Image",
            use_container_width=True
        )

        if st.button("Analyze Image"):

            files = {
                "file": (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    uploaded_file.type
                )
            }

            with st.spinner("Extracting text and analyzing..."):
                try:
                    response = requests.post(
                        f"{API_URL}/analyze-image",
                        files=files,
                        params={
                            "response_language": image_language
                        },
                        timeout=180
                    )
                except requests.exceptions.RequestException:
                    st.error("Could not reach the API.")
                    st.stop()

            if response.status_code == 200:

                result = response.json()

                st.subheader("Extracted Text")
                st.write(result["extracted_text"])

                analysis = result["analysis"]

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.markdown(f"""
                    <div class="risk-box">
                    <h3>📊 Risk Analysis</h3>
                    <b>Risk Score:</b> {analysis["risk_score"]}<br>
                    <b>Risk Level:</b> {analysis["risk_level"]}<br>
                    <b>Category:</b> {analysis["category"]}
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    flags_html = "<br>".join(
                        [f"🚩 {flag}" for flag in analysis["flags"]]
                    )

                    st.markdown(f"""
                    <div class="flag-box">
                    <h3>⚠️ Flags</h3>
                    {flags_html}
                    </div>
                    """, unsafe_allow_html=True)

                with col3:
                    st.markdown(f"""
                    <div class="advice-box">
                    <h3>🛡️ Safety Advice</h3>
                    {analysis["advice"]}
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown(f"""
                <div class="explanation-box">
                <h3>🤖 AI Explanation</h3>
                {analysis["explanation"].replace(chr(10), "<br>")}
                </div>
                """, unsafe_allow_html=True)

            else:
                st.error("Failed to analyze image.")

with tab3:

    if st.button("Load History"):

        response = requests.get(f"{API_URL}/history")

        if response.status_code == 200:
            st.dataframe(
                response.json(),
                use_container_width=True
            )
        else:
            st.error("Failed to load history.")

with tab4:

    if st.button("Load Analytics"):

        history_response = requests.get(
            f"{API_URL}/history"
        )

        if history_response.status_code == 200:

            df = pd.DataFrame(
                history_response.json()
            )

            if not df.empty:

                col1, col2, col3 = st.columns(3)

                col1.metric(
                    "Total Analyses",
                    len(df)
                )

                col2.metric(
                    "High Risk",
                    len(
                        df[df["risk_level"] == "High"]
                    )
                )

                col3.metric(
                    "Medium Risk",
                    len(
                        df[df["risk_level"] == "Medium"]
                    )
                )

                st.subheader("Scam Categories")
                st.bar_chart(
                    df["category"].value_counts()
                )

                st.subheader("Risk Distribution")
                st.bar_chart(
                    df["risk_level"].value_counts()
                )

                st.subheader("Recent Analyses")
                st.dataframe(
                    df,
                    use_container_width=True
                )

            else:
                st.warning("No data available.")
