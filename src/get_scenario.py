import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import os
import csv
import sys
from processing import QueryLLM
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


def get_block_text(content, index):
    code_block_match = re.search(r"```plaintext(.*?)```", content, re.DOTALL)
    if code_block_match:
        code_block_content = code_block_match.group(1).strip()
        return code_block_content
    else:
        print(f"row {index} no plaintext block")
        return " "

def process_scenario(base_path, scenarios_name='scenarios', test_inputs_name = 'test_inputs'):
    df_a = pd.read_csv(f'{base_path}/{scenarios_name}.csv')  
    df_b = pd.read_csv(f'{base_path}/inputs.csv') 
    for _, row in df_a.iterrows():
        idx = row['index']
        text_to_append = get_block_text(str(row['scenario']), idx)

        if pd.notna(text_to_append) and idx < len(df_b):
            df_b.loc[idx, 'test_scenario'] = text_to_append

    df_b.to_csv(f'{base_path}/{test_inputs_name}.csv', index=False)


template_scenario_gen_path = 'template/gen_scenario.txt'
with open(template_scenario_gen_path, "r") as f:
    template_scenario_gen = f.read()

def get_scenario(inputs_path, context_path, output_file, case_list):
    
    df = pd.read_csv(inputs_path)
    df_context = pd.read_csv(context_path)
    case_set = set(case_list)

    df_context.index = df_context.index.astype(int)
    df.index = df.index.astype(int)
    df['context'] = df_context['context']

    write_lock = threading.Lock()
    if not os.path.exists(output_file):
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['index', 'scenario'])


    def process_row(index, row):
        focal_method = row['focal_method']
        test_prefix = row['test_prefix_true']
        javadoc = row['docstring']
        context = row['context']
        try:
            answer = query_llm.get_scenario_from_test_prefix(template_scenario_gen, test_prefix, focal_method, context, javadoc)
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
            for index in case_set
            if index in df.index
        ]
        for future in as_completed(futures):
            pass


if __name__ == "__main__":
    base_path = sys.argv[1]
    # base_path = '../data/d4j_evo_prefix/deeporacle'
    inputs_path = f'{base_path}/inputs.csv'
    context_path = f'{base_path}/context.csv'
    scenario_path = f'{base_path}/scenarios.csv'
    
    df = pd.read_csv(inputs_path)
    case_list = list(range(len(df)))

    get_scenario(inputs_path, context_path, scenario_path, case_list)
    process_scenario(base_path)