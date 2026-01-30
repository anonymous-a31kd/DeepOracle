import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import os
import csv
from processing import QueryLLM
import re
import sys
from dotenv import load_dotenv

load_dotenv()
query_llm = QueryLLM(
    model='gpt-4o-2024-11-20', 
    api_key=os.getenv('OPENAI_FORWARD_API_KEY'), 
    api_base=os.getenv('OPENAI_FORWARD_API_BASE')
)

def get_block_text(content, index):
    code_block_match = re.search(r"```plaintext(.*?)```", content, re.DOTALL)
    if code_block_match:
        code_block_content = code_block_match.group(1).strip()
        return code_block_content
    else:
        print(f"row {index} no plaintext block")
        return " "

def get_java_text(content, index):
    code_block_match = re.search(r"```java(.*?)```", content, re.DOTALL)
    if code_block_match:
        code_block_content = code_block_match.group(1).strip()
        return code_block_content
    else:
        print(f"row {index} no java block")
        return " "

def extract_method_signature(method_code):
    if pd.isna(method_code):
        return method_code
    method_code = method_code.strip()
    match = re.search(r'^[\s\S]*?\)\s*(throws\s+\w+(?:\s*,\s*\w+)*)?\s*\{', method_code)
    if match:

        return match.group(0).rstrip('{').strip()
    return method_code

def process_oracle(base_path, version):
    df_a = pd.read_csv(f'{base_path}/test_case_llm_v{version}.csv')  
    df_b = pd.read_csv(f'{base_path}/meta.csv') 
    for _, row in df_a.iterrows():
        idx = row['index']
        text_to_append = get_java_text(str(row['test_case_llm']), idx)

        if pd.notna(text_to_append) and idx < len(df_b):
            df_b.loc[idx, 'test_case_llm'] = text_to_append

    os.makedirs(f'{base_path}/vote_tmp', exist_ok=True)
    df_b.to_csv(f'{base_path}/vote_tmp/oracle_v{version}.csv', columns=['project', 'bug_num', 'test_name', 'test_case_llm'], index=False)


baseline_llm_prompt_template_path = 'template/baseline_llm.txt'
with open(baseline_llm_prompt_template_path, "r") as f:
    template_gen_oracle = f.read()

def get_oracle(inputs_path, context_path, output_file, row_list):
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
        try:
            answer = query_llm.gen_oracle_with_context(template_gen_oracle, test_prefix, focal_method, javadoc, context)
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

if __name__ == "__main__":
    base_path = sys.argv[1]
    # base_path = '../data/d4j_all_bugs_evo_new/sample/baseline'
    inputs_path = f'{base_path}/inputs.csv'
    context_path = f'{base_path}/context.csv'
    
    df = pd.read_csv(inputs_path)
    row_list = list(range(len(df)))
    for i in range(1, 4):
        print(f'The {i}th generation:')
        oracle_file = f'{base_path}/test_case_llm_v{i}.csv'
        get_oracle(inputs_path, context_path, oracle_file, row_list)
        process_oracle(base_path, version=i)
    
    # postprocess