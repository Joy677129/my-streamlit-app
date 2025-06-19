import streamlit as st
import matplotlib.pyplot as plt
from matplotlib_venn import venn2, venn3
import re
import itertools
import os

# --- Configuration: Hardcoded Videos ---
# Add your videos here with their file paths (relative to app) and display titles
VIDEO_LIST = [
    {"path": "videos/a(intS)b.mp4", "title": "n(A∪B) = n(A) + n(B) - n(A∩B)"},
    {"path": "videos/aub_vid.mp4", "title": "A∩B"},
]

# --- Streamlit App: Set Operations & Video Viewer ---
st.set_page_config(
    page_title="Set Operations & Videos",
    layout="wide",
    initial_sidebar_state="expanded",  # ensure sidebar is visible by default
)
st.title("🔁 Interactive Set Operations")

# --- Helper Functions ---
@st.cache_data
def parse_element(x: str):
    """Parse a single element: strip whitespace, try to convert to int, else keep as string."""
    x_str = x.strip()
    if x_str == "":
        return None
    try:
        return int(x_str)
    except ValueError:
        return x_str

@st.cache_data
def parse_set(text: str):
    """Parse comma-separated elements into a Python set."""
    result = set()
    for part in text.split(','):
        el = parse_element(part)
        if el is not None:
            result.add(el)
    return result

@st.cache_data
def parse_universal(text: str):
    """Parse universal set input: numeric range 'start-end' or comma-separated list."""
    txt = text.strip()
    range_match = re.fullmatch(r"\s*([-]?\d+)\s*-\s*([-]?\d+)\s*", txt)
    if range_match:
        start, end = int(range_match.group(1)), int(range_match.group(2))
        if start <= end:
            return set(range(start, end+1))
        else:
            return set(range(end, start+1))
    return parse_set(txt)

@st.cache_data
def sort_result(s: set):
    """Sort a set for consistent display; fallback to string keys for mixed types."""
    try:
        return sorted(s)
    except TypeError:
        return sorted(s, key=lambda x: str(x))

def format_set(s: set) -> str:
    """Format a set as a math-like string: ∅ or {a, b, ...}."""
    if not s:
        return "∅"
    elems = sort_result(s)
    return "{" + ", ".join(str(e) for e in elems) + "}"

# Color blending for Venn diagrams
def blend_colors(color1, color2):
    import matplotlib.colors as mcolors
    rgb1 = mcolors.to_rgb(color1)
    rgb2 = mcolors.to_rgb(color2)
    return tuple((c1 + c2) / 2 for c1, c2 in zip(rgb1, rgb2))

def blend_colors_3(color1, color2, color3):
    import matplotlib.colors as mcolors
    rgb1 = mcolors.to_rgb(color1)
    rgb2 = mcolors.to_rgb(color2)
    rgb3 = mcolors.to_rgb(color3)
    return tuple((c1 + c2 + c3) / 3 for c1, c2, c3 in zip(rgb1, rgb2, rgb3))

# --- Sidebar Configuration ---
st.sidebar.header("Configuration")
show_venn = st.sidebar.checkbox("Enable Venn Diagram Operations", True)
show_powerset = st.sidebar.checkbox("Enable Power Set Generator", False)
show_video = st.sidebar.checkbox("Show Theorems / Videos", False)

