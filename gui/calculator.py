from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
import numpy as np
import pydicom
from pydicom.dataset import FileDataset
from .utils import read_json
from mtf import get_labelled_rois, calculate_mtf, preprocess_dcm
from mtf.dcmutils import MammoMTFImage


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


def get_fuji_mode(dcm: FileDataset) -> str:
    pass


class MammoTemplateCalc(MTFCalculator):
    """Calculator compatible with the mammo template"""

    def __init__(self, params_path: Path) -> None:
        self.sample_number = 104
        self.params_dict = read_json(params_path)

    def _get_metadata_from_preprocessed(
        self, preprocessed_img: MammoMTFImage
    ) -> tuple[dict, float]:
        """
        Extract metadata and calculate sample spacing from a preprocessed image.
        Returns metadata dictionary and sample spacing.
        """
        metadata = {}
        manufacturer_name = preprocessed_img.manufacturer
        pixel_spacing = preprocessed_img.pixel_spacing
        orientation = preprocessed_img.orientation
        mode = preprocessed_img.acquisition

        if "hologic" in manufacturer_name:
            mag_factor = self.params_dict["hologic"]["magnification_factor"][mode]
            metadata["manufacturer"] = "hologic"
        elif "siemens" in manufacturer_name:
            mag_factor = self.params_dict["siemens"]["magnification_factor"][mode]
            metadata["manufacturer"] = "siemens"
        elif "ge" in manufacturer_name:
            mag_factor = self.params_dict["ge"]["magnification_factor"][mode]
            metadata["manufacturer"] = "ge"
        elif "fuji" in manufacturer_name:
            mag_factor = self.params_dict["fuji"]["magnification_factor"][mode]
            metadata["manufacturer"] = "fuji"
        else:
            raise ValueError(f"Unsupported manufacturer {manufacturer_name}")

        sample_spacing = pixel_spacing / mag_factor
        metadata["mode"] = mode
        metadata["sample_spacing"] = sample_spacing
        metadata["pixel_spacing"] = pixel_spacing
        metadata["magnification_factor"] = mag_factor
        metadata["orientation"] = orientation

        return metadata, sample_spacing

    def _calculate_mtf_for_edges(
        self, preprocessed_img: MammoMTFImage, sample_spacing: float
    ) -> tuple[np.ndarray, dict]:
        """
        Calculate MTF for all edges in a preprocessed image.
        Returns results array and metadata.
        """
        metadata, _ = self._get_metadata_from_preprocessed(preprocessed_img)
        rois, rois_edge = get_labelled_rois(preprocessed_img.array)
        results_array = np.empty((self.sample_number, 5))
        results_array[:] = np.nan

        for edge_position in rois:
            edge_dir = EdgeDirection[edge_position].value
            edge_roi = rois[edge_position]
            edge_roi_canny = rois_edge[edge_position]
            try:
                mtf_container = calculate_mtf(
                    edge_roi,
                    sample_spacing,
                    edge_roi_canny,
                    edge_dir=edge_dir,
                )
                f, mtf_vals = mtf_container.f, mtf_container.mtf
                results_array[:, ColumnIndex[edge_position].value] = mtf_vals[
                    : self.sample_number
                ]
                results_array[:, 0] = f[: self.sample_number]
            except Exception as e:
                print(f"Exception found when processing {edge_position} edge:\n{e}")
        return results_array, metadata

    def calculate_mtf(self, dicom_path) -> tuple[np.ndarray, dict]:
        """
        Calculate MTF from a DICOM file.
        """
        dcm = pydicom.dcmread(dicom_path)
        preprocessed_img = preprocess_dcm(dcm)
        return self._calculate_mtf_for_edges(
            preprocessed_img, preprocessed_img.pixel_spacing
        )

    def calculate_mtf_from_preprocessed(
        self, preprocessed_img: MammoMTFImage
    ) -> tuple[np.ndarray, dict]:
        """
        Calculate MTF using a preprocessed image.
        This avoids re-processing the DICOM file.
        """
        metadata, sample_spacing = self._get_metadata_from_preprocessed(
            preprocessed_img
        )
        return self._calculate_mtf_for_edges(preprocessed_img, sample_spacing)
