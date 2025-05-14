import argparse
import logging
import os
import sys
import json

class ModulesConfig:

    logfile_name = "modules_config.log"
    args = None
    modules_config_env_var = "MODULES_CONFIG"
    modules_config = []    # List to use to generate and store module configuration dictionaries or to hold a preopolated modules configuration
    tests_list = ["unit", "bdd"] # here for now. Can make it a dynamic module loader later


    def __init__(self, modules_config=[]):
        """
        Constructor for the ModulesConfig class
        If supplied with a prebuilt modules_config in json then convert it to a python object and use that
        """
        # Sets up normal file logging (DEBUG) and add additional logging formatting
        # TODO: Pass in log level required (currently hardcoded to DEBUG)
        logging.basicConfig(filename=self.logfile_name,level=logging.DEBUG, format='%(asctime)s %(name)s %(levelname)s: %(message)s')
        logging.info('ModulesConfig initialising...')

        if modules_config:
            logging.debug("ModulesConfig - modules_config supplied")
            self.modules_config = json.loads(modules_config)
        else:
            # First read the environment to see if we already have a modules_config set
            if self.modules_config_env_var in os.environ:
                logging.debug("ModulesConfig - modules_config found in environment")
                self.modules_config = json.loads(os.environ[self.modules_config_env_var])
            else:
                logging.debug("ModulesConfig - no modules_config found in environment. A new configuration will be built")


    def output_logging(self):
        """
        Add an additional (INFO) logger (to the file logger) to also output information to the screen. Intended for terminal, AWS Lambda functions or similar.
        :return:
        """
        root_logger = logging.getLogger()
        output_logger = logging.StreamHandler(sys.stdout)
        # TODO: Pass in log level required (currently hardcoded to DEBUG)
        output_logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        output_logger.setFormatter(formatter)
        root_logger.addHandler(output_logger)

    def build_modules_config(self, files_string, output_var):
        """
        Build the modules config based on the files_string provided.
        Detects the modules that have changed and creates a JSON object with the module name and any tests that are present in the module directory
        This is then stored as an environment variable and can be used to determine which tests to run in the CI/CD pipeline.
        TODO: Run a way to determine the next semver version number to use for each changed module
              Look at python pbased ones such as semantic_versioning_release or similar
              Could also git reference the last release tag and compare the changed files to that
        """
        # If we haven't been supplied with an existing modules_config (either passed on or in the environment) then we need to build one
        if not self.modules_config:
            # If we don't already have a modules_config set then build one
            logging.info('ModulesConfig - building new configuration...')
            
            logging.debug(os.getcwd())
            # TODO: hack for locally testing code for now - remove when happy
            if "GITHUB_OUTPUT" not in os.environ:
                # TEMP TODO: Remove as just for local testing
                os.chdir("..")
                logging.debug('ModulesConfig - running locally and not in Github so switching the directory to test things...')
                logging.debug(os.getcwd())


            files_list = files_string.split()
            logging.debug(f"ModulesConfig - files_list: {files_list}")
            # go through each filepath and get the module name
            modules_list = []
            #modules_tojson = []
            for file in files_list:
                path_parts = file.split(os.path.sep)
                if path_parts[0] == "modules" and path_parts[1] not in modules_list:
                    # keep a track of the modules we have already processed
                    modules_list.append(path_parts[1])
                    # add the module name to a dictionary object
                    module_info = {
                        "module": path_parts[1],
                    }
                    logging.debug(f"ModulesConfig - module_info: {module_info}")

                    # check for tests folders. If present add a 'tests' key to the dictionary with a list of tests to run
                    tests_path = os.path.join(os.getcwd(), path_parts[0], path_parts[1], "tests")
                    logging.debug(f"ModulesConfig - tests_path: {tests_path}")
                    if os.path.isdir(tests_path):
                        module_info['tests'] = self.get_tests_list(os.path.join(tests_path))
                        logging.debug(f"ModulesConfig - tests: {module_info['tests']}")

                    self.modules_config.append(module_info)

            #print(json.dumps(modules_tojson, indent=2))
            # If running in Github Actions then output the modules_config to GITHUB_OUTPUT
            # If not then just return the json data
            return self.output_json(self.modules_config, self.modules_config_env_var)

    def get_tests_list(self, module_tests_path):
        """
        Get the list of tests present in the specified module directory
        :param module_path:
        :return:
        """
        detected_tests = []
        # cycle through the known tests list and check if they exist in the module tests directory
        for test_name in self.tests_list:
            test_path = os.path.join(module_tests_path, test_name)
            if os.path.isdir(test_path):
                detected_tests.append(test_name)
        return detected_tests
    
    def build_tests_include_matrix_config(self):
        """
        Uses the existing config to build a matrix strategy json object to run changed module tests
        """
        strategy_config = []
        for module in self.modules_config:
            # Check if the module has tests
            if "tests" in module:
                # Generate the strategy_config for the tests
                strategy_config.extend(
                    self.generate_matrix_strategy_config(module["module"], module["tests"])
                )
        # Wrap the strategy_config in a dictionary
        if strategy_config:
            wrapped_matrix_strategy = self.wrap_matrix_strategy_type("include", strategy_config)
            return self.output_json(wrapped_matrix_strategy, "TESTS_MATRIX_OUTPUT")
            # The subsequent tests matrix job needs to detect if this variable has been set in GITHUB_OUTPUT.

    def generate_matrix_strategy_config(self, item, list, param1="module", param2="test"):
        """
        Generates a list of options based on the provided item and list.
        """
        options_list = []
        for list_item in list:
            options = {
                param1: item,
                param2: list_item,
            }
            options_list.append(options)
        return options_list
    
    def wrap_matrix_strategy_type(self, name, matrix_strategy_config):
        """
        Wraps the matrix configuration in a dictionary with a key. Could be "include" or "exclude" as required
        """
        return {
            name: matrix_strategy_config
        }
    
    def output_json(self, final_output, output_var="PYTHON_OUTPUT"):
        if "GITHUB_OUTPUT" in os.environ:
            # Write to GITHUB_OUTPUT as a variable named from the -o argument passed into this script
            with open(os.environ["GITHUB_OUTPUT"], "a") as fh:
                # example output: 'PYTHON_OUTPUT={"include":[{"module":"module1","test":"unit"},{"module":"module1","test":"bdd"},{"module":"module2","test":"unit"}]}'
                # note, if output_var is not supplied then the the default GITHUB_OUTPUT variable will be named PYTHON_OUTPUT
                #       if using multiple python scripts then this variable needs to change otherwise running this again will overwrite the GITHUB_OUTPUT variable!
                print(f"{output_var}={str(json.dumps(final_output))}", file=fh)
        else:
            # called by a python script/module so returning the dictionary object
            logging.info(json.dumps(final_output, indent=2))
            return json.dumps(final_output)
    
if __name__ == "__main__":
    # Create an instance of the ModulesConfig class
    app = ModulesConfig()
    
    # Configure logging to output to both file and console
    #app.output_logging()
    
    # Example usage: TODO: Do we want to make sure we only receive the module names rather than the full path
    files_string = "modules/module1/main.tf modules/module1/tests/unit/test.py modules/module2/main.tf"
    output_var = "MODULES_CONFIG"
    
    # Build the modules config
    app.build_modules_config(files_string, output_var)
    
    # Build the tests include matrix config
    matrix_strategy_json = app.build_tests_include_matrix_config()
    print(matrix_strategy_json)