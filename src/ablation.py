import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import os
import csv
from processing import QueryLLM
from postprocess import extract_method_signature, process_oracle, judgement_text_process
from exception_judge import get_exception_result, gen_oracle_preds
import re
import sys
import fire
from dotenv import load_dotenv

load_dotenv()
query_llm = QueryLLM(
    model='gpt-4o-2024-11-20', 
    api_key=os.getenv('OPENAI_API_KEY'), 
    api_base=os.getenv('OPENAI_API_BASE')
)

oracle_gen_prompt_no_scenario_template_path = 'template/gen_oracle_a.txt'
with open(oracle_gen_prompt_no_scenario_template_path, "r") as f:
    template_gen_oracle_no_scenario = f.read()

def gen_oracle_without_scenario(inputs_path, context_path, output_file, row_list):
    df = pd.read_csv(inputs_path)
    df_context = pd.read_csv(context_path)
    row_set = set(row_list)

    df_context.index = df_context.index.astype(int)
    df.index = df.index.astype(int)
    df['context'] = df_context['context']

    write_lock = threading.Lock()

    if not os.path.exists(output_file):
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['index', 'test_case_llm'])

    def process_row(index, row):
        focal_method = row['focal_method']
        test_prefix = row['test_prefix_true']
        javadoc = row['docstring']
        context = row['context']
        focal_method_siganture = extract_method_signature(focal_method)
        try:
            answer = query_llm.gen_oracle_with_context(template_gen_oracle_no_scenario, test_prefix, focal_method_siganture, javadoc, context)
            print(f"process row {index} success")

            with write_lock:
                with open(output_file, 'a', encoding='utf-8', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([index, answer])

        except Exception as e:
            print(f"process row {index} error: {e}")

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [
            executor.submit(process_row, index, df.loc[index])
            for index in row_set
            if index in df.index
        ]
        for future in as_completed(futures):
            pass


exception_judge_prompt_no_scenario_template_path = 'template/exception_judge_a.txt'
with open(exception_judge_prompt_no_scenario_template_path, "r") as f:
    template_exception_judge_no_scenario = f.read()


def exception_judge_no_scenario(inputs_file, dir_path, version, exception_list):
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
        test_scenario = ''
        javadoc = row['docstring']

        try:
            answer = query_llm.is_Exception(template_exception_judge_no_scenario, test_prefix, test_scenario, focal_method, javadoc)
            with write_lock:
                with open(output_file, 'a', encoding='utf-8', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([index, answer])
            print(f"process row {index} success")
        except Exception as e:
            error_list.append(index)
            print(f"process row {index} error: {e}")
        return index, answer

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [
            executor.submit(process_row, index, df.loc[index])
            for index in exception_set
            if index in df.index
        ]
        for future in as_completed(futures):
            try:
                judge_result.append(future.result())
            except Exception as e:
                print(f"处理某一行出错: {e}")

    return error_list


def get_oracle_candidates_no_scenario(base_path):
    inputs_path = f'{base_path}/inputs.csv'
    context_path = f'{base_path}/context.csv'
    df = pd.read_csv(inputs_path)
    row_list = list(range(len(df)))
    for i in range(1, 4):
        print(f"The {i}th generation: ")
        oracle_file = f'{base_path}/test_case_llm_v{i}.csv'
        gen_oracle_without_scenario(inputs_path, context_path, oracle_file, row_list)
        process_oracle(base_path, version=i)


def get_exception_judgement_no_scenario(base_path):
    df_oracle = pd.read_csv(f'{base_path}/vote_tmp/oracle_preds.csv')
    exception_list = df_oracle.index[df_oracle["except_pred"] == 1].tolist()
    input_file = f'{base_path}/inputs.csv'
    dir_path = f'{base_path}/exception'
    for version in range(1, 4):
        print(f'The {version}th exception judgment(no scenario): ')
        error_list = exception_judge_no_scenario(input_file, dir_path, version, exception_list)
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



def ablation_both(base_path):
    # copy without_scenario_inf proj_type/vote_tmp
    pass



if __name__ == "__main__":
    fire.Fire({
        "get_oracle_candidates_no_scenario": get_oracle_candidates_no_scenario,
        "get_exception_judgement_no_scenario": get_exception_judgement_no_scenario,
        "ablation_both": ablation_both,
    })
    
    # no exception  
    # copy from vote_tmp/oracle_preds.csv
    
    # no scenario
    # 1. gen_oracle_no_scenario
    # 2. vote
    # 3. e_judge

    # no both
    # 1. gen_oracle_no_scenario
    # 2. vote

    pass