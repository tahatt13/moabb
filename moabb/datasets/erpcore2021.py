"""
Erpcore2021 dataset

# Author: Taha Habib <tahahb123@gmail.com>

# License: BSD (3-clause)
"""

import os
import warnings
from abc import abstractmethod
from functools import partialmethod
from pathlib import Path

import mne
import numpy as np
import pandas as pd
import pooch
from mne.datasets import fetch_dataset
from mne_bids import BIDSPath, read_raw_bids

from moabb.datasets.base import BaseDataset


OSF_BASE_URL = "https://files.osf.io/v1/resources/"

# Ids for the buckets on OSF and the folder OSF hash
# To download data from osf for each task
OSF_IDS = {
    "ERN": ["q6gwp", "600df65e75226b017d517f6d"],
    "LRP": ["28e6c", "600dffbf327cbe019d7b6a0c"],
    "MMN": ["5q4xs", "6007896286541a091d14b102"],
    "N170": ["pfde9", "60060f8ae80d370812a5b15d"],
    "N2pc": ["yefrq", "60077f09ba010908a4892b3a"],
    "N400": ["29xpq", "6007857286541a092614c5d3"],
    "P3": ["etdkz", "60077b04ba010908a78927e9"],
}

# URLs for JSON files containing the original value mapping
OSF_JSON = {
    "N170": "pfde9/providers/osfstorage/60077b01ba010908a78927da?",
    "MMN": "5q4xs/providers/osfstorage/60078d9e86541a092c15ebbe?",
    "N2pc": "yefrq/providers/osfstorage/6007856fba010908a2892c48?",
    "P3": "etdkz/providers/osfstorage/60077f07e80d3708e6a57d56?",
    "N400": "29xpq/providers/osfstorage/60078961e80d3708e3a57da1?",
    "LRP": "28e6c/providers/osfstorage/600e039db6416f01c5b03286?",
    "ERN": "q6gwp/providers/osfstorage/600dfa3eb6416f01b7b0467f?",
}


DATASET_PARAMS = {
    task: dict(
        archive_name=f"ERPCORE2021_{task}.zip",
        url=OSF_BASE_URL + f"{osf[0]}/providers/osfstorage/{osf[1]}/?zip=",
        folder_name=f"MNE-erpcore{task.lower()}2021-data",
        dataset_name=f"MNE-erpcore{task.lower()}2021",
        hash=None,
        config_key=f"MNE_ERPCORE_{task.upper()}_PATH",
    )
    for task, osf in OSF_IDS.items()
}


