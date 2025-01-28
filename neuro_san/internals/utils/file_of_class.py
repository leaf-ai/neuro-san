
# Copyright (C) 2023-2025 Cognizant Digital Business, Evolutionary AI.
# All Rights Reserved.
# Issued under the Academic Public License.
#
# You can be released from the terms, and requirements of the Academic Public
# License by purchasing a commercial license.
# Purchase of a commercial license is mandatory for any use of the
# neuro-san SDK Software in commercial settings.
#
# END COPYRIGHT
from pathlib import Path
import os


class FileOfClass:
    """
    Class which assists in getting absolute paths from a starting source file.
    Clients are expected to invoke with something like:
            FileOfClass(__file__, path_to_basis="../reacharound").
    """

    def __init__(self, source_file: str, path_to_basis: str = "."):
        """
        Constructor

        :param source_file: The source file which will be the starting point for relative paths.
        :param path_to_basis: An optional path to a relative basis, so as to be
                        able to find other relevant files in an absolute manner.
                        This is expected to be a single string of multiple degrees of
                        ".." (or "../..", etc).
                        The default is the directory of the source_file.
        """

        self.source_file: str = source_file
        self.path_to_basis: str = path_to_basis

    def get_file_path(self) -> Path:
        """
        :return: A pathlib Path pointing to the file of the source_file
        """
        return Path(self.source_file)

    def get_file(self) -> str:
        """
        :return: A string pointing to the absolute file path of the source_file
        """
        return str(self.get_file_path().resolve())

    def get_dir_path(self) -> Path:
        """
        :return: A pathlib Path pointing to the directory of the source_file
        """
        return Path(self.source_file).parent

    def get_basis_path(self) -> Path:
        """
        :return: The pathlib Path of the provided basis.
        """
        return self.get_dir_path() / self.path_to_basis

    def get_basis(self) -> str:
        """
        :return: The absolute file path of the provided basis.
        """
        return str(self.get_basis_path().resolve())

    def get_file_in_basis(self, filename: str) -> str:
        """
        :return: An absolute path to a file that resides within the basis.
        """
        return str((self.get_basis_path() / filename).resolve())

    @staticmethod
    def check_file(filepath: str, basis: str = "/") -> str:
        """
        Used to quell Path Traversal vulnerabilities
        :param filepath: The filepath to verify
        :param basis: The directory under which the file must reside
        :return: A fully resolved path if successful.
                Otherwise a ValueError will be thrown.
        """
        if filepath is None:
            return filepath

        if basis is None:
            raise ValueError("basis for file checking is None")

        # Resolve full paths
        # Incorrectly flagged as destination of Path Traversal 1, 2
        #   Reason: This is the method in which we are actually trying to do
        #           the path traversal check itself. CheckMarx does not recognize
        #           pathlib as a valid library with which to resolve these kinds
        #           of issues.
        test_abs_path: str = str(Path(filepath).resolve())

        if basis == "~":
            # Special case if we are looking under user's home directory
            basis = os.path.expanduser("~")
        basis_abs_path: str = str(Path(basis).resolve())

        if not test_abs_path.startswith(basis_abs_path):
            raise ValueError(f"{test_abs_path} must be under {basis_abs_path}")

        return test_abs_path
