"""
UI for file loading
"""

import sys
import os
import tempfile
import pandas as pd
import streamlit as st

# add parent dir
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import DEBUG, COLLECTION_LIST
from vector_search import SemanticSearch
from chunk_index_utils import load_and_split_pdf, load_and_split_docx
from utils import get_console_logger

# init session
if COLLECTION_LIST:
    if "collection_name" not in st.session_state:
        st.session_state.collection_name = COLLECTION_LIST[0]
else:
    st.error("No collections available.")

if "show_documents" not in st.session_state:
    st.session_state.show_documents = False


header_area = st.container()
table_area = st.container()

with header_area:
    st.header("Loading Utility")

logger = get_console_logger()


#
# Supporting functions
#
def list_books(_collection_name):
    """
    return the list of books in the given collection
    """
    _search = SemanticSearch()

    _books_list = _search.list_books_in_collection(collection_name=_collection_name)

    # reorder
    return sorted(_books_list)


def show_documents_in_collection(_collection_name):
    """
    show the documents in the given collection
    """
    if st.session_state.show_documents:
        with st.spinner():
            _books_list = list_books(_collection_name)

            books_names = [item[0] for item in _books_list]
            books_chunks = [item[1] for item in _books_list]

            # convert in a Pandas DataFrame for Visualization
            df_list = pd.DataFrame(
                {"Document": books_names,
                 "Num. chunks": books_chunks}
            )
            # index starting by 1
            df_list.index = range(1, len(df_list) + 1)
            # visualize
            with table_area:
                st.table(df_list)


def on_selection_change():
    """
    React to the selection of the collection
    """
    selected = st.session_state["name_selected"]

    logger.info("Collection list selected: %s", selected)

    show_documents_in_collection(selected)


st.session_state.collection_name = st.sidebar.selectbox(
    "Collection name",
    COLLECTION_LIST,
    key="name_selected",
    on_change=on_selection_change,
)

st.session_state.show_documents = st.sidebar.checkbox("Show documents")
uploaded_file = st.sidebar.file_uploader("Upload a file", type=["pdf", "docx"])

# added a button for loading
load_file = st.sidebar.button("Load file")

if uploaded_file is not None and load_file:
    # identify file type
    only_name = os.path.basename(uploaded_file.name)
    file_ext = uploaded_file.name.split(".")[-1]

    if DEBUG:
        logger.info(file_ext)

    # save as a temporary file
    path_file_temp = os.path.join(tempfile.gettempdir(), only_name)

    # write the temp file
    with open(path_file_temp, "wb") as tmp_file:
        tmp_file.write(uploaded_file.read())

    # check that the file is not already in the collection
    books_list = list_books(st.session_state.collection_name)

    if DEBUG:
        logger.info(books_list)

    if only_name not in books_list:
        logger.info("Loading %s ...", only_name)

        docs = []

        if file_ext == "pdf":
            docs = load_and_split_pdf(path_file_temp)

        elif file_ext == "docx":
            docs = load_and_split_docx(path_file_temp)

        if len(docs) > 0:
            SemanticSearch().add_documents(
                docs, collection_name=st.session_state.collection_name
            )

        st.success("Document loaded")

    else:
        st.error(f"{only_name} already in collection")