class Erpcore2021(BaseDataset):
    """Abstract base dataset class for Erpcore2021.

    Datasets [1]_ from the article [2]_.

    **Dataset Description**

    The ERP CORE dataset includes data from 40 neurotypical young adults
    (25 female, 15 male; Mean years of age = 21.5, SD = 2.87, Range 18–30; 38 right handed)
    from the University of California. Each participant had native English competence and normal
    color perception, normal or corrected-to-normal vision, and no history of neurological injury
    or disease (as indicated by self-report). They participated in six 10-minutes optimized
    experiments designed to measure seven widely used ERP components: N170, Mismatch Negativity
    (MMN), N2pc, N400, P3, Lateralized Readiness Potential (LRP), and Error-Related Negativity
    (ERN). These experiments were conducted to standardize ERP paradigms and protocols across
    studies.

    **Experimental procedures**:
    - **N170**: Subjects viewed faces and objects to elicit the N170 component. In this task,
    an image of a face, car, scrambled face, or scrambled car was presented on each trial in
    the center of the screen, and participants responded whether the stimulus was an “object”
    (face or car) or a “texture” (scrambled face or scrambled car).
    - **MMN**: Subjects were exposed to a sequence of auditory stimuli to evoke the mismatch
    negativity response, indicating automatic detection of deviant sounds.  Standard tones
    (presented at 80 dB, with p = .8) and deviant tones (presented at 70 dB, with p = .2)
    were presented over speakers while participants watched a silent video and ignored the tones.
    - **N2pc**: Participants were given a target color of pink or blue at the beginning of a
    trial block, and responded on each trial whether the gap in the target color square was
    on the top or bottom.
    - **N400**: On each trial, a red prime word was followed by a green target word.
    Participants responded whether the target word was semantically related or unrelated
    to the prime word.
    - **P3**: The letters A, B, C, D, and E were presented in random order (p = .2 for each
    letter). One letter was designated the target for a given block of trials, and the other
    4 letters were non-targets. Thus, the probability of the target category was .2, but the
    same physical stimulus served as a target in some blocks and a nontarget in others.
    Participants responded whether the letter presented on each trial was the target or a
    non-target for that block.
    - **LRP & ERN**: A central arrowhead pointing to the left or right was flanked on both
    sides by arrowheads that pointed in the same direction (congruent trials) or the opposite
    direction (incongruent trials). Participants indicated the direction of the central
    arrowhead on each trial with a left- or right-hand buttonpress.


    The continuous EEG was recorded using a Biosemi ActiveTwo recording system with active
    electrodes (Biosemi B.V., Amsterdam, the Netherlands). Recording from 30 scalp electrodes,
    mounted in an elastic cap and placed according to the International 10/20 System (FP1, F3,
    F7, FC3, C3, C5, P3, P7, P9, PO7, PO3, O1, Oz, Pz, CPz, FP2, Fz, F4, F8, FC4, FCz, Cz, C4,
    C6, P4, P8, P10, PO8, PO4, O2; see Supplementary Fig. S1). The common mode sense (CMS)
    electrode was located at PO1, and the driven right leg (DRL) electrode was located at PO2.
    The horizontal electrooculogram (HEOG) was recorded from electrodes placed lateral to the
    external canthus of each eye. The vertical electrooculogram (VEOG) was recorded from an
    electrode placed below the right eye. Signals were incidentally also recorded from 37 other
    sites, but these sites were not monitored during the recording and are not included in
    the ERP CORE data set. All signals were low-pass filtered using a fifth order sinc filter
    with a half-power cutoff at 204.8 Hz and then digitized at 1024 Hz with 24 bits of resolution.
    The signals were recorded in single-ended mode (i.e., measuring the voltage between the active
    and ground electrodes without the use of a reference), and referencing was performed offline.

    References
    ----------
    .. [1] Emily S. Kappenman, Jaclyn L. Farrens, Wendy Zhang, Andrew X. Stewart, Steven J. Luck.
        (2020). ERP CORE: An open resource for human event-related potential research. NeuroImage.
        DOI: https://doi.org/10.18115/D5JW4R

    .. [2] Emily S. Kappenman, Jaclyn L. Farrens, Wendy Zhang, Andrew X. Stewart, Steven J. Luck.
        ERP CORE: An open resource for human event-related potential research.
        DOI: https://doi.org/10.1016/j.neuroimage.2020.117465

    """

    def __init__(self, task):
        if task == "N170":
            interval = (-0.2, 0.8)
            events = {"Target": 1, "NonTarget": 2}
        elif task == "MMN":
            interval = (-0.2, 0.8)
            events = {"Target": 1, "NonTarget": 2}
        elif task == "N2pc":
            interval = (-0.2, 0.8)
            events = {"Target": 1, "NonTarget": 2}
        elif task == "P3":
            interval = (-0.2, 0.8)
            events = {"Target": 1, "NonTarget": 2}
        elif task == "N400":
            interval = (-0.2, 0.8)
            events = {"Target": 1, "NonTarget": 2}
        elif task == "ERN":
            interval = (-0.8, 0.2)
            events = {"Target": 1, "NonTarget": 2}
        elif task == "LRP":
            interval = (-0.6, 0.4)
            events = {"Target": 1, "NonTarget": 2}
        else:
            raise ValueError(f"Unknown task {task}")

        self.task = task

        super().__init__(
            subjects=list(range(1, 40 + 1)),
            sessions_per_subject=1,
            events=events,
            code=f"Erpcore2021-{task}",
            interval=interval,
            paradigm="p300",
            doi="10.1016/j.neuroimage.2020.117465",
        )

    def get_meta_data(self, subject):
        """
        Retrieve original events mapping and original event data for a given subject.

        Parameters
        ----------
        subject : int
            The subject number for which to retrieve data.

        Returns
        -------
        tuple A tuple containing the original events mapping
        and the original events DataFrame.
        """
        # Get the path to the events file for the subject
        events_path = self.events_path(subject)
        # Read the events data
        original_events = pd.read_csv(events_path, sep="\t")

        # Read the JSON file containing the original value mapping
        json_file_data = pd.read_json(OSF_BASE_URL + OSF_JSON[self.task])

        # Extract the value mapping
        original_mapping = json_file_data["value"]["Levels"]

        return original_mapping, original_events

    def _get_single_subject_data(self, subject):
        """Return the data of a single subject.

        Parameters
        ----------
        subject : int
            The subject number to fetch data for.

        Returns
        -------
        dict
            A dictionary containing the raw data for the subject.
        """
        # Get the file path for the subject's data
        file_path = self.data_path(subject)[0]

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            # Read the subject's raw data and set the montage
            raw = read_raw_bids(bids_path=file_path, verbose=False)
            raw.load_data()  # Preload the data because read_raw_bids does not load it
            raw = raw.set_montage("standard_1020", match_case=False)

        # Shift the stimulus event codes forward in time
        # to account for the LCD monitor delay
        # (26 ms on our monitor, as measured with a photosensor).
        if self.task != "MMN":
            raw.annotations.onset = raw.annotations.onset + 0.026

        events_path = self.events_path(subject)
        raw = self.handle_events_reading(events_path, raw)

        # There is only one session
        sessions = {"0": {"0": raw}}

        return sessions

    def data_path(
        self, subject, path=None, force_update=False, update_path=None, verbose=None
    ):
        """
        Return the data BIDS paths of a single subject.

        Parameters
        ----------
        subject : int
            The subject number to fetch data for.
        path : None | str
            Location of where to look for the data storing location. If None,
            the environment variable or config parameter MNE_(dataset) is used.
            If it doesn’t exist, the “~/mne_data” directory is used. If the
            dataset is not found under the given path, the data
            will be automatically downloaded to the specified folder.
        force_update : bool
            Force update of the dataset even if a local copy exists.
        update_path : bool | None
            If True, set the MNE_DATASETS_(dataset)_PATH in mne-python config
            to the given path.
            If None, the user is prompted.
        verbose : bool, str, int, or None
            If not None, override default verbose level (see mne.verbose()).

        Returns
        -------
        list
            A list containing the BIDSPath object for the subject's data file.
        """
        if subject not in self.subject_list:
            raise ValueError("Invalid subject number")

        # Download and extract the dataset
        dataset_path = self.download_and_extract(
            path=path, force_update=force_update, update_path=update_path
        )

        # Create a BIDSPath object for the subject
        bids_path = BIDSPath(
            subject=f"{subject:03d}",
            task=self.task,
            suffix="eeg",
            datatype="eeg",
            root=dataset_path,
        )

        subject_paths = [bids_path]

        return subject_paths

    def download_and_extract(self, path=None, force_update=False, update_path=None):
        """
        Download and extract the dataset.

        Parameters
        ----------
        path : str | None
            The path to the directory where the dataset should be downloaded.
            If None, the default directory is used.
        force_update : bool
            Force update of the dataset even if a local copy exists.
        update_path: bool | None
            If True, set the MNE_DATASETS_(dataset)_PATH in mne-python config
            to the given path.

        Returns
        -------
        path : str
            The dataset path.
        """
        if path is not None:
            path = Path(path) / DATASET_PARAMS[self.task]["folder_name"]
        else:
            # Default path is in the user's home directory under 'mne_data'
            path = Path.home() / "mne_data" / DATASET_PARAMS[self.task]["folder_name"]

        # Check if the dataset already exists and force_update is False
        if not force_update and path.exists():
            return path

        # Download and extract the dataset
        _ = fetch_dataset(
            DATASET_PARAMS[self.task],
            path=path,
            force_update=force_update,
            update_path=update_path,
            processor=pooch.Unzip(extract_dir=path),
        )
        return path

    def events_path(self, subject):
        """
        Get the path to the events file for a given subject.

        Parameters
        ----------
        subject : int
            The subject number for which to get the events file path.

        Returns
        -------
        str
            The path to the events file.
        """
        # Get the BIDSPath object for the subject
        bids_path = self.data_path(subject)[0]
        # Construct the path to the events file
        events_path = os.path.join(
            bids_path.directory,
            bids_path.update(suffix="events", extension=".tsv").basename,
        )
        return events_path

    def handle_events_reading(self, events_path, raw):
        """Read associated events.tsv and populate raw with annotations.

        Parameters
        ----------
        events_path : str
            The path to the events file.
        raw : mne.io.Raw
            The raw EEG data object.

        Returns
        -------
        mne.io.Raw
            The updated raw EEG data object with annotations.
        """

        events_df = pd.read_csv(events_path, sep="\t")

        # Encode the events
        event_category, mapping = self.encoding(events_df=events_df)

        # Create the event array using the sample column and the encoded
        # event categories
        events = np.column_stack(
            (events_df["sample"].values, np.zeros(len(event_category)), event_category)
        )

        # Create and set annotations from the events
        annotations = mne.annotations_from_events(
            events, sfreq=raw.info["sfreq"], event_desc=mapping
        )
        raw.set_annotations(annotations)

        return raw

    @staticmethod
    @abstractmethod
    def encode_event(row: str):
        """
        Encode a single event values based on the task-specific criteria.

        Parameters
        ----------
        row : pd.Series
            A row of the events DataFrame.

        Returns
        -------
        str
            Encoded event value.
        """

    @abstractmethod
    def encoding(self, events_df: pd.DataFrame):
        """
        Encode the column value in the events DataFrame.

        Parameters
        ----------
        events_df : DataFrame
            DataFrame containing the events information.

        Returns
        -------
        tuple
            A tuple containing the encoded event values and the mapping dictionary.
        """


