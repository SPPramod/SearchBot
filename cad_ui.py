import os
os.environ["TRIMESH_NO_OPENGL"] = "1"

import streamlit as st
import trimesh
import tempfile
import plotly.graph_objects as go
from supabase import create_client
from datetime import datetime
from PIL import Image
from sentence_transformers import SentenceTransformer, util
import numpy as np

SUPABASE_URL = "https://nhuwmvuxihqruajlycvm.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5odXdtdnV4aWhxcnVhamx5Y3ZtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjkxMDAyNjcsImV4cCI6MjA4NDY3NjI2N30.56S7hlbs1F8DCyzSfCKoPl-HilbmQsR2h-vi9SVTW_0"  # Replace with your key

SUPPORTED_MESH = ["stl", "obj"]
SUPPORTED_STEP = ["step", "stp"]
SUPPORTED_IMAGE = ["png", "jpg", "jpeg"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
st.set_page_config(page_title="Intelligent CAD Search Bot", page_icon="🛠️", layout="centered")

model = SentenceTransformer('all-MiniLM-L6-v2')

st.markdown("""
<style>
.stApp { background: linear-gradient(180deg, #eaf2ff 0%, #f5f9ff 100%); }
.block-container { padding-top: 2rem; }
.card { background: white; padding: 2.5rem 3rem; border-radius: 16px; box-shadow: 0 14px 40px rgba(0,0,0,0.08); max-width: 900px; margin: auto; }
.title { text-align: center; font-size: 2.4rem; font-weight: 700; margin-bottom: 0.3rem; }
.subtitle { text-align: center; color: #6b7280; margin-bottom: 2rem; }
.section-title { font-weight: 600; margin-top: 1.6rem; margin-bottom: 0.4rem; }
input { height: 3rem !important; border-radius: 8px !important; }
div.stButton > button { width: 100%; height: 3rem; border-radius: 8px; margin-top: 1.2rem; }
</style>
""", unsafe_allow_html=True)

def analyze_mesh(path):
    mesh = trimesh.load_mesh(path, force="mesh", process=False)
    if mesh.is_empty:
        raise ValueError("Invalid mesh")
    l, w, h = map(float, mesh.bounding_box.extents)
    return {"mesh": mesh, "length": l, "width": w, "height": h,
            "volume": float(mesh.volume), "surface_area": float(mesh.area)}

def generate_geometry_description(l, w, h, volume, area, ext):
    ratio = max(l, w, h) / max(min(l, w, h), 1e-6)
    shape = "elongated" if ratio > 4 else "compact" if ratio < 1.5 else "balanced"
    mass = "solid" if volume / max(area, 1e-6) > 5 else "lightweight"
    return (f"A {mass}, {shape} mechanical component represented as a {ext.upper()} CAD file. "
            "The geometry suggests a functional industrial part such as a bracket, housing, or mount.")

def generate_step_description(filename):
    return (f"A parametric CAD model stored as a STEP file. "
            f"The file '{filename}' likely represents a precise engineering component "
            "intended for manufacturing or assembly workflows.")

def generate_image_description(filename):
    return (f"An engineering-related image file '{filename}'. "
            "The image likely represents a CAD render, technical illustration, or product visualization.")

def plot_mesh(mesh):
    v, f = mesh.vertices, mesh.faces
    fig = go.Figure(data=[go.Mesh3d(x=v[:,0], y=v[:,1], z=v[:,2],
                                    i=f[:,0], j=f[:,1], k=f[:,2], opacity=0.6)])
    fig.update_layout(scene=dict(aspectmode="data"), margin=dict(l=0,r=0,t=0,b=0))
    return fig

def embed_text(texts):
    return model.encode(texts, convert_to_tensor=True)

def search_cad_semantic(query, top_k=10):
    response = supabase.table("cad_meta").select("*").execute()
    data = response.data
    if not data:
        return []

    desc_list = [row['description'] for row in data]
    desc_embeddings = embed_text(desc_list)
    query_embedding = embed_text([query])

    cos_scores = util.cos_sim(query_embedding, desc_embeddings)[0].cpu().numpy()
    sorted_indices = np.argsort(-cos_scores)

    results = []
    for idx in sorted_indices[:top_k]:
        row = data[idx]
        row['score'] = float(cos_scores[idx])
        
        image_path = row.get('image_path')
        if image_path and os.path.exists(image_path):
            row['local_image'] = image_path
        else:
            row['local_image'] = None
        results.append(row)
    return results

with st.container():
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='title'>Intelligent CAD Search Bot</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Search CAD drawings and 3D models using natural language, numbers, or shapes</div>", unsafe_allow_html=True)

    st.markdown("<div class='section-title'>Enter your search query</div>", unsafe_allow_html=True)
    query = st.text_input("Search query", placeholder="e.g., tank of 5000-liter capacity or heat exchanger 120 m²", label_visibility="collapsed")
    st.caption("Supports: text descriptions, numerical specs, component types, geometric features")

    st.markdown("<div class='section-title'>Or upload a reference CAD file (optional)</div>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload CAD or image file", type=SUPPORTED_MESH + SUPPORTED_STEP + SUPPORTED_IMAGE)

    if st.button("🔍 Search CAD Files"):
        if query or uploaded_file:
            st.info("Searching CAD files...")

            if query:
                results = search_cad_semantic(query)
                st.subheader("Search Results")
                if results:
                    for r in results:
                        st.write(f"**{r['filename']}** ({r['file_type']}) - {r['description']} (score: {r['score']:.2f})")
                        if r.get('local_image'):
                            try:
                                img = Image.open(r['local_image'])
                                st.image(img, width=300)
                            except Exception as e:
                                st.warning(f"Could not open image: {e}")
                        else:
                            st.info("No local image available")
                else:
                    st.warning("No results found.")


            if uploaded_file:
                ext = uploaded_file.name.split(".")[-1].lower()
                with tempfile.NamedTemporaryFile(delete=False, suffix="."+ext) as tmp:
                    tmp.write(uploaded_file.read())
                    path = tmp.name

                try:
                    if ext in SUPPORTED_MESH:
                        st.info("🔍 Mesh CAD detected")
                        result = analyze_mesh(path)
                        desc = generate_geometry_description(result["length"], result["width"], result["height"],
                                                            result["volume"], result["surface_area"], ext)

                        st.subheader("📐 Dimensions (mm)")
                        c1,c2,c3 = st.columns(3)
                        c1.metric("Length", f"{result['length']:.2f}")
                        c2.metric("Width", f"{result['width']:.2f}")
                        c3.metric("Height", f"{result['height']:.2f}")

                        st.subheader("📊 Geometry")
                        c4,c5 = st.columns(2)
                        c4.metric("Volume", f"{result['volume']:.2f}")
                        c5.metric("Surface Area", f"{result['surface_area']:.2f}")

                        st.subheader("🧱 3D Preview")
                        st.plotly_chart(plot_mesh(result["mesh"]), use_container_width=True)

                    elif ext in SUPPORTED_STEP:
                        st.info("📐 STEP file detected (metadata-only)")
                        desc = generate_step_description(uploaded_file.name)

                    else:
                        st.info("🖼️ Image detected")
                        img = Image.open(path)
                        st.image(img, use_column_width=True)
                        desc = generate_image_description(uploaded_file.name)

                    st.subheader("📝 Description")
                    st.write(desc)

                    if st.button("💾 Save to Supabase"):
                        supabase.table("cad_meta").insert({
                            "filename": uploaded_file.name,
                            "file_type": ext,
                            "description": desc,
                            "image_path": path,
                            "created_at": datetime.utcnow().isoformat()
                        }).execute()
                        st.success("Saved successfully 🚀")

                except Exception as e:
                    st.error(f"❌ {e}")

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
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")
st.caption("Safe • Deterministic • Industrial-grade")
