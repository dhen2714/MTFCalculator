import sqlite3
from typing import Protocol
from dataclasses import dataclass, field
from pathlib import Path
import numpy as np
from PIL import Image
import pydicom
from mtf import preprocess_dcm
from .sql_queries import CREATE_TABLE, INSERT_ROWS, DELETE_ALL, UPDATE_MTF_VALUES
from .errors import ExcelWriteError


@dataclass
class MTFEdge:
    fpath: str
    _name: str = field(default=None, compare=False)
    manufacturer: str = None
    mode: str = None
    orientation: str = None
    frequency: str = None
    left: str = None
    right: str = None
    top: str = None
    bottom: str = None
    processed: int = 0

    @property
    def name(self) -> str:
        return Path(self.fpath).name

    def astuple(self) -> tuple[str, ...]:
        return (
            self.fpath,
            self.name,
            self.manufacturer,
            self.mode,
            self.orientation,
            self.frequency,
            self.left,
            self.right,
            self.top,
            self.bottom,
            self.processed,
        )


class MTFCalculator(Protocol):
    def calculate_mtf(self, dicom_path) -> tuple[np.ndarray, dict]: ...


class ExcelHandler(Protocol):
    selected_book: str

    @property
    def book_names(self) -> list[str]: ...

    def write_data(
        self,
        file_name: str,
        manufacturer: str,
        mode: str,
        orientation: str,
        mtf_data: np.ndarray,
    ) -> None: ...


def mtfcol2str(data_column: np.array) -> str:
    """Convert numpy array to comma separated string."""
    return ",".join(data_column.astype(str))


def str2mtfcol(data_str: str) -> np.array:
    return np.array(data_str.split(","), dtype=float)