class Erpcore2021_N170(Erpcore2021):
    """
    .. admonition:: Dataset summary

        ================== ======== ======= ================= =============== =============== ===========
        Name               #Subj    #Chan   #Trials / class   Trials length   Sampling rate   #Sessions
        ================== ======== ======= ================= =============== =============== ===========
        Erpcore2021_N170   40       30      240 NT / 80 T     4s              1024Hz          1
        ================== ======== ======= ================= =============== =============== ===========

    Description of the task:

    Subjects viewed faces and objects to elicit the N170 component. In this task,
    an image of a face, car, scrambled face, or scrambled car was presented on each trial in
    the center of the screen, and participants responded whether the stimulus was an “object”
    (face or car) or a “texture” (scrambled face or scrambled car).

    """

    __init__ = partialmethod(Erpcore2021.__init__, "N170")

    @staticmethod
    def encode_event(row):
        value = row["value"]
        # Stimulus - faces
        if 1 <= value <= 40:
            return "Stimulus - faces"
        elif 41 <= value <= 80:
            return "Stimulus - cars"
        elif 101 <= value <= 140:
            return "Stimulus - scrambled faces"
        elif 141 <= value <= 180:
            return "Stimulus - scrambled cars"

    def encoding(self, events_df):
        # Drop rows corresponding to the responses
        events_df.drop(events_df[events_df["value"].isin([201, 202])].index, inplace=True)

        # Apply the encoding function to each row
        encoded_column = events_df.apply(self.encode_event, axis=1)

        # Create the mapping dictionary
        mapping = {
            "Stimulus - faces": "Target",
            "Stimulus - cars": "NonTarget",
            "Stimulus - scrambled faces": "NonTarget",
            "Stimulus - scrambled cars": "NonTarget",
        }
        return encoded_column.values, mapping


