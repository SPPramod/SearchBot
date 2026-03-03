import streamlit as st
import os
import tempfile
from PIL import Image
from google import genai
from supabase import create_client
import mimetypes

# ---------------------------
# CONFIG
# ---------------------------
SUPABASE_URL = "https://nhuwmvuxihqruajlycvm.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5odXdtdnV4aWhxcnVhamx5Y3ZtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjkxMDAyNjcsImV4cCI6MjA4NDY3NjI2N30.56S7hlbs1F8DCyzSfCKoPl-HilbmQsR2h-vi9SVTW_0"

GEMINI_API_KEY = "AIzaSyBYNFa6GM-5Qve7a5KWkKmilCi8tYAD3xk"

SUPPORTED_IMAGE_TYPES = ["image/png", "image/jpeg", "image/webp"]
SUPPORTED_CAD_TYPES = [
    "model/stl",
    "model/step",
    "model/iges",
    "model/obj",
    "application/octet-stream"
]

MODEL_NAME = "gemini-1.5-flash"  # ✅ supported

# ---------------------------
# INIT CLIENTS
# ---------------------------
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

client = genai.Client(api_key=GEMINI_API_KEY)

# ---------------------------
# STREAMLIT UI
# ---------------------------
st.set_page_config(
    page_title="Intelligent CAD Analyzer",
    page_icon="🛠️",
    layout="centered"
)

st.title("🛠️ Intelligent CAD Analyzer")
st.caption("Analyze CAD files and images using Gemini AI")

uploaded_file = st.file_uploader(
    "Upload image or CAD file",
    type=["png", "jpg", "jpeg", "webp", "stl", "step", "iges", "obj"]
)

# ---------------------------
# GEMINI ANALYSIS FUNCTIONS
# ---------------------------
def analyze_with_gemini_image(image: Image.Image):
    prompt = """
    You are an expert mechanical engineer.

    Analyze the given image and identify:
    - Component type
    - Engineering category
    - Likely application
    - Key attributes (angle, shape, assembly type if visible)

    Return output strictly in JSON with keys:
    component, category, attributes, description
    """

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[prompt, image]
    )

    return response.text


def analyze_cad_placeholder(filename: str):
    prompt = f"""
    A CAD file named "{filename}" was uploaded.

    Based on the filename and typical industrial CAD usage,
    infer:
    - Component type
    - Category
    - Engineering description

    Respond ONLY with valid JSON.
    """

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    return response.text


# ---------------------------
# PROCESS FILE
# ---------------------------
if uploaded_file:
    mime_type, _ = mimetypes.guess_type(uploaded_file.name)

    st.write("📄 File:", uploaded_file.name)
    st.write("📎 Type:", mime_type)

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(uploaded_file.read())
        temp_path = tmp.name

    # IMAGE FILE
    if mime_type in SUPPORTED_IMAGE_TYPES:
        image = Image.open(temp_path).convert("RGB")
        st.image(image, caption="Uploaded Image", use_column_width=True)

        with st.spinner("Analyzing image with Gemini..."):
            result = analyze_with_gemini_image(image)

    # CAD FILE
    else:
        st.info("CAD file detected (visual rendering not enabled yet).")

        with st.spinner("Analyzing CAD metadata with Gemini..."):
            result = analyze_cad_placeholder(uploaded_file.name)

    st.subheader("🔍 AI Analysis Result")
    st.code(result, language="json")

    # ---------------------------
    # STORE IN SUPABASE
    # ---------------------------
    if st.button("Save to Database"):
        payload = {
            "filename": uploaded_file.name,
            "analysis": result
        }
        supabase.table("cad_metadata").insert(payload).execute()
        st.success("Saved to Supabase successfully!")
