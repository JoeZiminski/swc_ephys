"""
Here defaults related to the HPC system `spikewrap` is run on
(if not running locally) are stored.


`hpc_sorter_images_path()`
    This function returns the default path where singularity images are stored.
    The purpose of this storage path is to avoid users installing multiple copies
    across the system. This path can be changed based on the HPC system used and
    populated with SpikeInterface singularity images.

`default_slurm_options()`
    The default options passed to the submitit executor and converted
    to SLURM batch script arguments. If passing new options in `slurm_batch`,
    the passed options are overriden but other defaults are maintained.
"""
from typing import Dict


def hpc_sorter_images_path() -> str:
    return "/ceph/neuroinformatics/neuroinformatics/scratch/sorter_images"


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
