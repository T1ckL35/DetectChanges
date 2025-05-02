"""
Todo...
    python3 .github/scripts/test.py -f "modules/module1/main.tf modules/module2/main.tf"
"""

import argparse
import logging
import os
import sys
import json

class PackageModule:

    logfile_name = "mylogfile"
    tests_list = ["unit", "bdd"] # here for now. Can make it a dynamic module loader later
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
        # parser.add_argument("-f", "--files", help="string of space separated file paths that have been updated.")
        # optional to control the output type
        parser.add_argument("-o", "--output", nargs='?', default="PYTHON_OUTPUT", help="output type. If used then pushes the output from this script into the environment variable GITHUB_OUTPUT. Intended to be used in a Github Actions workflow.")
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
        #print(os.getcwd())
        self.configure()
        files_string = self.args.files
        files_list = files_string.split()
        # go through each filepath and get the module name
        modules_list = []
        modules_tojson = []
        for file in files_list:
            path_parts = file.split(os.path.sep)
            if path_parts[0] == "modules":
                if path_parts[1] not in modules_list:
                    # add the module name to a dictionary object
                    module_info = {
                        "module_name": path_parts[1],
                    }
                    # check for tests folders. If present add a 'tests' key to the dictionary with a list of tests to run
                    tests_path = os.path.join(path_parts[0], path_parts[1], "tests")
                    if os.path.isdir(tests_path):
                        module_info['tests'] = self.get_tests_list(os.path.join(tests_path))

                    modules_tojson.append(module_info)

        #print(json.dumps(modules_tojson, indent=2))

        # Catch so this only runs in GitHub Actions
        if "GITHUB_OUTPUT" in os.environ:
            # Write to GITHUB_OUTPUT as a variable named from the -o argument passed into this script
            with open(os.environ["GITHUB_OUTPUT"], "a") as fh:
                # example output: 'MY_VAR=[{module_name: module1, tests: [unit, bdd]},{module_name: module2}]'
                # note, if -o or --output is not supplied to the script the the default GITHUB_OUTPUT variable will be named PYTHON_OUTPUT
                #       if using multiple python scripts then this needs to change otherwise the next script will overwrite the output of the one before!
                print(f"{self.args.output}={str(json.dumps(modules_tojson))}", file=fh)
        else:
            # called by a python script/module so returning the dictionary object
            return modules_tojson


    def get_tests_list(self, module_tests_path):
        """
        Get the list of tests in the specified module directory
        :param module_path:
        :return:
        """
        detected_tests = []
        for test_name in self.tests_list:
            test_path = os.path.join(module_tests_path, test_name)
            if os.path.isdir(test_path):
                detected_tests.append(test_name)
        return detected_tests


    def check_for_matching_folders(self, module_path, matches=[]):
        """
        Check if the folder name exists in the modules directory
        :param folder_name:
        :return:
        """
        for match_check in matches:
            folder_check = os.path.join(module_path, match_check)
            if os.path.isdir(folder_check):
                return True
        return False


if __name__ == "__main__":
    try:
        #print(os.getcwd())
        app = PackageModule()
        # app.output_logging()
        app.run()
    except Exception as e:
        print("EXCEPTION ENCOUNTERED:")
        print(e)
        logging.exception(e, exc_info=True)
        sys.exit(1)