class Erpcore2021_MMN(Erpcore2021):
    """
    ================= ======== ======= ================= =============== =============== ===========
    Name              #Subj    #Chan   #Trials / class   Trials length   Sampling rate   #Sessions
    ================= ======== ======= ================= =============== =============== ===========
    Erpcore2021_MMN   40       30      800 NT / 200 T    1s              1024Hz          1
    ================= ======== ======= ================= =============== =============== ===========

    Description of the task:

    Subjects were exposed to a sequence of auditory stimuli to evoke the mismatch
    negativity response, indicating automatic detection of deviant sounds.  Standard tones
    (presented at 80 dB, with p = .8) and deviant tones (presented at 70 dB, with p = .2)
    were presented over speakers while participants watched a silent video and ignored the tones.
    """

    __init__ = partialmethod(Erpcore2021.__init__, "MMN")

    @staticmethod
    def encode_event(row):
        value = row["value"]
        if value == 80:
            return "Stimulus - standard"
        elif value == 180:
            return "Stimulus - first stream of standards"
        elif value == 70:
            return "Stimulus - deviant"

    def encoding(self, events_df):
        # Remove rows which correspond to trial_type = STATUS
        events_df.drop(events_df[events_df["trial_type"] == "STATUS"].index, inplace=True)
        # Apply the encoding function to each row
        encoded_column = events_df.apply(self.encode_event, axis=1)

        # Create the mapping dictionary
        mapping = {
            "Stimulus - standard": "Target",
            "Stimulus - first stream of standards": "Target",
            "Stimulus - deviant": "NonTarget",
        }

        return encoded_column.values, mapping