class Model:
    def __init__(
        self, mtf_calculator: MTFCalculator = None, excel_handler: ExcelHandler = None
    ) -> None:
        self.connection = sqlite3.connect(":memory:")
        self.cursor = self.connection.cursor()
        self.cursor.execute(CREATE_TABLE)
        self.excel = excel_handler
        self.mtf_calc = mtf_calculator
        self.display_images = dict()
        self.display_image_details = dict()
        self.preprocessed_images = {}  # Cache for preprocessed images
        self.display_image_size = (512, 512)

    def add_edge_files(self, file_list: list[str]) -> None:
        new_data_rows = [MTFEdge(fpath=fpath).astuple() for fpath in file_list]
        self.cursor.executemany(INSERT_ROWS, new_data_rows)
        self.connection.commit()

    def get_edge_names(self) -> list[str]:
        edge_names: list[str] = []
        for data_row in self.cursor.execute("select fpath from edges"):
            file_name = Path(data_row[0]).name
            edge_names.append(file_name)
        return edge_names

    def delete_edge(self, dcm_name: str) -> None:
        """
        Delete a single edge from the database.
        """
        self.cursor.execute("delete from edges where name = ?", (dcm_name,))
        self.connection.commit()
        # Clear cached data for this image
        if dcm_name in self.display_images:
            del self.display_images[dcm_name]
        if dcm_name in self.display_image_details:
            del self.display_image_details[dcm_name]
        if dcm_name in self.preprocessed_images:
            del self.preprocessed_images[dcm_name]

    def delete_all(self) -> None:
        """
        Delete all edges from the database.
        """
        self.cursor.execute(DELETE_ALL)
        self.connection.commit()
        # Clear all cached data
        self.display_images.clear()
        self.display_image_details.clear()
        self.preprocessed_images.clear()

    def dicom_to_display_image(self, dcm_name: str) -> Image:
        if dcm_name == "":
            pixel_array = 256 * np.ones(self.display_image_size)
            im = Image.fromarray(pixel_array.astype(np.uint8))
        else:
            dcm_path = self.cursor.execute(
                "select fpath from edges where name = ?", (dcm_name,)
            ).fetchall()[0][0]
            dcm_name = Path(dcm_path).name
            if dcm_name in self.display_images.keys():
                im = self.display_images[dcm_name]
            else:
                dcm = pydicom.dcmread(dcm_path)
                mammo_image_preprocessed = preprocess_dcm(dcm)
                # Cache the preprocessed image
                self.preprocessed_images[dcm_name] = mammo_image_preprocessed
                pixel_array = mammo_image_preprocessed.array
                im = Image.fromarray(pixel_array.astype(np.uint8))
                im.thumbnail(self.display_image_size)
                self.display_images[dcm_name] = im
                self.display_image_details[dcm_name] = {
                    "acquisition": mammo_image_preprocessed.acquisition,
                    "manufacturer": mammo_image_preprocessed.manufacturer,
                    "pixel_spacing": mammo_image_preprocessed.pixel_spacing,
                    "focus_plane": mammo_image_preprocessed.focus_plane,
                }
        return im

    def calculate_mtf(self, dicom_path: str | Path) -> tuple[str, dict]:
        """
        Calculate MTF for a single image.
        Uses cached preprocessed image if available, otherwise processes the image.
        Returns results in form of strings
        """
        dcm_name = Path(dicom_path).name
        if dcm_name in self.preprocessed_images:
            # Use cached preprocessed image
            preprocessed_img = self.preprocessed_images[dcm_name]
            results_array, metadata = self.mtf_calc.calculate_mtf_from_preprocessed(
                preprocessed_img
            )
        else:
            # Process image if not in cache
            results_array, metadata = self.mtf_calc.calculate_mtf(dicom_path)
            # Cache the preprocessed image for future use
            dcm = pydicom.dcmread(dicom_path)
            self.preprocessed_images[dcm_name] = preprocess_dcm(dcm)

        frequency = mtfcol2str(results_array[:, 0])
        left = mtfcol2str(results_array[:, 1])
        right = mtfcol2str(results_array[:, 2])
        top = mtfcol2str(results_array[:, 3])
        bottom = mtfcol2str(results_array[:, 4])
        return frequency, left, right, top, bottom, metadata

    def update_mtf_values(
        self,
        fpath: str,
        manufacturer: str,
        mode: str,
        orientation: str,
        frequency: str,
        left: str,
        right: str,
        top: str,
        bottom: str,
    ) -> None:
        self.cursor.execute(
            UPDATE_MTF_VALUES,
            (
                manufacturer,
                mode,
                orientation,
                frequency,
                left,
                right,
                top,
                bottom,
                fpath,
            ),
        )
        self.connection.commit()

    def get_unprocessed_paths(self) -> list[str]:
        unprocessed_rows = self.cursor.execute(
            "select fpath from edges where processed = 0"
        )
        unprocessed_paths = []
        for row in unprocessed_rows:
            unprocessed_paths.append(row[0])
        return unprocessed_paths

    def calculate_all(self) -> None:
        """
        Calculate MTF for all unprocessed image files
        """
        unprocessed = self.get_unprocessed_paths()
        for dcm_path in unprocessed:
            frequency, left, right, top, bottom, metadata = self.calculate_mtf(dcm_path)
            mode = metadata["mode"]
            manufacturer = metadata["manufacturer"]
            orientation = metadata["orientation"]
            self.update_mtf_values(
                dcm_path,
                manufacturer,
                mode,
                orientation,
                frequency,
                left,
                right,
                top,
                bottom,
            )
        pass

    def get_all_processed(self) -> list[MTFEdge]:
        """
        Extract all processed entries from the database
        """
        processed_rows = self.cursor.execute(
            "select * from edges where processed = 1"
        ).fetchall()
        processed_rows = [MTFEdge(*values) for values in processed_rows]
        return processed_rows

    def write_all_processed(self) -> list[dict]:
        """
        Go through database, getting all processed edges and writing them all to
        excel.
        """
        processed_rows = self.get_all_processed()

        for row in processed_rows:
            row.frequency = str2mtfcol(row.frequency)
            row.left = str2mtfcol(row.left)
            row.right = str2mtfcol(row.right)
            row.top = str2mtfcol(row.top)
            row.bottom = str2mtfcol(row.bottom)
            mtf_data = np.array(
                [row.frequency, row.left, row.right, row.top, row.bottom]
            ).T
            try:
                self.excel.write_data(
                    row.name, row.manufacturer, row.mode, row.orientation, mtf_data
                )
            except ExcelWriteError as e:
                print(e)
