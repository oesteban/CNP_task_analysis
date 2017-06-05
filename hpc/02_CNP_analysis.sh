#!/bin/bash
#SBATCH --time=5:00:00
#SBATCH --mem=4GB
##SBATCH --qos=russpold
##SBATCH -p russpold
#SBATCH --output=logs/CNP.%a.txt
#SBATCH --error=logs/CNP.%a.txt
#SBATCH --mail-type=ALL
#SBATCH --mail-user=joke.durnez@gmail.com
#SBATCH --cpus-per-task=1
#SBATCH --ntasks=1

source /oak/stanford/groups/russpold/data/ds000030_R1.0.3_analysis_0.4.4_code/config.sh

unset PYTHONPATH

if [ ! -f $SINGULARITY ]; then
    echo "Singularity container for analyses not found!  Please first create singularity container."
fi

singularity exec $SINGULARITY echo "Analyis '${SLURM_ARRAY_TASK_ID}' started"

cd $HOMEDIR

set -e

eval $( sed "${SLURM_ARRAY_TASK_ID}q;d" hpc/tasks.txt )

echo "༼ つ ◕_◕ ༽つ CNP modeling pipeline finished"