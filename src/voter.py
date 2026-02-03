import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import os
import csv
import sys
from processing import QueryLLM
from postprocess import gen_oracle_preds_file
import re
from dotenv import load_dotenv

load_dotenv()
query_llm = QueryLLM(
    model='gpt-4o-2024-11-20', 
    api_key=os.getenv('OPENAI_FORWARD_API_KEY'), 
    api_base=os.getenv('OPENAI_FORWARD_API_BASE')
)

MAX_WORKERS = 8

def vote_text_process(text):
    lines = text.strip().split('\n')
    lines.reverse()
    target_text = 'Therefore, it should be:'
    for line in lines:
        if target_text in line:
            result = line.split(target_text)[-1]
            result = result.split('|')[0]
            result = result.strip().lstrip('<').rstrip('>').strip().upper()
            answer = 'No'
            if 'YES' in result:
                answer = "Yes"
            if 'NO' in result:
                answer = "No"
            return answer

def format_vote_result(vote_file, vote_result_tmp):
    df = pd.read_csv(vote_file)
    df['vote_result'] = df['vote_result'].apply(vote_text_process)
    df['vote_result'] = df['vote_result'].replace(["", "none", "None"], pd.NA)
    df['vote_result'] = df['vote_result'].fillna("No")
    df.to_csv(vote_result_tmp, index=False)



def init_vote_result(vote_result_file, row_list):
    df_init = pd.DataFrame({
        "index": row_list,
        "vote_result": ["TestCase_4"] * len(row_list)
    })
    df_init.to_csv(vote_result_file, index=False)


def save_vote_result(vote_result_file, yes_list, result="TestCase_4"):
    df = pd.read_csv(vote_result_file)
    df.loc[df["index"].isin(yes_list), "vote_result"] = result
    df.to_csv(vote_result_file, index=False)


template_vote_path = 'template/vote_oracle.txt'
with open(template_vote_path, "r") as f:
    template_vote = f.read()

def vote(inputs_path, oracle_v1, oracle_v2, output_file, row_list):
    df = pd.read_csv(inputs_path)
    df_case_v1 = pd.read_csv(oracle_v1)
    df_case_v2 = pd.read_csv(oracle_v2)
    row_set = set(row_list)

    write_lock = threading.Lock()

    if os.path.exists(output_file):
        os.remove(output_file)

    if not os.path.exists(output_file):
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['index', 'vote_result'])

    def process_row(index, row):
        test_prefix = row['test_prefix_true']

        case_v1 = df_case_v1.loc[index, 'test_case_llm']
        case_v2 = df_case_v2.loc[index, 'test_case_llm']

        try:
            answer = query_llm.vote_oracle(template_vote, test_prefix, case_v1, case_v2)
            print(f"process row {index} success")
            with write_lock:
                with open(output_file, 'a', encoding='utf-8', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([index, answer])

        except Exception as e:
            print(f"process row {index} error: {e}")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [
            executor.submit(process_row, index, df.loc[index])
            for index in row_set
            if index in df.index
        ]
        for future in as_completed(futures):
            pass


if __name__ == "__main__":
    base_path = sys.argv[1]
    # base_path = '../data/d4j_evo_prefix/deeporacle'
    inputs_path = f'{base_path}/inputs.csv'
    
    oracle_v1 = f'{base_path}/vote_tmp/oracle_v1.csv'
    oracle_v2 = f'{base_path}/vote_tmp/oracle_v2.csv'
    oracle_v3 = f'{base_path}/vote_tmp/oracle_v3.csv'
    vote_file = f'{base_path}/vote_tmp/llm_vote.csv'
    vote_result_tmp = f'{base_path}/vote_tmp/vote_result_tmp.csv'
    vote_result = f'{base_path}/vote_tmp/vote_result_process.csv'

    df_inputs = pd.read_csv(inputs_path)
    row_list = list(range(len(df_inputs)))
    # init vote_result_process.csv
    init_vote_result(vote_result, row_list)

    # first_vote
    print('first compare oracle_v1 and oracle_v2: ')
    vote(inputs_path, oracle_v1, oracle_v2, vote_file, row_list)
    # format
    format_vote_result(vote_file, vote_result_tmp)
    df_vote_tmp = pd.read_csv(vote_result_tmp)
    yes_list = df_vote_tmp.loc[df_vote_tmp["vote_result"] == 'Yes', "index"].tolist()
    no_list = df_vote_tmp.loc[df_vote_tmp["vote_result"] == 'No', "index"].tolist()
    save_vote_result(vote_result, yes_list, result="TestCase_1")
    
    # second_vote
    if len(no_list) > 0:
        print('second compare oracle_v2 and oracle_v3: ')
        vote(inputs_path, oracle_v2, oracle_v3, vote_file, no_list)
        format_vote_result(vote_file, vote_result_tmp)
        df_vote_tmp = pd.read_csv(vote_result_tmp)
        yes_list = df_vote_tmp.loc[df_vote_tmp["vote_result"] == 'Yes', "index"].tolist()
        no_list = df_vote_tmp.loc[df_vote_tmp["vote_result"] == 'No', "index"].tolist()
        save_vote_result(vote_result, yes_list, result="TestCase_2")

    # third_vote
    if len(no_list) > 0:
        print('third compare oracle_v1 and oracle_v3: ')
        vote(inputs_path, oracle_v1, oracle_v3, vote_file, no_list)
        format_vote_result(vote_file, vote_result_tmp)
        df_vote_tmp = pd.read_csv(vote_result_tmp)
        yes_list = df_vote_tmp.loc[df_vote_tmp["vote_result"] == 'Yes', "index"].tolist()
        no_list = df_vote_tmp.loc[df_vote_tmp["vote_result"] == 'No', "index"].tolist()
        save_vote_result(vote_result, yes_list, result="TestCase_3")
    
    df_vote = pd.read_csv(vote_result) 
    for _, row in df_vote.iterrows():
        idx = row['index']
        vote_result = row['vote_result']

        choose_case = vote_result.split('_')[-1]
        test_case = ''

        if choose_case == '1':
            df_case_v1 = pd.read_csv(oracle_v1)
            test_case = df_case_v1.loc[idx, 'test_case_llm']
        
        if choose_case == '2':
            df_case_v2 = pd.read_csv(oracle_v2)
            test_case = df_case_v2.loc[idx, 'test_case_llm']
        
        if choose_case == '3':
            df_case_v3 = pd.read_csv(oracle_v3)
            test_case = df_case_v3.loc[idx, 'test_case_llm']

        if choose_case == '4':
            df_case_v4 = pd.read_csv(inputs_path)
            test_case = df_case_v4.loc[idx, 'test_prefix_true']

        if pd.notna(test_case) and idx < len(df_inputs):
            df_inputs.loc[idx, 'test_case_llm'] = test_case

    df_inputs['test_prefix'] = df_inputs['test_prefix_true']
    oracle_tmp_file = f"{base_path}/vote_tmp/test_oracle_vote.csv"
    df_inputs.to_csv(oracle_tmp_file, columns=['test_prefix', 'test_case_llm'], index=False)

    # # postprocess
    meta_path = f'{base_path}/meta.csv'
    oracle_preds_path = f'{base_path}/vote_tmp/oracle_preds.csv'
    gen_oracle_preds_file(oracle_tmp_file, meta_path, oracle_preds_path)

