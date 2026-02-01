import pandas as pd
import os


def read_second_row_vals(file_path, cols):
    if not os.path.exists(file_path):
        return {c: 0.0 for c in cols}
    df = pd.read_csv(file_path)
    if df.shape[0] < 2:
        return {c: 0.0 for c in cols}
    row = df.iloc[1]
    out = {}
    for c in cols:
        out[c] = float(row.get(c, 0.0))
    return out

def print_aggregated_results(methods, proj_types):
    cols = ['BugFound', 'TPs', 'FPs', 'TNs']

    method_w = max(len('Method'), max(len(m) for m in methods)) + 2
    col_w = 12
    col_w_l = 6
    fmt = f"{{:<{method_w}}}{{:>{col_w}}}{{:>{col_w}}}{{:>{col_w}}}{{:>{col_w_l}}}{{:>{col_w_l}}}{{:>{col_w_l}}}"

    print(fmt.format('Method', 'BugFound', 'FPR', 'Precision', 'TP', 'FP', 'TN'))
    for method in methods:
        totals = {c: 0.0 for c in cols}
        for proj in proj_types:
            fp = f'../RQ3/{method}/{proj}/rq1.csv'
            vals = read_second_row_vals(fp, cols)
            for c in cols:
                totals[c] += vals[c]
        bugfound = int(totals['BugFound'])
        tp = int(totals['TPs'])
        fp_cnt = int(totals['FPs'])
        tn = int(totals['TNs'])
        fpr = (fp_cnt / (fp_cnt + tn)) if (fp_cnt + tn) > 0 else 0.0
        precision = (tp / (tp + fp_cnt)) if (tp + fp_cnt) > 0 else 0.0
        print(fmt.format(method,
                        bugfound,
                        f"{fpr*100:.2f}%",
                        f"{precision*100:.2f}%",
                        tp, fp_cnt, tn))

if __name__ == "__main__":
    methods = ['deeporacle', 'without_exception_inf', 'without_scenario_inf', 'without_both']
    proj_types_evo = ['d4j_evo_prefix', 'gb_evo_prefix']
    proj_types_llm = ['d4j_llm_prefix', 'gb_llm_prefix']

    print("RQ3 Results: Ablation Study")
    print("EvoSuite-Generated Test Prefixes")
    print_aggregated_results(methods, proj_types_evo)
    
    print("\nLLM-Generated Test Prefixes")
    print_aggregated_results(methods, proj_types_llm)