# --- Venn Diagram Section ---
if show_venn:
    st.sidebar.subheader("Venn Diagram Settings")
    num_sets = st.sidebar.selectbox("Number of Sets for Venn Diagram", [2, 3], index=0)
    default_examples = {
        2: ["2, 4, 6, 8", "3, 4, 5, 6, 9"],
        3: ["1, 2, 3, 5", "2, 3, 4, 6", "1, 4, 5, 7"]
    }
    A_input = st.sidebar.text_input("Set A elements (comma-separated)", value=default_examples[num_sets][0])
    B_input = st.sidebar.text_input("Set B elements (comma-separated)", value=default_examples[num_sets][1])
    C_input = None
    if num_sets == 3:
        C_input = st.sidebar.text_input("Set C elements (comma-separated)", value=default_examples[3][2])

    color_A = st.sidebar.color_picker("Color for Set A", "#FF5733")
    color_B = st.sidebar.color_picker("Color for Set B", "#33C1FF")
    color_C = None
    if num_sets == 3:
        color_C = st.sidebar.color_picker("Color for Set C", "#75FF33")

    U_input = st.sidebar.text_input("Universal Set (e.g., 1-10 or comma-separated)", value="1-10")

    if num_sets == 2:
        operation = st.sidebar.selectbox(
            "Choose Operation (2 sets)", [
                "A ∪ B", "A ∩ B", "A \\ B", "B \\ A",
                "Complement of A", "Complement of B",
                "Complement of (A ∪ B)", "Complement of (A ∩ B)"
            ]
        )
    else:
        operation = st.sidebar.selectbox(
            "Choose Operation (3 sets)", [
                "A ∪ B ∪ C", "A ∩ B ∩ C",
                "A \\ (B ∪ C)", "B \\ (A ∪ C)", "C \\ (A ∪ B)",
                "(A ∩ B) \\ C", "(A ∩ C) \\ B", "(B ∩ C) \\ A",
                "Complement of A", "Complement of B", "Complement of C",
                "Complement of (A ∪ B ∪ C)", "Complement of (A ∩ B ∩ C)"
            ]
        )

    A = parse_set(A_input)
    B = parse_set(B_input)
    C = parse_set(C_input) if num_sets == 3 else None
    U = parse_universal(U_input)

    # Validate universal coverage for complements
    if 'Complement' in operation:
        missing = set()
        missing |= (A - U)
        missing |= (B - U)
        if num_sets == 3:
            missing |= (C - U)
        if missing:
            st.sidebar.error(
                f"Universal set missing elements: {format_set(missing)}. Complements may be incomplete."
            )

    result, highlight_ids = set(), []

    # Compute result & highlight region IDs
    if num_sets == 2:
        set1, set2 = A, B
        colors = (color_A, color_B)
        if operation == "A ∪ B":
            result = A | B
            highlight_ids = ['10','01','11']
        elif operation == "A ∩ B":
            result = A & B
            highlight_ids = ['11']
        elif operation == "A \\ B":
            result = A - B
            highlight_ids = ['10']
        elif operation == "B \\ A":
            result = B - A
            highlight_ids = ['01']
        elif operation == "Complement of A":
            result = U - A
            set1, set2 = U, A
            colors = ("#CCCCCC", color_A)
            highlight_ids = ['10']
        elif operation == "Complement of B":
            result = U - B
            set1, set2 = U, B
            colors = ("#CCCCCC", color_B)
            highlight_ids = ['10']
        elif operation == "Complement of (A ∪ B)":
            union = A | B
            result = U - union
            set1, set2 = U, union
            colors = ("#CCCCCC", "#888888")
            highlight_ids = ['10']
        elif operation == "Complement of (A ∩ B)":
            inter = A & B
            result = U - inter
            set1, set2 = U, inter
            colors = ("#CCCCCC", "#888888")
            highlight_ids = ['10']
        else:
            st.error("Unknown operation.")
            set1 = set2 = result = set()
            colors = (color_A, color_B)

        result_repr = format_set(result)
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Venn Diagram")
            def plot_venn2_local(s1, s2, c1, c2, hids, repr_str):
                fig, ax = plt.subplots()
                v = venn2([s1, s2], set_labels=("A", "B"), set_colors=(c1, c2), ax=ax)
                normal_lw, inter_lw, result_lw = 0.5, 1.0, 1.5
                for rid, face_color in [('10', c1), ('01', c2)]:
                    patch = v.get_patch_by_id(rid)
                    if patch:
                        patch.set_facecolor(face_color); patch.set_alpha(1.0)
                        lw = result_lw if rid in hids else normal_lw
                        patch.set_edgecolor('black'); patch.set_linewidth(lw)
                p11 = v.get_patch_by_id('11')
                if p11:
                    blended = blend_colors(c1, c2)
                    p11.set_facecolor(blended); p11.set_alpha(1.0)
                    lw = result_lw if '11' in hids else inter_lw
                    p11.set_edgecolor('black'); p11.set_linewidth(lw)
                ax.set_title(f"Result: {repr_str}", fontsize=10)
                st.pyplot(fig)
            plot_venn2_local(set1, set2, colors[0], colors[1], highlight_ids, result_repr)

        with col2:
            st.subheader("Resulting Set")
            if result:
                st.write(f"Result: {result_repr}")
                with st.expander("Detailed Regions"):
                    A_only = A - B; B_only = B - A; AB = A & B
                    regions = {
                        'A only': (A_only, '10'),
                        'B only': (B_only, '01'),
                        'A ∩ B': (AB, '11')
                    }
                    for label, (subset, rid) in regions.items():
                        incl = '✅' if rid in highlight_ids else '❌'
                        st.write(f"**{label}**: {format_set(subset)} {incl}")
            else:
                st.info("Resulting set is empty (∅).")

    else:  # num_sets == 3
        set1, set
