"""
Todo...
    python3 .github/scripts/module_helper.py
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

    def build_modules_config(self, files_string, output_var):
        logging.info('PackageModule running...')
        #print(os.getcwd())
        files_list = files_string.split()
        # go through each filepath and get the module name
        modules_list = []
        modules_tojson = []
        for file in files_list:
            path_parts = file.split(os.path.sep)
            if path_parts[0] == "modules" and path_parts[1] not in modules_list:
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
        return self.output_json(self, modules_tojson, output_var)

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
    
def get_config(self):
    """
    Outputs the full modules configuration
    Expected to be a json list of objects
    TODO: Thinking it should be in the format:
    [
        {
            "module": {
                "name": "module1",
                "version_next": "0.0.3"    # TODO: Consider passing in and bumping Major and Minor version from the PR commmit mesage
                "tests": [
                    "unit",
                    "compliance"
                ] 
            }
        }
    ]
    """
    pass

def set_modules_list(self, modules_list=[]):
    """
    Adds/updates one or many module skeletons to the dictionary. Expected to be initially used when detecting which modules have code updates applied
    For example ["module1","module2"]
    Only adds skeleton dictionary item(s) in the format {"module": { "name": "modulename"}}
    """
    return

def set_module_version_next(self, module, version_next):
    """
    Adds/updates the next calculated module version
    This could be from the GitVersion check or from a PR message bumping to a new Major/Minor version
    For example: "module1", "0.0.3" 
    """
    return

def set_module_tests_list(self, module, tests_list=[]):
    """
    Adds/updates a list of tests based on checking the module codebase for tests within a tests folder
    For example: ["unit, "compliance"]
    """
    return

def set_module(self, module_config):
    """
    Adds/Updates the specified module configuration
    For example: see the example structure of a module in the get_config() function
    """
    return

def get_modules(self, output="json"):
    """
    Gets a list of module names in the specified format. Expected to be used for Github matrix jobs
    For example: ["module1", "module2"]
    """
    return 

def get_module(self, module):
    """
    Gets the configuration for the specified module (if it exists)
    For example: see the example structure of a module in the get_config() function
    """
    return

def get_module_property(self, module, property_name):
    """
    Gets the specified modules property
    For example:
        module1, version_next returns: "0.0.3"
        module1, tests returns: ["unit", "compliance"]
    """
    return

def output_json(self, modules_config, output_var="PYTHON_OUTPUT"):
    if "GITHUB_OUTPUT" in os.environ:
        # Write to GITHUB_OUTPUT as a variable named from the -o argument passed into this script
        with open(os.environ["GITHUB_OUTPUT"], "a") as fh:
            # example output: 'MY_VAR=[{module_name: module1, tests: [unit, bdd]},{module_name: module2}]'
            # note, if -o or --output is not supplied to the script the the default GITHUB_OUTPUT variable will be named PYTHON_OUTPUT
            #       if using multiple python scripts then this needs to change otherwise the next script will overwrite the output of the one before!
            print(f"{output_var}={str(json.dumps(modules_config))}", file=fh)
    else:
        # called by a python script/module so returning the dictionary object
        return modules_config
    return

# def update_module_parameter(self, modules_config_json, module_name, module_param_name, module_param_value, output_var):
#     """
#     Update the json object with any detected next module versions
#     """
#     modules_config = json.loads(modules_config_json)
#     modules_config[module_name][module_param_name] = module_param_value
#     return self.output_json(modules_config, output_var)



# Not designed to be called directly, instead import and use as a script
# if __name__ == "__main__":
#     try:
#         #print(os.getcwd())
#         app = PackageModule()
#         # app.output_logging()
#         app.run()
#     except Exception as e:
#         print("EXCEPTION ENCOUNTERED:")
#         print(e)
#         logging.exception(e, exc_info=True)
#         sys.exit(1)

