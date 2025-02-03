import streamlit as st
import pandas as pd
import ast
from io import StringIO

st.title('Finetune Metric Editor')
uploaded_file = st.file_uploader('Choose a file')

LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

def get_excel_col_name(col):
    result = []
    while col:
        col, rem = divmod(col-1, 26)
        result[:0] = LETTERS[rem]
    return ''.join(result)

def correct_markdown_table(input_text):
    rows = input_text.strip().split("\n")

    corrected_rows = []
    
    for row in rows:
        cells = row.strip().split(' | ')
        
        corrected_cells = [cell.strip() for cell in cells]
        corrected_cells[0] = str(corrected_cells[0]).removeprefix('| ')
        corrected_cells[-1] = str(corrected_cells[-1]).removesuffix(' |')
        
        corrected_rows.append('| ' + ' | '.join(corrected_cells) + ' |')

    if corrected_rows:
        num_columns = corrected_rows[0].count('|') - 1
        
        alphabet_headers = '| ' + ' | '.join([chr(65 + i) for i in range(num_columns)]) + ' |'
        separator_row = '| ' + ' | '.join(['---'] * num_columns) + ' |'
        
        corrected_rows.insert(0, alphabet_headers)
        corrected_rows.insert(1, separator_row)

    return "\n".join(corrected_rows)

def parse_markdown_table(input_text):
    rows = input_text.strip().split('\n')
    
    if not rows:
        return pd.DataFrame()

    parsed_rows = []
    for row in rows:
        cells = row.strip().split(' | ')
        cells = [cell.strip() for cell in cells]
        cells[0] = cells[0].removeprefix('| ')
        cells[-1] = cells[-1].removesuffix(' |')
        parsed_rows.append(cells)

    num_columns = len(parsed_rows[0])
    alphabet_headers = [get_excel_col_name(i+1) for i in range(num_columns)]

    df = pd.DataFrame(parsed_rows, columns=alphabet_headers)

    return df

def switch_state(idx):
    if st.session_state['watched_chunks'][idx]:
        st.session_state['watched_chunks'][idx] = False
    else:
        st.session_state['watched_chunks'][idx] = True

if uploaded_file:
    stringio = StringIO(uploaded_file.getvalue().decode('utf-8'))
    jsonl_list = stringio.readlines()

    if 'watched_chunks' not in st.session_state:
        st.session_state['watched_chunks'] = [False] * len(jsonl_list)
    
    watched_chunks = st.session_state['watched_chunks']

    st.sidebar.header('Watched Chunks Summary')
    watched_count = sum(watched_chunks)
    total_chunks = len(jsonl_list)
    st.sidebar.write(f'✔️ **{watched_count} / {total_chunks}** chunks viewed')

    for idx, jsonl in enumerate(jsonl_list):
        message_pair = ast.literal_eval(jsonl)['messages']
        user_sent_obj_str = next(x for x in message_pair if x['role'] == 'user')['content']
        user_sent_obj = ast.literal_eval(user_sent_obj_str)
        chunk_data = user_sent_obj['chunk']
        sheet_name = user_sent_obj['SheetName']
        file_name = user_sent_obj['fileName']

        df = parse_markdown_table(chunk_data)
        
        st.subheader(f'Chunk {idx + 1}')
        st.dataframe(df)
        
        st.checkbox('Mark as viewed', on_change=switch_state, args=[idx], key=f'watched_{idx}', value=watched_chunks[idx])

        st.divider()