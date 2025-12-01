#!/bin/bash
#SBATCH --job-name=testing_parallel       # Job name
#SBATCH --nodes=1                  # Run on a single node
#SBATCH --ntasks=16
#SBATCH --time=02:00:00            # Time limit of 2 hours
#SBATCH --output=testing_parallel.o%j     # Standard output and error log

module load modtree/cpu
module load python
module load openmpi
module load py-mpi4py 

# Print job information
echo "Job ID: $SLURM_JOB_ID"
echo "Job Name: $SLURM_JOB_NAME"
echo "Nodes: $SLURM_JOB_NUM_NODES"
echo "Tasks: $SLURM_NTASKS"
echo "CPUs per task: $SLURM_CPUS_PER_TASK"
echo "Working directory: $SLURM_SUBMIT_DIR"
echo ""

# Change to the directory where the script was submitted
cd $SLURM_SUBMIT_DIR

# Run the MPI Python application
echo "Running testing_parallel.py with $SLURM_NTASKS MPI processes..."
mpirun -np $SLURM_NTASKS python testing_parallel.py

echo "Job completed successfully!"