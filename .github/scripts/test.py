"""
Todo...
    file.py -f "modules/module1/main.tf modules/module2/main.tf"
"""

import argparse
import logging
import os
import sys

class PackageModule:

    logfile_name = "mylogfile"
    args = None

    def __init__(self, options=None):
        # Sets up normal file logging (DEBUG) and add additional logging formatting
        logging.basicConfig(filename=self.logfile_name,level=logging.DEBUG, format='%(asctime)s %(name)s %(levelname)s: %(message)s')
        logging.info('PackageModule initialising...')

    def configure(self):
        """
        Retrieves any defined input arguments
        """
        logging.info('PackageModule configuring input...')
        parser = argparse.ArgumentParser()
        # required = parser.add_argument_group('required arguments')
        parser.add_argument("-f", "--files", help="string of space separated file paths that have been updated.")
        self.args = parser.parse_args()
        logging.info(f"Input args: {self.args}")

    def output_logging(self):
        """
        Add an additional (INFO) logger (to the file logger) to also output information to the screen. Intended for terminal, AWS Lambda functions or similar.
        :return:
        """
        root_logger = logging.getLogger()
        output_logger = logging.StreamHandler(sys.stdout)
        output_logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        output_logger.setFormatter(formatter)
        root_logger.addHandler(output_logger)

    def run(self):
        logging.info('PackageModule running...')
        self.configure()
        files_string = self.args.files
        files_list = files_string.split()
        # go through each filepath and get the module name
        modules_list = []
        for file in files_list:
            path_parts = file.split(os.path.sep)
            if path_parts[0] == "modules":
                if path_parts[1] not in modules_list:
                    modules_list.append(path_parts[1])
        print(modules_list)


if __name__ == "__main__":
    try:
        app = PackageModule()
        app.output_logging()
        app.run()
    except Exception as e:
        print("EXCEPTION ENCOUNTERED:")
        print(e)
        logging.exception(e, exc_info=True)
        sys.exit(1)

