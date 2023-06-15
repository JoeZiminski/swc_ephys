from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Dict, List, Literal, Tuple, Union

if TYPE_CHECKING:
    from spikeinterface.core import BaseRecording

    from ..data_classes.preprocessing import PreprocessingData
    from ..data_classes.sorting import SortingData

import copy
import os.path
import subprocess
from pathlib import Path

import numpy as np
from spikeinterface import concatenate_recordings


def canonical_names(name: str) -> str:
    filenames = {
        "preprocessed_yaml": "preprocess_data_attributes.yaml",
    }
    return filenames[name]


def get_keys_first_char(
    data: Union[PreprocessingData, SortingData], as_int: bool = False
) -> Union[List[str], List[int]]:
    """
    Get the first character of all keys in a dictionary. Expected
    that the first characters are integers (as str type).

    Parameters
    ----------

    data : PreprocessingData
        swc_ephys PreprocessingData class holding filepath information.

    as_int : bool
        If True, the first character of the keys are cast to
        integer type.
    """
    return [int(key[0]) if as_int else key[0] for key in data.keys()]


def get_dict_value_from_step_num(
    data: Union[PreprocessingData, SortingData], step_num: str
) -> Tuple[BaseRecording, str]:
    """
    Get the value of the PreprocessingData dict from the preprocessing step number.

    PreprocessingData contain keys indicating the preprocessing steps,
    starting with the preprocessing step number.
    e.g. 0-raw, 1-raw-bandpass_filter, 2-raw_bandpass_filter-common_average

    Return the value of the dict (spikeinterface recording object)
    from the dict using only the step number

    Parameters
    ----------

    data : PreprocessingData
        swc_ephys PreprocessingData class holding filepath information.

    step_num : str
        The preprocessing step number to get the value (i.e. recording object)
        from.
    """
    if step_num == "last":
        pp_key_nums = get_keys_first_char(data, as_int=True)

        # complete overkill but this is critical
        step_num = str(int(np.max(pp_key_nums)))
        assert (
            int(step_num) == len(data.keys()) - 1
        ), "the last key has been taken incorrectly"

    select_step_pp_key = [key for key in data.keys() if key[0] == step_num]

    assert len(select_step_pp_key) == 1, "pp_key must always have unique first char"

    pp_key: str = select_step_pp_key[0]

    return data[pp_key], pp_key


def message_user(message: str, verbose: bool = True) -> None:
    """
    Method to interact with user.

    Parameters
    ----------

    message : str
        Message to print.

    verbose : bool
        The mode of the application. If verbose is False,
        nothing is printed.
    """
    if verbose:
        print(message)


# TODO: this is a little bit confusing because preprocessing
# class is always lazy. sorter class loads real data (still lazy though)
# it needs to be super explicitly that preprocessing is not undertakne
# until the binary object is written. For example, ti does not make
# sense to load the preprocessing data in the Preprocess data setting
# to check it. It is not crystallised until loaded into the SortingData
# class (this can be checked separately in visualise data).
# This needs to be super clear because it is a powerful but confusing
# aspect of spikeinterface.


def concatenate_runs(recording: BaseRecording) -> BaseRecording:
    """
    Convenience function to concatenate the segments
    of a recording object.

    Parameters
    ----------

    recording : BaseRecording
        A spikeinterface recording object.
    """
    message_user(f"Conatenating {recording.get_num_segments()} into a single segment.")

    concatenated_recording = concatenate_recordings([recording])

    return concatenated_recording


def get_local_sorter_path(sorter: str) -> Path:
    """
    Return the path to a sorter singularity image. The sorters are
    stored by swc_ephys in the home folder.

    Parameters
    ----------

    sorter : str
        The name of the sorter to get the path to (e.g. kilosort2_5)
    """
    local_path = (
        Path.home() / ".swc_ephys" / "sorter_images" / get_sorter_image_name(sorter)
    )
    local_path.parent.mkdir(exist_ok=True, parents=True)
    return local_path


def get_hpc_sorter_path(sorter: str) -> Path:
    """
    Return the path to the sorter image on the HCP.

    Parameters
    ----------

    sorter : str
        The name of the sorter to get the path to (e.g. kilosort2_5)
    """
    base_path = Path("/ceph/neuroinformatics/neuroinformatics/scratch/sorter_images")
    return base_path / sorter / get_sorter_image_name(sorter)


