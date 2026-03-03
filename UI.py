import streamlit as st

# ---------------- Page Config ----------------
st.set_page_config(
    page_title="Intelligent CAD Search Bot",
    page_icon="🛠️",
    layout="centered"
)

# ---------------- CSS ----------------
st.markdown(
    """
    <style>
    /* App background */
    .stApp {
        background: linear-gradient(180deg, #eaf2ff 0%, #f5f9ff 100%);
    }

    /* Reduce top padding safely */
    .block-container {
        padding-top: 2rem;
    }

    /* Card styling */
    .card {
        background: white;
        padding: 2.5rem 3rem;
        border-radius: 16px;
        box-shadow: 0 14px 40px rgba(0,0,0,0.08);
        max-width: 900px;
        margin: auto;
    }

    .title {
        text-align: center;
        font-size: 2.4rem;
        font-weight: 700;
        margin-bottom: 0.3rem;
    }

    .subtitle {
        text-align: center;
        color: #6b7280;
        margin-bottom: 2rem;
    }

    .section-title {
        font-weight: 600;
        margin-top: 1.6rem;
        margin-bottom: 0.4rem;
    }

    input {
        height: 3rem !important;
        border-radius: 8px !important;
    }

    div.stButton > button {
        width: 100%;
        height: 3rem;
        border-radius: 8px;
        margin-top: 1.2rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ---------------- STREAMLIT CONTAINER ----------------
with st.container():

    st.markdown("<div class='card'>", unsafe_allow_html=True)

    st.markdown("<div class='title'>Intelligent CAD Search Bot</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='subtitle'>Search CAD drawings and 3D models using natural language, numbers, or shapes</div>",
        unsafe_allow_html=True
    )

    st.markdown("<div class='section-title'>Enter your search query</div>", unsafe_allow_html=True)
    query = st.text_input(
        "",
        placeholder="e.g., tank of 5000-liter capacity or heat exchanger 120 m²"
    )
    st.caption("Supports: text descriptions, numerical specs, component types, geometric features")

    st.markdown("<div class='section-title'>Or upload a reference CAD file (optional)</div>", unsafe_allow_html=True)
    cad_file = st.file_uploader(
        "Upload CAD file",
        type=["dwg", "dxf", "step", "iges"]
    )

    if st.button("Search CAD Files"):
        if query or cad_file:
            st.success("Searching CAD files...")
        else:
            st.error("Please enter a query or upload a CAD file.")

    st.markdown("---")
    st.markdown("<div class='section-title'>Quick Search Examples</div>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.button("tank of 5000-liter capacity")
        st.button("flanged elbow 90 degree")
    with c2:
        st.button("heat exchanger with 120 m² area")
        st.button("pressure vessel stainless steel")

    st.markdown("</div>", unsafe_allow_html=True)
