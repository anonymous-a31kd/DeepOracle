import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import os
import csv
from processing import QueryLLM
import re
import sys
from collections import Counter
from dotenv import load_dotenv

load_dotenv()
query_llm = QueryLLM(
    model='gpt-4o-2024-11-20', 
    api_key=os.getenv('OPENAI_FORWARD_API_KEY'), 
    api_base=os.getenv('OPENAI_FORWARD_API_BASE')
)

def judgement_text_process(text):
    lines = text.strip().split('\n')
    lines.reverse()
    target_text = 'an unexpected exception:'
    result = 'No'
    for line in lines:
        line = line.replace('*', '').lower()
        if target_text in line:
            result = line.split(target_text)[-1]
            if 'yes' in result:
                result = 'Yes'
            elif 'no' in result:
                result = 'No'
            result = result.strip()
            return result
    return result


def get_exception_result(judge_result_1, judge_result_2, judge_result_3, output_file):
    df_a = pd.read_csv(judge_result_1)
    df_b = pd.read_csv(judge_result_2)
    df_c = pd.read_csv(judge_result_3)
    df_out = df_a.copy()

    def majority_vote(values):
        counter = Counter(values)
        most_common = counter.most_common()

        if len(most_common) == 1 and most_common[0][1] >= 2:
            return most_common[0][0]

        if len(most_common) > 1:
            if most_common[0][1] >= 2 and most_common[0][1] > most_common[1][1]:
                return most_common[0][0]
            else:
                return None  

        return None  

    final_llm = []
    # final_exc = []

    for i in range(len(df_a)):
        vote_a = df_a.loc[i,'llm_judgement']
        vote_b = df_b.loc[i,'llm_judgement']
        vote_c = df_c.loc[i,'llm_judgement']

        combo_votes = [vote_a, vote_b, vote_c]
        result = majority_vote(combo_votes)
        
        if result is None:
            llm = "No"
        else:
            llm = result

        final_llm.append(llm)

    df_out['llm_judgement'] = final_llm
    df_out.to_csv(output_file, index=False)


def gen_oracle_preds(judge_result, raw_oracle_preds, new_oracle_preds):
    exception_judgement = pd.read_csv(judge_result)
    oracle_preds = pd.read_csv(raw_oracle_preds)

    idx_to_update = exception_judgement.loc[(exception_judgement["llm_judgement"] == "Yes"), "index"].tolist()
    mask = (
        oracle_preds.index.isin(idx_to_update)
        & (oracle_preds["except_pred"] == 1)
    )

    oracle_preds.loc[mask, "except_pred"] = 0
    oracle_preds.loc[mask, "assert_pred"] = oracle_preds.loc[mask, "test_prefix"]
    oracle_preds.to_csv(new_oracle_preds, index=False)

exception_prompt_template_path = 'template/exception_judge.txt'
with open(exception_prompt_template_path, "r") as f:
    template_isException = f.read()


def exception_judge(inputs_file, dir_path, version, exception_list):
    df = pd.read_csv(inputs_file)
    exception_set = set(exception_list)

    output_file = f'{dir_path}/exception_judgement_{version}.csv'
    os.makedirs(dir_path, exist_ok=True)

    write_lock = threading.Lock()

    if os.path.exists(output_file):
        os.remove(output_file)

    if not os.path.exists(output_file):
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['index', 'llm_judgement'])

    judge_result = []
    error_list = []
    def process_row(index, row):
        test_prefix = row['test_prefix_true']
        focal_method = row['focal_method']
        test_scenario = row['test_scenario']
        javadoc = row['docstring']

        try:
            answer = query_llm.is_Exception(template_isException, test_prefix, test_scenario, focal_method, javadoc)
            with write_lock:
                with open(output_file, 'a', encoding='utf-8', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([index, answer])
            print(f"process row {index} success")
        except Exception as e:
            error_list.append(index)
            print(f"process row {index} error: {e}")
        return index, answer

    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [
            executor.submit(process_row, index, df.loc[index])
            for index in exception_set
            if index in df.index
        ]
        for future in as_completed(futures):
            try:
                judge_result.append(future.result())
            except Exception as e:
                print(e)

    return error_list

if __name__ == "__main__":
    base_path = sys.argv[1]
    # base_path = '../data/d4j_evo_prefix/deeporacle'
    df_oracle = pd.read_csv(f'{base_path}/vote_tmp/oracle_preds.csv')
    exception_list = df_oracle.index[df_oracle["except_pred"] == 1].tolist()

    input_file = f'{base_path}/test_inputs.csv'
    dir_path = f'{base_path}/exception'

    print(f'exception count: {len(exception_list)}')
    for version in range(1, 4):
        print(f'The {version}th exception judgment: ')
        error_list = exception_judge(input_file, dir_path, version, exception_list)
        # if (len(error_list) > 0):
        #     print(f'error row：{error_list}')
    
    for i in range(1, 4):
        df = pd.read_csv(f'{dir_path}/exception_judgement_{i}.csv')
        df['llm_judgement'] = df['llm_judgement'].apply(judgement_text_process)
        df = df.sort_values(by="index")
        df.to_csv(f'{dir_path}/judgement_result_process_{i}.csv', index=False)

    judge_result_1 = f'{dir_path}/judgement_result_process_1.csv'
    judge_result_2 = f'{dir_path}/judgement_result_process_2.csv'
    judge_result_3 = f'{dir_path}/judgement_result_process_3.csv'
    judge_result = f'{dir_path}/judgement_result_vote.csv'

    get_exception_result(judge_result_1, judge_result_2, judge_result_3, judge_result)

    raw_oracle_preds = f"{base_path}/vote_tmp/oracle_preds.csv"
    new_oracle_preds = f"{base_path}/oracle_preds.csv"
    gen_oracle_preds(judge_result, raw_oracle_preds, new_oracle_preds)

    