class Erpcore2021_N2pc(Erpcore2021):
    """
    ================== ======== ======= ================= =============== =============== ===========
    Name               #Subj    #Chan   #Trials / class   Trials length   Sampling rate   #Sessions
    ================== ======== ======= ================= =============== =============== ===========
    Erpcore2021_N2pc   40       30      160 NT / 160 T    1s              1024Hz          1
    ================== ======== ======= ================= =============== =============== ===========

    Description of the task:

    Participants were given a target color of pink or blue at the beginning of a
    trial block, and responded on each trial whether the gap in the target color square was
    on the top or bottom.
    """

    __init__ = partialmethod(Erpcore2021.__init__, "N2pc")

    @staticmethod
    def encode_event(row):
        value = row["value"]

        if value == 111:
            return "Stimulus - target blue, target left, gap at top"
        elif value == 112:
            return "Stimulus - target blue, target left, gap at bottom"
        elif value == 211:
            return "Stimulus - target pink, target left, gap at top"
        elif value == 212:
            return "Stimulus - target pink, target left, gap at bottom"
        elif value == 121:
            return "Stimulus - target blue, target right, gap at top"
        elif value == 122:
            return "Stimulus - target blue, target right, gap at bottom"
        elif value == 221:
            return "Stimulus - target pink, target right, gap at top"
        elif value == 222:
            return "Stimulus - target pink, target right, gap at bottom"

    def encoding(self, events_df):

        # Drop rows corresponding to the responses
        events_df.drop(events_df[events_df["value"].isin([201, 202])].index, inplace=True)

        # Apply the encoding function to each row
        encoded_column = events_df.apply(self.encode_event, axis=1)

        # Create the mapping dictionary
        # Target : Stimulus with target at left,
        # NonTarget : Stimulus with target at right

        mapping = {
            "Stimulus - target blue, target left, gap at top": "Target",
            "Stimulus - target blue, target left, gap at bottom": "Target",
            "Stimulus - target pink, target left, gap at top": "Target",
            "Stimulus - target pink, target left, gap at bottom": "Target",
            "Stimulus - target blue, target right, gap at top": "NonTarget",
            "Stimulus - target blue, target right, gap at bottom": "NonTarget",
            "Stimulus - target pink, target right, gap at top": "NonTarget",
            "Stimulus - target pink, target right, gap at bottom": "NonTarget",
        }

        return encoded_column.values, mapping


