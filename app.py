import json

import numpy as np
import pandas as pd
import streamlit as st
from libeq import EqSolver, SolverData, species_concentration

if "wmode" not in st.session_state:
    st.session_state.wmode = "distribution"
if "data" not in st.session_state:
    st.session_state.data = dict(
        speciesModel={
            "Ignored": {},
            "Name": {},
            "LogB": {},
            "Sigma": {},
            "Ref. Ionic Str.": {},
            "CG": {},
            "DG": {},
            "EG": {},
            "A": {},
            "Ref. Comp.": {},
        },
        solidSpeciesModel={
            "Ignored": {},
            "Name": {},
            "LogKs": {},
            "Sigma": {},
            "Ref. Ionic Str.": {},
            "CG": {},
            "DG": {},
            "EG": {},
            "A": {},
            "Ref. Comp.": {},
        },
    )
if "results" not in st.session_state:
    st.session_state.results = None
if "calculated" not in st.session_state:
    st.session_state.calculated = False


def calculate():
    solver_data = SolverData.load_from_pyes(st.session_state.data)

    result, log_beta, log_ks, saturation_index, total_concentration = EqSolver(
        solver_data, mode=st.session_state.wmode
    )

    concentrations = species_concentration(
        result, log_beta, solver_data.stoichiometry, full=True
    )

    st.session_state.results = pd.DataFrame(
        concentrations[
            :,
            np.r_[
                0 : solver_data.nc,
                (solver_data.nc + solver_data.nf) : (
                    solver_data.nc + solver_data.nf + solver_data.ns
                ),
            ],
        ],
        columns=solver_data.species_names,
    )
    st.session_state.calculated = True


def clear_results():
    st.session_state.calculated = False
    st.session_state.results = None


st.title("PyES Online 🧪")
st.divider()

col1, col2 = st.columns([3, 1])

pyes_file = st.file_uploader(
    "Pick a PyES file",
    type=["json"],
    accept_multiple_files=False,
    on_change=clear_results,
)
st.button(
    "Calculate",
    use_container_width=True,
    disabled=(pyes_file is None),
    on_click=calculate,
)


if pyes_file:
    st.session_state.data = json.load(pyes_file)
else:
    st.write("No file selected")


tab1, tab2, tab3 = st.tabs(["Species", "Settings", "Results"])

with tab1:
    st.subheader("Soluble")
    st.dataframe(
        st.session_state.data.get("speciesModel", {}),
        use_container_width=True,
        column_config={
            "Ignored": st.column_config.CheckboxColumn(
                default=False,
            )
        },
        hide_index=True,
    )

    st.subheader("Precipitates")
    st.dataframe(
        st.session_state.data.get("solidSpeciesModel", {}),
        use_container_width=True,
        column_config={
            "Ignored": st.column_config.CheckboxColumn(
                default=False,
            )
        },
        hide_index=True,
    )

with tab2:
    wmode = st.selectbox("Work mode", ("Species Distribution", "Titration Simulation"))

    st.divider()
    st.subheader("Mode Settings")
    if wmode == "Species Distribution":
        st.session_state.wmode = "distribution"
        st.number_input("Initial pX", value=st.session_state.data.get("initialLog", 1))
        st.number_input("Final pX", value=st.session_state.data.get("finalLog", 14))
        conc_columns = ["C0", "Sigma C0"]

    elif wmode == "Titration Simulation":
        st.session_state.wmode = "titration"
        conc_columns = ["C0", "CT", "Sigma C0", "Sigma CT"]

        st.write("Titration Simulation")
    else:
        st.write("Unknown mode")

    st.divider()
    st.subheader("Concentrations")

    st.dataframe(
        st.session_state.data.get("concModel", {}),
        use_container_width=True,
        column_order=conc_columns,
    )

with tab3:
    if st.session_state.calculated:
        st.dataframe(st.session_state.results, use_container_width=True)

        st.line_chart(st.session_state.results)
