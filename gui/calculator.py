from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
import numpy as np
import pydicom
from pydicom.dataset import FileDataset
from .utils import read_json
from mtf import get_labelled_rois, calculate_mtf, preprocess_dcm


class MTFCalculator(ABC):
    @abstractmethod
    def calculate_mtf(self, dicom_path: str | Path) -> tuple[np.ndarray, dict]: ...


class EdgeDirection(Enum):
    left = "vertical"
    right = "vertical"
    top = "horizontal"
    bottom = "horizontal"


class ColumnIndex(Enum):
    left = 1
    right = 2
    top = 3
    bottom = 4


def get_hologic_mode(dcm: FileDataset) -> str:
    img_type_header = dcm[0x0008, 0x0008].value
    if "TOMOSYNTHESIS" in img_type_header or "VOLUME" in img_type_header:
        mode = "tomo_recon_top"
    else:
        paddleval = dcm[0x0018, 0x11A4].value
        if paddleval == "10CM MAG":
            mode = "mag"
        else:
            mode = "contact"
    return mode


class MammoTemplateCalc(MTFCalculator):
    """Calculator compatible with the mammo template"""

    def __init__(self, params_path: Path) -> None:
        self.sample_number = 104
        self.params_dict = read_json(params_path)

    def calculate_mtf(self, dicom_path) -> tuple[np.ndarray, dict]:
        """
        Return metadata dictionary with
        mode

        """
        metadata = {}
        dcm = pydicom.dcmread(dicom_path)
        image_array = preprocess_dcm(dcm)
        manufacturer_name = dcm[0x0008, 0x0070].value.lower()
        if "hologic" in manufacturer_name:
            mode = get_hologic_mode(dcm)
            sample_spacing = self.params_dict["hologic"]["spacing"][mode]
            metadata["manufacturer"] = "hologic"
        elif "ge" in manufacturer_name:
            mode = "contact"
            sample_spacing = self.params_dict["ge"]["spacing"][mode]
            metadata["manufacturer"] = "ge"
        metadata["mode"] = mode
        rois, rois_edge = get_labelled_rois(image_array)
        results_array = np.empty((self.sample_number, 5))
        results_array[:] = np.nan

        for edge_position in rois:
            edge_dir = EdgeDirection[edge_position].value
            edge_roi = rois[edge_position]
            edge_roi_canny = rois_edge[edge_position]
            mtf_container = calculate_mtf(
                edge_roi,
                sample_spacing,
                edge_roi_canny,
                edge_dir=edge_dir,
            )
            f, mtf = mtf_container.f, mtf_container.mtf
            results_array[:, ColumnIndex[edge_position].value] = mtf[
                : self.sample_number
            ]
            results_array[:, 0] = f[: self.sample_number]
        return results_array, metadata