class Erpcore2021_P3(Erpcore2021):
    """
    ================ ======== ======= ================= =============== =============== ===========
    Name             #Subj    #Chan   #Trials / class   Trials length   Sampling rate   #Sessions
    ================ ======== ======= ================= =============== =============== ===========
    Erpcore2021_P3   40       30      160 NT / 40 T     1s              1024Hz          1
    ================ ======== ======= ================= =============== =============== ===========

    Description of the task:

    The letters A, B, C, D, and E were presented in random order (p = .2 for each
    letter). One letter was designated the target for a given block of trials, and the other
    4 letters were non-targets. Thus, the probability of the target category was .2, but the
    same physical stimulus served as a target in some blocks and a nontarget in others.
    Participants responded whether the letter presented on each trial was the target or a
    non-target for that block.
    """

    __init__ = partialmethod(Erpcore2021.__init__, "P3")

    @staticmethod
    # Keeping only the stimulus without the response
    def encode_event(row):
        value = row["value"]
        if value == 11:
            return "Stimulus - block target A, trial stimulus A"
        elif value == 22:
            return "Stimulus - block target B, trial stimulus B"
        elif value == 33:
            return "Stimulus - block target C, trial stimulus C"
        elif value == 44:
            return "Stimulus - block target D, trial stimulus D"
        elif value == 55:
            return "Stimulus - block target E, trial stimulus E"
        elif value == 21:
            return "Stimulus - block target B, trial stimulus A"
        elif value == 31:
            return "Stimulus - block target C, trial stimulus A"
        elif value == 41:
            return "Stimulus - block target D, trial stimulus A"
        elif value == 51:
            return "Stimulus - block target E, trial stimulus A"
        elif value == 12:
            return "Stimulus - block target A, trial stimulus B"
        elif value == 32:
            return "Stimulus - block target C, trial stimulus B"
        elif value == 42:
            return "Stimulus - block target D, trial stimulus B"
        elif value == 52:
            return "Stimulus - block target E, trial stimulus B"
        elif value == 13:
            return "Stimulus - block target A, trial stimulus C"
        elif value == 23:
            return "Stimulus - block target B, trial stimulus C"
        elif value == 43:
            return "Stimulus - block target D, trial stimulus C"
        elif value == 53:
            return "Stimulus - block target E, trial stimulus C"
        elif value == 14:
            return "Stimulus - block target A, trial stimulus D"
        elif value == 24:
            return "Stimulus - block target B, trial stimulus D"
        elif value == 34:
            return "Stimulus - block target C, trial stimulus D"
        elif value == 54:
            return "Stimulus - block target E, trial stimulus D"
        elif value == 15:
            return "Stimulus - block target A, trial stimulus E"
        elif value == 25:
            return "Stimulus - block target B, trial stimulus E"
        elif value == 35:
            return "Stimulus - block target C, trial stimulus E"
        elif value == 45:
            return "Stimulus - block target D, trial stimulus E"

    def encoding(self, events_df):

        # Drop rows corresponding to the responses
        events_df.drop(events_df[events_df["value"].isin([201, 202])].index, inplace=True)

        # Apply the encoding function to each row
        encoded_column = events_df.apply(self.encode_event, axis=1)

        # Create the mapping dictionary
        # Target : Stimulus matching the target letter,
        # NonTarget : Stimulus not matching the target letter
        mapping = {
            "Stimulus - block target A, trial stimulus A": "Target",
            "Stimulus - block target B, trial stimulus B": "Target",
            "Stimulus - block target C, trial stimulus C": "Target",
            "Stimulus - block target D, trial stimulus D": "Target",
            "Stimulus - block target E, trial stimulus E": "Target",
            "Stimulus - block target B, trial stimulus A": "NonTarget",
            "Stimulus - block target C, trial stimulus A": "NonTarget",
            "Stimulus - block target D, trial stimulus A": "NonTarget",
            "Stimulus - block target E, trial stimulus A": "NonTarget",
            "Stimulus - block target A, trial stimulus B": "NonTarget",
            "Stimulus - block target C, trial stimulus B": "NonTarget",
            "Stimulus - block target D, trial stimulus B": "NonTarget",
            "Stimulus - block target E, trial stimulus B": "NonTarget",
            "Stimulus - block target A, trial stimulus C": "NonTarget",
            "Stimulus - block target B, trial stimulus C": "NonTarget",
            "Stimulus - block target D, trial stimulus C": "NonTarget",
            "Stimulus - block target E, trial stimulus C": "NonTarget",
            "Stimulus - block target A, trial stimulus D": "NonTarget",
            "Stimulus - block target B, trial stimulus D": "NonTarget",
            "Stimulus - block target C, trial stimulus D": "NonTarget",
            "Stimulus - block target E, trial stimulus D": "NonTarget",
            "Stimulus - block target A, trial stimulus E": "NonTarget",
            "Stimulus - block target B, trial stimulus E": "NonTarget",
            "Stimulus - block target C, trial stimulus E": "NonTarget",
            "Stimulus - block target D, trial stimulus E": "NonTarget",
        }

        return encoded_column.values, mapping


