#!/bin/bash
#SBATCH --time=00:20:00
#SBATCH --mem=4GB
##SBATCH --qos=russpold
##SBATCH -p russpold
#SBATCH --output=logs/CNP.preparation.txt
#SBATCH --error=logs/CNP.preparation.txt
#SBATCH --mail-type=ALL
#SBATCH --mail-user=joke.durnez@gmail.com
#SBATCH --cpus-per-task=1
#SBATCH --ntasks=1

source $HOME/CNP_analysis/config.sh

unset PYTHONPATH

set -e

singularity exec -B $OAK:$OAK $SINGULARITY echo "Analyis started"
singularity exec -B $OAK:$OAK $SINGULARITY python -s $HOMEDIR/hpc/write_contrasts.py
singularity exec -B $OAK:$OAK $SINGULARITY python -s $HOMEDIR/hpc/write_group_tasks.py
singularity exec -B $OAK:$OAK $SINGULARITY python -s $HOMEDIR/hpc/write_tasks.py

echo "༼ つ ◕_◕ ༽つ CNP pipeline preparation finished"