def get_sorter_image_name(sorter: str) -> str:
    """
    Get the sorter image name, as defined by how
    SpikeInterface names the images it provides.

    Parameters
    ----------

    sorter : str
        The name of the sorter to get the path to (e.g. kilosort2_5)
    """
    if "kilosort" in sorter:
        sorter_name = f"{sorter}-compiled-base.sif"
    else:
        if sorter == "spykingcircus":
            sorter = "spyking-circus"
        sorter_name = f"{sorter}-base.sif"
    return sorter_name


def check_singularity_install() -> bool:
    """
    Check the system install of singularity.
    Return bool indicating if singularity is installed.
    """
    try:
        subprocess.run("singularity --version", shell=True)
        return True
    except FileNotFoundError:
        return False


def sort_list_of_paths_by_datetime_order(list_of_paths: List[Path]) -> List[Path]:
    """
    Given a list of paths to folders, sort the paths by the creation
    time of the folders they point to. Return the sorted
    list of paths.

    Parameters
    ----------

    list_of_paths : List[Path]
        A list of paths to sort into datetime order
    """
    list_of_paths_by_creation_time = copy.deepcopy(list_of_paths)
    list_of_paths_by_creation_time.sort(key=os.path.getctime)

    return list_of_paths_by_creation_time


def list_of_files_are_in_datetime_order(
    list_of_paths: List[Path], creation_or_modification: str = "creation"
) -> bool:
    """
    Assert whether a list of paths are in order. By default, check they are
    in order by creation date. Can also check if they are ordered by
    modification date.

    Parameters
    ----------

    list_of_paths : List[Path]
        A list of paths to sort into datetime order.

    creation_or_modification : str
        If "creation", check the list of paths are ordered by creation datetime.
        Otherwise if "modification", check they are sorterd by modification datetime.
    """
    assert creation_or_modification in [
        "creation",
        "modification",
    ], "creation_or_modification must be 'creation' or 'modification."

    filter: Callable
    filter = (
        os.path.getmtime if creation_or_modification == "creation" else os.path.getctime
    )

    list_of_paths_by_time = copy.deepcopy(list_of_paths)
    list_of_paths_by_time.sort(key=filter)

    return list_of_paths == list_of_paths_by_time


def make_preprocessing_plot_title(
    run_name: str,
    full_key: str,
    shank_idx: int,
    recording_to_plot: BaseRecording,
    total_used_shanks: int,
) -> str:
    """
    For visualising data, make the plot titles (with headers in bold). If
    more than one shank is used, the title will also contain information
    on the displayed shank.

    Parameters
    ----------
    run_name : TODO xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

    full_key : str
        The full preprocessing key (as defined in preprocess.py)

    shank_idx : int
        The SpikeInterface group number representing the shank number.

    recording_to_plot : BaseRecording
        The SpikeInterface recording object that is being displayed.

    total_used_shanks : int
        The total number of shanks used in the recording. For a 4-shank probe,
        this could be between 1 - 4 if not all shanks are mapped.
    """
    plot_title = (
        r"$\bf{Run \ name:}$" + f"{run_name}"
        "\n" + r"$\bf{Preprocessing \ step:}$" + f"{full_key}"
    )
    if total_used_shanks > 1:
        plot_title += (
            "\n"
            + r"$\bf{Shank \ group:}$"
            + f"{shank_idx}, "
            + r"$\bf{Num \ channels:}$"
            + f"{recording_to_plot.get_num_channels()}"
        )
    return plot_title


def cast_pp_steps_values(
    pp_steps: Dict, list_or_tuple: Literal["list", "tuple"]
) -> None:
    """"""
    assert list_or_tuple in ["list", "tuple"], "Must cast to `list` or `tuple`."
    func = tuple if list_or_tuple == "tuple" else list

    for key in pp_steps.keys():
        pp_steps[key] = func(pp_steps[key])


# Misc. ----------------------------------------------------------------------------


def get_probe_group_num(data: Union[PreprocessingData, SortingData]) -> int:
    """
    This is shank num

    TODO
    ---
    This is getting out of scope for this class, which should really be
    file-path related. Understand how shank index on the probe property
    maps to real-world shank
    """
    num_groups = np.unique(data[data.init_data_key].get_property("group")).size
    return num_groups