class Erpcore2021_N400(Erpcore2021):
    """
    ================== ======== ======= ================= =============== =============== ===========
    Name               #Subj    #Chan   #Trials / class   Trials length   Sampling rate   #Sessions
    ================== ======== ======= ================= =============== =============== ===========
    Erpcore2021_N400   40       30      60 NT / 60 T      1s              1024Hz          1
    ================== ======== ======= ================= =============== =============== ===========

    Description of the task:

    On each trial, a red prime word was followed by a green target word.
    Participants responded whether the target word was semantically related or unrelated
    to the prime word.
    """

    __init__ = partialmethod(Erpcore2021.__init__, "N400")

    @staticmethod
    def encode_event(row):
        # We removed the stimulus corresponding to the prime word
        # and only kept the stimulus corresponding to the target word
        value = row["value"]
        if value == 211:
            return "Stimulus - target word, related word pair, list 1"
        elif value == 212:
            return "Stimulus - target word, related word pair, list 2"
        elif value == 221:
            return "Stimulus - target word, unrelated word pair, list 1"
        elif value == 222:
            return "Stimulus - target word, unrelated word pair, list 2"

    def encoding(self, events_df):

        # Drop rows corresponding to the responses
        events_df.drop(
            events_df[events_df["value"].isin([111, 112, 121, 122, 201, 202])].index,
            inplace=True,
        )

        # Apply the encoding function to each row
        encoded_column = events_df.apply(self.encode_event, axis=1)

        # Create the mapping dictionary
        # Target : Stimulus - related word pair,
        # NonTarget : Stimulus - unrelated word pair
        mapping = {
            "Stimulus - target word, related word pair, list 1": "Target",
            "Stimulus - target word, related word pair, list 2": "Target",
            "Stimulus - target word, unrelated word pair, list 1": "NonTarget",
            "Stimulus - target word, unrelated word pair, list 2": "NonTarget",
        }

        return encoded_column.values, mapping


class Erpcore2021_ERN(Erpcore2021):
    """
    ================= ======== ======= ================= =============== =============== ===========
    Name              #Subj    #Chan   #Trials / class   Trials length   Sampling rate   #Sessions
    ================= ======== ======= ================= =============== =============== ===========
    Erpcore2021_ERN   40       30      ~ 400 All         1s              1024Hz          1
    ================= ======== ======= ================= =============== =============== ===========

    Description of the task:

    A central arrowhead pointing to the left or right was flanked on both
    sides by arrowheads that pointed in the same direction (congruent trials) or the opposite
    direction (incongruent trials). Participants indicated the direction of the central
    arrowhead on each trial with a left- or right-hand buttonpress.
    """

    __init__ = partialmethod(Erpcore2021.__init__, "ERN")

    @staticmethod
    def encode_event(row):
        # We only kept the stimulus corresponding to the response
        value = row["value"]
        if value == 111:
            return "Response - left, compatible flankers, target left"
        elif value == 121:
            return "Response - left, incompatible flankers, target left"
        elif value == 212:
            return "Response - right, compatible flankers, target right"
        elif value == 222:
            return "Response - right, incompatible flankers, target right"
        elif value == 112:
            return "Response - left, compatible flankers, target right"
        elif value == 122:
            return "Response - left, incompatible flankers, target right"
        elif value == 211:
            return "Response - right, compatible flankers, target left"
        elif value == 221:
            return "Response - right, incompatible flankers, target left"

    def encoding(self, events_df):
        # Check the first two rows if both are 'Response'
        if (
            events_df.iloc[0]["trial_type"] == "response"
            and events_df.iloc[1]["trial_type"] == "response"
        ):
            events_df.drop(events_df.index[:2], inplace=True)
            events_df.reset_index(drop=True, inplace=True)

        # Check and drop the first row if it starts with 'Response'
        if events_df.iloc[0]["trial_type"] == "response":
            events_df.drop(events_df.index[0], inplace=True)
            events_df.reset_index(drop=True, inplace=True)

        # Check and drop the last row if the last two rows are 'Response'
        if (
            events_df.iloc[-1]["trial_type"] == "response"
            and events_df.iloc[-2]["trial_type"] == "response"
        ):
            events_df.drop(events_df.index[-1], inplace=True)
        # Keep rows corresponding to the responses
        events_df.drop(
            events_df[
                ~events_df["value"].isin([111, 112, 121, 122, 211, 212, 221, 222])
            ].index,
            inplace=True,
        )

        # Apply the encoding function to each row
        encoded_column = events_df.apply(self.encode_event, axis=1)

        # Create the mapping dictionary
        # Target: Correct response
        # NonTarget: Incorrect response,
        mapping = {
            "Response - left, compatible flankers, target left": "Target",
            "Response - left, incompatible flankers, target left": "Target",
            "Response - right, compatible flankers, target right": "Target",
            "Response - right, incompatible flankers, target right": "Target",
            "Response - left, compatible flankers, target right": "NonTarget",
            "Response - left, incompatible flankers, target right": "NonTarget",
            "Response - right, compatible flankers, target left": "NonTarget",
            "Response - right, incompatible flankers, target left": "NonTarget",
        }

        return encoded_column.values, mapping


