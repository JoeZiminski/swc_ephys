import datetime
import subprocess
from pathlib import Path
from typing import Callable, Dict, Union

import submitit

from spikewrap.configs.hpc import (
    default_cpu_partition,
    default_gpu_partition,
    default_slurm_options,
)
from spikewrap.utils import _utils
from spikewrap.utils._checks import system_call_success


def run_in_slurm(slurm_opts: Union[bool, Dict], func_to_run: Callable, func_opts: Dict, log_base_path: Path):
    """
    Run a function in SLURM using submitit.

    Parameters
    ----------

    slurm_opts : Union[bool, Dict]
        Default SLURM options will be loaded from backend/hpc.py. If `True`, defaults
        are used as-is, otherwise these can be overwritten by including the
        key-value pairs to overwrite in a Dict. See backend/hpc.py for an example.

    func_to_run : Callable
        The function to run with SLURM with submitit.

    func_opts : Dict
        A dictionary of kwargs to run in the `func_to_run`.
    """
    if not is_slurm_installed():
        raise RuntimeError("Cannot run with slurm, slurm is not found on this system.")

    used_slurm_opts = default_slurm_options()

    if isinstance(slurm_opts, Dict):
        used_slurm_opts.update(slurm_opts)

    should_wait = used_slurm_opts.pop("wait")
    env_name = used_slurm_opts.pop("env_name")

    log_path = make_job_log_output_path(log_base_path)

    executor = get_executor(log_path, used_slurm_opts)

    job = executor.submit(
        wrap_function_with_env_setup, func_to_run, env_name, func_opts
    )

    if should_wait:
        job.wait()

    send_user_start_message(func_to_run.__name__, log_path, job, func_opts)


# Utils --------------------------------------------------------------------------------


def get_executor(log_path: Path, slurm_opts: Dict) -> submitit.AutoExecutor:
    """
    Return the executor object that defines parameters
    of the SLURM node to request and the path to
    logs.

    Parameters
    ----------
    log_path : Path
        Path to log the SLURM output to.

    slurm_opts : Dict
        The slurm options to run. See backend/hpc.py for an example.

    Returns
    -------
    executor : submitit.AutoExecutor
        submitit executor object defining requested SLURM
        node parameters.
    """
    print(f"\nThe SLURM batch output logs will " f"be saved to {log_path}\n")

    executor = submitit.AutoExecutor(
        folder=log_path,
    )

    executor.update_parameters(**slurm_opts)

    return executor


def wrap_function_with_env_setup(
    function: Callable, env_name: str, func_opts: Dict
) -> None:
    """
    Set up the environment from within the SLURM job, prior
    to running the processing function (e.g. run_full_pipeline).

    This is required to set up the conda environment within the job
    or the processing function will fail.

    Parameters
    ----------
    function : Callable
        A function to run in the SLURM job.

    env_name : str
        The name of the conda environment to run the job in

    func_opts : Dict
        All arguments passed to the public function.
    """
    print(f"\nrunning {function.__name__} with SLURM....\n")

    subprocess.run(
        f"module load miniconda; " f"source activate {env_name}; module load cuda",
        executable="/bin/bash",
        shell=True,
    )

    function(**func_opts)


def make_job_log_output_path(log_base_path: Path) -> Path:
    """
    The SLURM job logs are saved to a folder 'slurm_logs'.

    Parameters
    ----------
    log_base_path : Dict
        Path to the folder that will contain the folder 'slurm_logs'

    Returns
    -------
    log_path : Path
        The path to the SLURM log output folder for the current job.
        The logs are saved to a folder with machine datetime.
    """
    now = datetime.datetime.now()

    log_subpath = Path("slurm_logs") / f"{now.strftime('%Y-%m-%d_%H-%M-%S')}"

    log_path = log_base_path / log_subpath

    log_path.mkdir(exist_ok=True, parents=True)

    return log_path


def send_user_start_message(
    processing_function: str, log_path: Path, job: submitit.Job, func_opts: Dict
) -> None:
    """
    Convenience function to print important information
    regarding the SLURM job.

    Parameters
    ----------
    processing_function : str
        The function being run (i.e. run_full_pipeline, run_sorting)

    log_path : Path
        The path to the SLURM log output folder for the current job.

    job : submitit.job
        submitit.job object holding the SLURM job_id

    func_opts : Dict
        Keyword arguments passed to the function to run in SLURM.
    """
    _utils.message_user(
        f"---------------------- SLURM job submitted ----------------------\n"
        f"The function {processing_function} submitted to SLURM with job id {job.job_id}\n"
        f"Output will be logged to: {log_path}\n"
        f"Function called with arguments{func_opts}"
    )


def is_slurm_installed():
    slurm_installed = system_call_success("sinfo -v")
    return slurm_installed
