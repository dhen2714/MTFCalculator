from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
import numpy as np
import pydicom
from pydicom.dataset import FileDataset
from .utils import read_json
from .constants import DEFAULT_TEMPLATE_PATH
from mtf import get_labelled_rois, calculate_mtf, preprocess_dcm


class MTFCalculator(ABC):
    @abstractmethod
    def calculate_mtf(self, dicom_path: str | Path) -> tuple[np.ndarray, dict]:
        ...


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

    def __init__(self, params_path=None) -> None:
        self.sample_number = 104
        if params_path:
            self.params_dict = read_json(params_path)
        else:
            self.params_dict = read_json(DEFAULT_TEMPLATE_PATH)

    def calculate_mtf(self, dicom_path) -> tuple[np.ndarray, dict]:
        """
        Return metadata dictionary with
        mode

        """
        dcm = pydicom.dcmread(dicom_path)
        image_array = preprocess_dcm(dcm)
        manufacturer_name = dcm[0x0008, 0x0070].value.lower()
        if "hologic" in manufacturer_name:
            mode = get_hologic_mode(dcm)
            sample_spacing = self.params_dict["hologic_spacing"][mode]
        elif "ge" in manufacturer_name:
            mode = "contact"
            sample_spacing = 0.1

        rois, rois_edge = get_labelled_rois(image_array)
        results_array = np.empty((self.sample_number, 5))
        results_array[:] = np.nan

        for edge_position in rois:
            edge_dir = EdgeDirection[edge_position].value
            edge_roi = rois[edge_position]
            edge_roi_canny = rois_edge[edge_position]
            f, mtf = calculate_mtf(
                edge_roi,
                sample_spacing,
                edge_roi_canny,
                edge_dir=edge_dir,
                sample_number=self.sample_number,
            )
            results_array[:, ColumnIndex[edge_position].value] = mtf
            results_array[:, 0] = f
        return results_array
