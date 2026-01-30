import re
import pandas as pd
import os
import sys
import fire

def get_java_text(content, index):
    code_block_match = re.search(r"```java(.*?)```", content, re.DOTALL)
    if code_block_match:
        code_block_content = code_block_match.group(1).strip()
        return code_block_content
    else:
        print(f"row {index} no java block")
        return " "

def get_block_text(content, index):
    code_block_match = re.search(r"```plaintext(.*?)```", content, re.DOTALL)
    if code_block_match:
        code_block_content = code_block_match.group(1).strip()
        return code_block_content
    else:
        print(f"row {index} no plaintext block")
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


def is_exception(test, index):
    exception_str = '@Test(expect'
    try:
        if exception_str in test or ('try {' in test and ('} catch' in test or '} finally' in test)):
            return True
        else:
            return False
    except Exception as e:
        print(f'error: {index}')
        print(e)


def gen_oracle_preds_file(oracle_file, meta_file, output_file):
    df_oracle = pd.read_csv(oracle_file)
    df_meta = pd.read_csv(meta_file)

    if 'except_pred' not in df_meta:
        df_meta['except_pred'] = 0
    if 'assert_pred' not in df_meta:
        df_meta['assert_pred'] = ""
        
    for idx, row in df_oracle.iterrows():
        test_case = row['test_case_llm']
        result = is_exception(test_case, idx)

        if result:
            df_meta.at[idx, 'except_pred'] = 1
        else:
            df_meta.at[idx, 'except_pred'] = 0
            df_meta.at[idx, 'assert_pred'] = test_case.replace('@Test', '')

    df_oracle_selected = df_oracle[['test_prefix']]
    df_meta_selected = df_meta[['project','bug_num', 'test_name', 'except_pred', 'assert_pred']]
    combined = pd.concat([df_meta_selected, df_oracle_selected], axis=1)
    combined.to_csv(output_file, index=False)


if __name__ == "__main__":
    fire.Fire({
        'get_java_text': get_java_text,
        'process_oracle': process_oracle
    })