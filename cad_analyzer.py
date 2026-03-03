import os
os.environ["TRIMESH_NO_OPENGL"] = "1"

import streamlit as st
import trimesh
import tempfile
import plotly.graph_objects as go
from supabase import create_client
from datetime import datetime
import math

# -----------------------------
# CONFIG
# -----------------------------

# -----------------------------
# INIT SUPABASE
# -----------------------------
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# -----------------------------
# STREAMLIT CONFIG
# -----------------------------
st.set_page_config(
    page_title="CAD File Analyzer",
    layout="centered"
)

st.title("🧩 CAD File Analyzer")
st.caption("OpenGL-free • Geometry-aware • Supabase enabled")

# -----------------------------
# Upload
# -----------------------------
uploaded_file = st.file_uploader(
    "Upload STL or OBJ file",
    type=["stl", "obj"]
)

# -----------------------------
# CAD Analysis
# -----------------------------
def analyze_cad(path):
    mesh = trimesh.load_mesh(
        path,
        force="mesh",
        process=False
    )

    if mesh.is_empty:
        raise ValueError("Invalid CAD file")

    bbox = mesh.bounding_box.extents
    length, width, height = map(float, bbox)

    return {
        "mesh": mesh,
        "length": length,
        "width": width,
        "height": height,
        "volume": float(mesh.volume),
        "surface_area": float(mesh.area)
    }

# -----------------------------
# DESCRIPTION GENERATOR
# -----------------------------
def generate_description(filename, dims, volume, surface_area):
    l, w, h = dims
    dims_sorted = sorted([l, w, h], reverse=True)

    aspect_ratio = dims_sorted[0] / max(dims_sorted[2], 1e-6)
    solidity = volume / max(surface_area, 1e-6)

    if aspect_ratio > 4:
        shape_desc = "elongated"
    elif aspect_ratio < 1.5:
        shape_desc = "compact"
    else:
        shape_desc = "moderately proportioned"

    if solidity > 5:
        mass_desc = "solid"
    else:
        mass_desc = "lightweight or hollow"

    file_type = filename.split(".")[-1].upper()

    return (
        f"A {mass_desc}, {shape_desc} 3D mechanical component "
        f"modeled as a {file_type} CAD file. "
        f"The geometry suggests a functional industrial part "
        f"such as a bracket, housing, or structural element."
    )

# -----------------------------
# 3D Plot
# -----------------------------
def plot_mesh(mesh):
    v = mesh.vertices
    f = mesh.faces

    fig = go.Figure(
        data=[
            go.Mesh3d(
                x=v[:, 0],
                y=v[:, 1],
                z=v[:, 2],
                i=f[:, 0],
                j=f[:, 1],
                k=f[:, 2],
                opacity=0.6
            )
        ]
    )

    fig.update_layout(
        scene=dict(aspectmode="data"),
        margin=dict(l=0, r=0, t=0, b=0)
    )

    return fig

# -----------------------------
# MAIN
# -----------------------------
if uploaded_file:
    try:
        with st.spinner("Analyzing CAD file..."):
            suffix = os.path.splitext(uploaded_file.name)[1].lower()

            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded_file.read())
                temp_path = tmp.name

            result = analyze_cad(temp_path)

            description = generate_description(
                uploaded_file.name,
                (result["length"], result["width"], result["height"]),
                result["volume"],
                result["surface_area"]
            )

        st.success("CAD file analyzed successfully ✅")

        # -----------------------------
        # Display Metrics
        # -----------------------------
        st.subheader("📐 Dimensions (mm)")
        c1, c2, c3 = st.columns(3)
        c1.metric("Length", f"{result['length']:.2f}")
        c2.metric("Width", f"{result['width']:.2f}")
        c3.metric("Height", f"{result['height']:.2f}")

        st.subheader("📊 Geometry")
        c4, c5 = st.columns(2)
        c4.metric("Volume (mm³)", f"{result['volume']:.2f}")
        c5.metric("Surface Area (mm²)", f"{result['surface_area']:.2f}")

        st.subheader("📝 Auto-generated Description")
        st.write(description)

        st.subheader("🧱 3D Preview")
        st.plotly_chart(plot_mesh(result["mesh"]), use_container_width=True)

        # -----------------------------
        # SAVE TO SUPABASE
        # -----------------------------
        if st.button("💾 Save to Supabase"):
            payload = {
                "filename": uploaded_file.name,
                "file_type": suffix.replace(".", ""),
                "length_mm": result["length"],
                "width_mm": result["width"],
                "height_mm": result["height"],
                "volume_mm3": result["volume"],
                "surface_area_mm2": result["surface_area"],
                "description": description,
                "created_at": datetime.utcnow().isoformat()
            }

            supabase.table("cad_meta").insert(payload).execute()
            st.success("Saved to Supabase successfully 🚀")

    except Exception as e:
        st.error(f"❌ Error analyzing CAD file: {e}")

    finally:
        if "temp_path" in locals() and os.path.exists(temp_path):
            os.remove(temp_path)

st.markdown("---")
st.caption("Geometry-driven description • No AI • Production-safe")
