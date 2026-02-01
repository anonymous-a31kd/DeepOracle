import pandas as pd
import os


def read_csv_second_row(file_path):
    df = pd.read_csv(file_path)
    if df.shape[0] < 2:
        return []  
    second_row = df.iloc[1, 1:]  
    return second_row.tolist()

def format_row(data):
    if not data or len(data) < 6:
        return None
    bugfound = int(data[0])
    fpr = round(float(data[1]) * 100, 2)
    precision = round(float(data[2]) * 100, 2)
    tp = int(data[3])
    fp = int(data[4])
    tn = int(data[5])
    return [bugfound, f"{fpr:.2f}%", f"{precision:.2f}%", tp, fp, tn]

def print_formatted_table(methods, proj_types):
    header = ['Method', 'BugFound', 'FPR', 'Precision', 'TP', 'FP', 'TN']
    method_w = max(len('Method'), max(len(m) for m in methods)) + 2
    col_w = 12
    col_w_l = 6
    fmt = f"{{:<{method_w}}}{{:>{col_w}}}{{:>{col_w}}}{{:>{col_w}}}{{:>{col_w_l}}}{{:>{col_w_l}}}{{:>{col_w_l}}}"

    for proj_type in proj_types:
        if 'd4j' in proj_type:
            print("Defects4J")
        else:
            print("GrowingBugs")

        print(fmt.format(*header))
        for method in methods:
            file_path = f'../data/{proj_type}/{method}/rq1.csv'
            second_row_data = read_csv_second_row(file_path)
            formatted = format_row(second_row_data)
            if formatted is None:
                print(fmt.format(method, '-', '-', '-', '-', '-', '-'))
            else:
                # formatted = [BugFound, "FPR%", "Precision%", TP, FP, TN]
                print(fmt.format(method, formatted[0], formatted[1], formatted[2], formatted[3], formatted[4], formatted[5]))
        print()

if __name__ == "__main__":
    methods = ['toga', 'togll', 'llm_direct', 'deeporacle']
    print("RQ1_1 Results: EvoSuite-Generated Test Prefixes")
    rq1_1_proj_types = ['d4j_evo_prefix', 'gb_evo_prefix']
    print_formatted_table(methods, rq1_1_proj_types)

    print("RQ1_2 Results: LLM-Generated Test Prefixes")
    rq1_2_proj_types = ['d4j_llm_prefix', 'gb_llm_prefix']
    print_formatted_table(methods, rq1_2_proj_types)