class Erpcore2021_LRP(Erpcore2021):
    """
    ================= ======== ======= ================= =============== =============== ===========
    Name              #Subj    #Chan   #Trials / class   Trials length   Sampling rate   #Sessions
    ================= ======== ======= ================= =============== =============== ===========
    Erpcore2021_LRP   40       30      ~ 400 All         1s              1024Hz          1
    ================= ======== ======= ================= =============== =============== ===========

    Description of the task:

    A central arrowhead pointing to the left or right was flanked on both
    sides by arrowheads that pointed in the same direction (congruent trials) or the opposite
    direction (incongruent trials). Participants indicated the direction of the central
    arrowhead on each trial with a left- or right-hand buttonpress.
    """

    __init__ = partialmethod(Erpcore2021.__init__, "LRP")

    @staticmethod
    def encode_event(row):
        # We only kept the stimulus corresponding to the response
        value = row["value"]
        if value == 111:
            return "Response - left, compatible flankers, target left"
        elif value == 121:
            return "Response - left, incompatible flankers, target left"
        elif value == 212:
            return "Response - right, compatible flankers, target right"
        elif value == 222:
            return "Response - right, incompatible flankers, target right"
        elif value == 112:
            return "Response - left, compatible flankers, target right"
        elif value == 122:
            return "Response - left, incompatible flankers, target right"
        elif value == 211:
            return "Response - right, compatible flankers, target left"
        elif value == 221:
            return "Response - right, incompatible flankers, target left"

    def encoding(self, events_df):

        # Check the first two rows if both are 'Response'
        if (
            events_df.iloc[0]["trial_type"] == "response"
            and events_df.iloc[1]["trial_type"] == "response"
        ):
            events_df.drop(events_df.index[:2], inplace=True)
            events_df.reset_index(drop=True, inplace=True)

        # Check and drop the first row if it starts with 'Response'
        if events_df.iloc[0]["trial_type"] == "response":
            events_df.drop(events_df.index[0], inplace=True)
            events_df.reset_index(drop=True, inplace=True)

        # Check and drop the last row if the last two rows are 'Response'
        if (
            events_df.iloc[-1]["trial_type"] == "response"
            and events_df.iloc[-2]["trial_type"] == "response"
        ):
            events_df.drop(events_df.index[-1], inplace=True)
        # Keep rows corresponding to the responses
        events_df.drop(
            events_df[
                ~events_df["value"].isin([111, 112, 121, 122, 211, 212, 221, 222])
            ].index,
            inplace=True,
        )

        # Apply the encoding function to each row
        encoded_column = events_df.apply(self.encode_event, axis=1)

        # Create the mapping dictionary
        # Target: Response - left
        # NonTarget: Response - right
        mapping = {
            "Response - left, compatible flankers, target left": "Target",
            "Response - left, incompatible flankers, target left": "Target",
            "Response - left, compatible flankers, target right": "Target",
            "Response - left, incompatible flankers, target right": "Target",
            "Response - right, compatible flankers, target right": "NonTarget",
            "Response - right, incompatible flankers, target right": "NonTarget",
            "Response - right, compatible flankers, target left": "NonTarget",
            "Response - right, incompatible flankers, target left": "NonTarget",
        }

        return encoded_column.values, mapping