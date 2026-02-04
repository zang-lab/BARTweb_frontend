#!/bin/bash
#SBATCH -n {{N}}
#SBATCH --mem={{MEM}}
#SBATCH -t {{TIME}}
#SBATCH -p {{PARTITION}}
#SBATCH -A {{ACCOUNT}}

source ~/.bashrc
module load miniforge bioconda
conda activate {{CONDA_ENV}}

{{BART_CMD}} > {{LOG_FILE}} 2>&1
# python3 send_finish_email.py {{USER_PATH}}