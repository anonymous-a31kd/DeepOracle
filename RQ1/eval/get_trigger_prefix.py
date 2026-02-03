# 获取assert语句中的实际值
import os
from tree_sitter import Language, Parser
import re
import pandas as pd
from gen_tests_from_metadata import get_prefix

fail_catch_extract_re = re.compile(r'try\s*{(.*;).*fail\(.*\)\s*;\s*}\s*catch', re.DOTALL)
assert_re = re.compile(r'assert\w*\s*\((.*?)\);', re.DOTALL)


def has_oracle(test):
    '''
    @return: 1:(has try-catch); 2:(has assert); 3:(no oracle)
    '''
    m_try_catch = fail_catch_extract_re.search(test)
    m_assert = assert_re.search(test)
    if m_try_catch:
        return 1
    elif m_assert:
        return 2
    else:
        return 0


JAVA_LANGUAGE = Language('../lib/tree_sitter/my-languages.so', 'java')
parser = Parser()
parser.set_language(JAVA_LANGUAGE)

def get_result(code):
    tree = parser.parse(code.encode("utf8"))
    root_node = tree.root_node
    code_bytes = code.encode("utf8")


    def get_text(node):
        return code_bytes[node.start_byte:node.end_byte].decode("utf8")

    def find_assert_actual_expressions(node):
        actual_expressions = []

        def walk(n):
            if n.type == "method_invocation":
                method_name_node = n.child_by_field_name("name")
                args_node = n.child_by_field_name("arguments")
                if method_name_node and args_node:
                    method_name = get_text(method_name_node)

                    if method_name.startswith("assert"):
                        args = [c for c in args_node.children if c.is_named]
                        
                        if method_name in ["assertTrue", "assertFalse", "assertNull", "assertNotNull"]:
                            if len(args) >= 1:
                                actual_expr = args[0]
                            actual_expressions.append(get_text(actual_expr))
                        elif method_name == "assertEquals":
                            if len(args) == 2:
                                actual_expr = args[1]
                            elif len(args) == 3:
                                actual_expr = args[1]
                            elif len(args) == 4:
                                actual_expr = args[2]
                            actual_expressions.append(get_text(actual_expr))
                        elif method_name == "assertSame":
                            if len(args) >= 2:
                                actual_expr_1 = args[0]
                                actual_expr_2 = args[1]
                                actual_expressions.append(get_text(actual_expr_1)+ '==' + get_text(actual_expr_2))

                        # if len(args) >= 1:
                        #     last_arg = args[-1]
                        #     actual_expressions.append(get_text(last_arg))
            for child in n.children:
                walk(child)

        walk(node)
        return actual_expressions

    actuals = find_assert_actual_expressions(root_node)
    return actuals


def insert_try_catch(method, save_path):
    open_curly = method.find('{')
    try_catch_method = method[:open_curly] + '{\n\ttry ' + method[open_curly:] + f'\n\t\twriteResultToFile("False", \"{save_path}\");' + '\n\t\tfail(\"Expecting exception\"); \n\t} catch (Exception e) { '+f'\n\t\twriteResultToFile("True", \"{save_path}\");' + ' \n\t}\n}'
    return try_catch_method

def insert_save_code(method, save_code):
    lines = method.strip().split("\n")
    return "\n".join(lines + ["      " + save_code] + ["}"])

def gen_get_result_test(code, save_path):
    type = has_oracle(code)
    result = get_result(code)
    tmp_test = get_prefix(code) + '\n}'
    test = '@Test\n' + get_prefix(tmp_test).strip()

    if type == 1:
        test = insert_try_catch(test, save_path)
    elif type == 2:
        if len(result) > 0:
            inputs = result[0]
            save_code = f'writeResultToFile({inputs}, \"{save_path}\");'
            test = insert_save_code(test, save_code)
        else:
            test = insert_try_catch(test, save_path)
    elif type == 0:
        test = insert_try_catch(test, save_path)
    return test

def create_fresh_file(path):

    os.makedirs(os.path.dirname(path), exist_ok=True)

    if os.path.exists(path):
        os.remove(path)

    with open(path, 'w') as f:
        pass  

    return True

if __name__ == '__main__':
    version = 'buggy'
    projects = '5project_1'
    df_inputs = pd.read_csv(f'../data/test_cases_evosuite/{projects}/1/inputs.csv')
    df_meta = pd.read_csv(f'../data/test_cases_evosuite/{projects}/1/meta.csv')
    print(df_meta.shape)
    if 'except_pred' not in df_meta:
        df_meta['except_pred'] = 0
    if 'assert_pred' not in df_meta:
        df_meta['assert_pred'] = ""
    
    for idx, row in df_inputs[:].iterrows():
        test_prefix = row['test_prefix']
        save_path = f"../data/test_cases_evosuite/{projects}/1/filter/{version}/run_result/{idx}"
        if not create_fresh_file(save_path):
            print(f'{idx} create fail')
        test_case = gen_get_result_test(test_prefix, save_path)
        # print(test_case)
        df_meta.at[idx, 'assert_pred'] = test_case
    
    df_inputs_selected = df_inputs[['test_prefix']]
    df_meta_selected = df_meta[['project','bug_num', 'test_name', 'except_pred', 'assert_pred']]
    combined = pd.concat([df_meta_selected, df_inputs_selected], axis=1)
    combined.to_csv(f'../data/test_cases_evosuite/{projects}/1/filter/{version}/oracle_preds.csv', index=False)
    


