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


# Reproduction
## Use DeepOracle to Generate oracles 
```bash
# Generate Scenario
python get_scenario.py work_dir
# Generate oracle candidates and vote
python gen_oracle.py work_dir
python voter.py work_dir
# Execute exception Inference 
python exception_judge.py work_dir
```
* work_dir represents the working directory, which should include inputs.csv, meta.csv, context.csv

## RQ1
### Execute the generated oracle
``` bash
# generate oracles using DeepOracle and Baselines
cd RQ1
# run experiments for rq1_1 and rq1_2
bash run_rq1_2.sh
# obtain the results
python -m rqs.rq1_2 cal_result
```

### Display the comparison results with baselines.
``` bash
cd eval
python rq1.py
```

## RQ2

```

```

## RQ3

### Display the abaltion experiment results
``` bash
cd eval
python rq1.py
```

### Without Exception Inference
``` bash
# Generate Scenario
python get_scenario.py work_dir
# Generate oracle candidates and vote
python gen_oracle.py work_dir
python voter.py work_dir
```

### Without Scenario Inference
``` bash
python -m ablation.get_oracle_candidates_no_scenario work_dir
python voter.py work_dir
python -m ablation.get_exception_judgement_no_scenario work_dir
```

### Without Both
``` bash
python -m ablation.get_oracle_candidates_no_scenario work_dir
python voter.py work_dir
```
