import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import os
import csv
import sys
from processing import QueryLLM
from postprocess import process_oracle
import re
from dotenv import load_dotenv

load_dotenv()
query_llm = QueryLLM(
    model='gpt-4o-2024-11-20', 
    api_key=os.getenv('OPENAI_API_KEY'), 
    api_base=os.getenv('OPENAI_API_BASE')
)

def extract_method_signature(method_code):
    if pd.isna(method_code):
        return method_code
    method_code = method_code.strip()
    match = re.search(r'^[\s\S]*?\)\s*(throws\s+\w+(?:\s*,\s*\w+)*)?\s*\{', method_code)
    if match:
        return match.group(0).rstrip('{').strip()
    return method_code

oracle_gen_prompt_template_path = 'template/gen_oracle.txt'
with open(oracle_gen_prompt_template_path, "r") as f:
    template_oracle_gen = f.read()

def get_oracle(inputs_path, context_path, output_file, row_list, max_workers=8):

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

    error_list = []
    def process_row(index, row):
        focal_method = row['focal_method']
        test_scenario = row['test_scenario']
        javadoc = row['docstring']
        context = row['context']
        test_prefix = row['test_prefix_true']
        method_signature = extract_method_signature(focal_method)
        
        try:
            answer = query_llm.gen_oracle_for_test_prefix(template_oracle_gen, test_prefix, test_scenario, method_signature, context, javadoc)
            with write_lock:
                with open(output_file, 'a', encoding='utf-8', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([index, answer])
            print(f"process row {index} success")

        except Exception as e:
            error_list.append(index)
            print(f"process row {index} error: {e}")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
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

    context_path = f'{base_path}/context.csv'
    merge_input = f'{base_path}/test_inputs.csv'

    df = pd.read_csv(merge_input)
    row_list = list(range(len(df)))

    for i in range(1, 4):
        print(f"The {i}th generation: ")
        error_list = []
        oracle_path = f'{base_path}/test_case_llm_v{i}.csv'
        if os.path.exists(oracle_path): 
            os.remove(oracle_path)
        error_list = get_oracle(merge_input, context_path, oracle_path, row_list, 8)
        # print(error_list)
        process_oracle(base_path, version=i)

    