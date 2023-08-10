from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Literal, Tuple, Union

import numpy as np
import yaml

if TYPE_CHECKING:
    from spikeinterface.core import BaseRecording

    from ..data_classes.preprocessing import PreprocessingData
    from ..data_classes.sorting import SortingData


def get_logging_path(base_path, sub_name):
    return Path(base_path) / "derivatives" / sub_name / "logs"


def canonical_names(name: str) -> str:
    """
    Store the canonical names e.g. filenames, tags
    that are used throughout the project. This setup
    means filenames can be edited without requiring
    extensive code changes.

    Parameters
    ----------
    name : str
        short-hand name of the full name of interest.

    Returns
    -------
    filenames[name] : str
        The full name of interest e.g. filename.

    """
    filenames = {
        "preprocessed_yaml": "preprocessing_info.yaml",
        "sorting_yaml": "sorting_info.yaml",
    }
    return filenames[name]


def get_formatted_datetime():
    return datetime.now().strftime("%Y-%m-%d_%H%M%S")


def get_keys_first_char(
    data: Union[PreprocessingData, SortingData], as_int: bool = False
) -> Union[List[str], List[int]]:
    """
    Get the first character of all keys in a dictionary. Expected
    that the first characters are integers (as str type).

    Parameters
    ----------
    data : Union[PreprocessingData, SortingData]
        spikewrap PreprocessingData class holding filepath information.

    as_int : bool
        If True, the first character of the keys are cast to
        integer type.

    Returns
    -------
    list_of_numbers : Union[List[str], List[int]]
        A list of numbers of string or integer type, that are
        the first numbers of the Preprocessing / Sorting Data
        .data dictionary keys.
    """
    list_of_numbers = [
        int(key.split("-")[0]) if as_int else key.split("-")[0] for key in data.keys()
    ]
    return list_of_numbers


def get_dict_value_from_step_num(
    data: Union[PreprocessingData, SortingData], step_num: str
) -> Tuple[BaseRecording, str]:
    """
    Get the value of the PreprocessingData dict from the preprocessing step number.

    PreprocessingData contain keys indicating the preprocessing steps,
    starting with the preprocessing step number.
    e.g. 0-raw, 1-raw-bandpass_filter, 2-raw_bandpass_filter-common_average

    Return the value of the dict (spikeinterface recording object)
    from the dict using only the step number.

    Parameters
    ----------
    data : Union[PreprocessingData, SortingData]
        spikewrap PreprocessingData class holding filepath information.

    step_num : str
        The preprocessing step number to get the value (i.e. recording object)
        from.

    Returns
    -------
    dict_value : BaseRecording
        The SpikeInterface recording stored in the dict at the
        given preprocessing step number.

    pp_key : str
        The key of the preprocessing dict at the given
        step number.
    """
    if step_num == "last":
        pp_key_nums = get_keys_first_char(data, as_int=True)

        # Complete overkill as a check but this is critical.
        step_num = str(int(np.max(pp_key_nums)))
        assert (
            int(step_num) == len(data.keys()) - 1
        ), "the last key has been taken incorrectly"

    select_step_pp_key = [key for key in data.keys() if key.split("-")[0] == step_num]

    try:
        assert len(select_step_pp_key) == 1, "pp_key must always have unique first char"
    except:
        breakpoint()
    pp_key: str = select_step_pp_key[0]
    dict_value = data[pp_key]

    return dict_value, pp_key


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
        print(f"\n{message}")


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
    run_name : str
        The name of the preprocessing run (e.g. "1-phase_shift").

    full_key : str
        The full preprocessing key (as defined in preprocess.py).

    shank_idx : int
        The SpikeInterface group number representing the shank number.

    recording_to_plot : BaseRecording
        The SpikeInterface recording object that is being displayed.

    total_used_shanks : int
        The total number of shanks used in the recording. For a 4-shank probe,
        this could be between 1 - 4 if not all shanks are mapped.

    Returns
    -------
    plot_title : str
        The formatted plot title.
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
    """
    The settings in the pp_steps dictionary that defines the options
    for preprocessing should be stored in Tuple as they are not to
    be edited. However, when dumping Tuple to .yaml, there are tags
    displayed on the .yaml file which are very ugly.

    These are not shown when storing list, so this function serves
    to convert Tuple and List values in the preprocessing dict when
    loading / saving the preprocessing dict to .yaml files. This
    function converts `pp_steps` in place.

    Parameters
    ----------
    pp_steps : Dict
        The dictionary indicating the preprocessing steps to perform.

    list_or_tuple : Literal["list", "tuple"]
        The direction to convert (i.e. if "tuple", will convert to Tuple).
    """
    assert list_or_tuple in ["list", "tuple"], "Must cast to `list` or `tuple`."
    func = tuple if list_or_tuple == "tuple" else list

    for key in pp_steps.keys():
        pp_steps[key] = func(pp_steps[key])


def dump_dict_to_yaml(filepath, dict_):
    with open(
        filepath,
        "w",
    ) as file_to_save:
        yaml.dump(dict_, file_to_save, sort_keys=False)


def load_dict_from_yaml(filepath):
    with open(filepath, "r") as file:
        loaded_dict = yaml.safe_load(file)
    return loaded_dict
