"""
Here defaults related to the HPC system `spikewrap` is run on
(if not running locally) are stored.

`default_slurm_options()`
    The default options passed to the submitit executor and converted
    to SLURM batch script arguments. If passing new options in `slurm_batch`,
    the passed options are overriden but other defaults are maintained.
"""

from typing import Dict


def default_slurm_options() -> Dict:
    return {
        "nodes": 1,
        "mem_gb": 40,
        "timeout_min": 24 * 60,
        "cpus_per_task": 8,
        "tasks_per_node": 1,
        "gpus_per_node": 1,
        "slurm_gres": "gpu:1",
        "slurm_partition": "gpu",
        "exclude": "gpu-sr670-20,gpu-sr670-21,gpu-sr670-22",
        "wait": False,
        "env_name": "spikewrap",
    }


def default_gpu_partition():
    return "gpu"


def default_cpu_partition():
    return "cpu"
