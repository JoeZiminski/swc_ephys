from pathlib import Path

from swc_ephys.pipeline.full_pipeline import run_full_pipeline

base_path = Path(
    r"/ceph/neuroinformatics/neuroinformatics/scratch/jziminski/ephys/test_data/steve_multi_run/1119617/time-short"
)
sub_name = "1119617"  # "1110925"  # "1119617"
run_names = [
    #  "1110925_test_shank1"
    "1119617_LSE1_shank12",
    "1119617_posttest1_shank12",
    "1119617_pretest1_shank12",
]

config_name = "default"
sorter = "kilosort3"  # "spykingcircus"

if __name__ == "__main__":
    run_full_pipeline(
        base_path,
        sub_name,
        run_names,
        config_name,
        sorter,
        existing_preprocessed_data="load_if_exists",
        existing_sorting_output="overwrite",
        overwrite_postprocessing=True,
        slurm_batch=False,
    )
