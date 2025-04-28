
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

import argparse

from neuro_san.test.assessor.assessor_assert_forwarder import AssessorAssertForwarder
from neuro_san.test.driver.data_drvien_agent_test_driver import DataDrivenAgentTestDriver


class Assessor:
    """
    Command line tool for assessing an agent network's response
    to an input test case.
    """

    def __init__(self):
        """
        Constructor
        """
        self.args = None

    def main(self):
        """
        Main entry point for command line user interaction.
        """
        self.parse_args()
        asserts = AssessorAssertForwarder()
        driver = DataDrivenAgentTestDriver(asserts)
        driver.one_test(self.args.test_hocon)

    def parse_args(self):
        """
        Parse command line arguments into member variables
        """
        arg_parser = argparse.ArgumentParser()
        self.add_args(arg_parser)
        self.args = arg_parser.parse_args()

    def add_args(self, arg_parser: argparse.ArgumentParser):
        """
        Adds arguments.  Allows subclasses a chance to add their own.
        :param arg_parser: The argparse.ArgumentParser to add.
        """
        arg_parser.add_argument("--test_hocon", type=str,
                                help="The test case .hocon file to use as a basis for assessment")


if __name__ == '__main__':
    Assessor().main()
