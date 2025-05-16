
import logging
import os
import sys
import json
# Make sure requirements.txt has entries for the PyGitHub and semver modules
from github import Github, GithubException, Auth
import semver

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

        # If we have passed in a modules_config then use that. Mainly intended for overriding the default/calculated modules_config for testing purposes.
        if modules_config:
            logging.debug("ModulesConfig - modules_config supplied")
            self.modules_config = json.loads(modules_config)
        else:
            # Check to see if we have a modules_config already set in the environment. If so use that, otherwise build a new one
            if self.modules_config_env_var in os.environ and os.environ[self.modules_config_env_var] != "":
                # First read the environment to see if we already have a modules_config set
                logging.debug("ModulesConfig - populated modules_config found in environment")
                self.modules_config = json.loads(os.environ[self.modules_config_env_var])
            else:
                # Nothing found so genreate a new modules_config by parsing the changed files
                logging.debug("ModulesConfig - no populated modules_config found in environment. A new configuration will be built")


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

                    # check for tags and work out the next version number
                    next_versions = self.get_modules_tag(path_parts[1])
                    logging.debug(f"ModulesConfig - next versions: {next_versions}")
                    # TODO: Need to parse the PR message to determine which next version to use (major, minor or patch)
                    module_info['versions'] = next_versions

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
    

    def get_modules_tag(self, reference):
        """
        Get the latest module tag
        :param reference: The module name to check for tags
        :return: A dictionary object either empty or with the current version and the next major, minor and patch versions
        """
        # Public Web Github
        #g = Github(auth=auth)
        # Set in the GHA Workflow
        auth = Auth.Token(os.environ['GH_TOKEN'])
        g = Github(auth=auth)
        # g = Github(os.environ['GH_TOKEN'])
        repo = g.get_repo("T1ckL35/DetectChanges")

        # Github Enterprise with custom hostname
        # g = Github(base_url="https://{hostname}/api/v3", auth=auth)

        # Object to store current and future versions in
        version_object = {}

        try:
            logging.debug(f"Checking GitHub Tag with reference tags/{reference}*...")
            tag = repo.get_git_ref(f"tags/{reference}")
            if tag._rawData:
                logging.debug(f"GitHub Tag with reference tags/{reference}* exists...")

                # grabs all found prefix named tags, gets the semver tag from the ref name and sorts them
                current_semver_tag = sorted(list((object['ref'].removeprefix(f"refs/tags/{reference}-") for object in tag._rawData)))[-1]
                logging.debug(f"Current found semver tag is: {current_semver_tag}")

            # PyGitHub returns GitRef(ref=None) if for example searching for tag v13 and v13 does not exist, but v13.0.0 exists
            # It returns a 404 if for example searching for tag v13.0.0 and v13.0.0 does not exist

        except GithubException as e:
            if e.status == 404:
                # PyGitHub returns a 404 if for example searching for tag v13.0.0 and v13.0.0 does not exist
                # If the tag does not exist then set the current version to 0.0.1
                logging.debug(f"Unable to find GitHub Tag with reference tags/{reference}* - 404 error. Creating a first tag...")
                current_version_tag = "0.0.1"
            else:
                logging.debug(f"Retrieving GitHub Tag has failed with the following status code: {e.status}")
                raise Exception(
                    f"Retrieving GitHub Tag has failed with the following status code: {e.status}"
                )
        return self.build_versions(version_object)
    
    def build_versions(self, current_version="0.0.1"):
        """
        Build the versions object based on the current version supplied
        :param current_version: The current version to use as a base. Defaults to 0.0.1 if no tag has been supplied.
        :return: A dictionary object with the current, major, minor and patch versions
        """
        return {
            "current": current_version,
            "major": semver.bump_major(current_version),
            "minor": semver.bump_minor(current_version),
            "patch": semver.bump_patch(current_version)
        }

    
    def build_tests_matrix_config(self):
        """
        Uses the existing config to build a matrix strategy json object to run changed module tests
        By default pushes to GITHUB_OUTPUT > TESTS_MATRIX_OUTPUT as a variable to use
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
            # Push the output to the default GITHUB_OUTPUT variable.
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
        """
        Detects whether we are running in a Github Actions environment or not. If yes then it sets the relevant github variable. If not then it outputs the values - useful if calling this code as a python module.
        Note, setting GITHUB_OUTPUT will not reflect the value in the currently running step but will be available in all subsequent jobs/steps as required
        """
        if "GITHUB_OUTPUT" in os.environ:
            # Write to GITHUB_OUTPUT as a variable named from the output_var variable value passed into this function
            with open(os.getenv("GITHUB_OUTPUT"), "a") as fh:
                # example: matrix strategy config output: 'PYTHON_OUTPUT={"include":[{"module":"module1","test":"unit"},{"module":"module1","test":"bdd"},{"module":"module2","test":"unit"}]}'
                # note, if output_var is not supplied then the the default GITHUB_OUTPUT variable will be named PYTHON_OUTPUT
                #       if using multiple python scripts then this variable needs to change otherwise running this again will overwrite the GITHUB_OUTPUT variable!
                print(f"{output_var}={str(json.dumps(final_output))}", file=fh)
        else:
            # called by a python script/module so returning the dictionary object
            logging.info(json.dumps(final_output, indent=2))
            return json.dumps(final_output)
    

if __name__ == "__main__":
    """
    Only runs the code below if the script is called directly. Usually it is called from a Github Actions workflow with inline python code.
    """
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
    matrix_strategy_json = app.build_tests_matrix_config()
    print(matrix_strategy_json)