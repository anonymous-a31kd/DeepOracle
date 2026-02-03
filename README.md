# Preparation

## Install Defects4J
- See: https://github.com/rjust/defects4j
- Install v2.0.0

## Install GrowingBugs
- See: https://github.com/liuhuigmail/GrowingBugRepository
- Install v7.0
- Commit a880ccb, adding 100 new bugs


# Directory Architecture
```text

```

# Use DeepOracle to Generate oracles (requires configuring API-KEY)
```bash
cd src
# Generate Scenario
python get_scenario.py work_dir
# Generate oracle candidates and vote
python gen_oracle.py work_dir
python voter.py work_dir
# Execute exception Inference 
python exception_judge.py work_dir
```
* work_dir represents the working directory, which should include inputs.csv, meta.csv, context.csv

---

# Reproduction
## RQ1
### Execute the generated oracle 
(Datasets need to be prepared before running)
``` bash
# generate oracles using DeepOracle and Baselines
cd RQ1
tar xzf test_framework.tar.gz
# run experiments for rq1_1 and rq1_2
bash run_rq1_2.sh 4 1
```

### Display the comparison results with baselines
All runtime data and results during the experiment are stored in data/run_record.tar.gz.
``` bash
cd data
tar xzf run_record.tar.gz
```

You can execute the following script to view the data statistics results.
``` bash
cd eval
python rq1.py
```
---

## RQ2
Test Scenario Evaluation samples and evaluation results are stored in RQ2
```

```

---
## RQ3
### Display the ablation experiment results
All runtime data and results during the experiment are stored in RQ3/ablation_run_record.tar.gz.
You can execute the following script to view the data statistics results.
``` bash
cd eval
python rq3.py
```

### Manually rerun the ablation experiment (requires configuring API-KEY)
Without Exception Inference
``` bash
# Generate Scenario
python get_scenario.py work_dir
# Generate oracle candidates and vote
python gen_oracle.py work_dir
python voter.py work_dir
```
---
Without Scenario Inference
``` bash
python -m ablation.get_oracle_candidates_no_scenario work_dir
python voter.py work_dir
python -m ablation.get_exception_judgement_no_scenario work_dir
```
---
Without Both
``` bash
python -m ablation.get_oracle_candidates_no_scenario work_dir
python voter.py work_dir
```
