"""
Name/Description etc.. goes here
"""

#import argparse
import logging
import os
import sys
import json

class MatrixHelper:

    logfile_name = "gha_matrix_logs"
    args = None

    def __init__(self, options=None):
        # Sets up normal file logging (DEBUG) and add additional logging formatting
        logging.basicConfig(filename=self.logfile_name,level=logging.DEBUG, format='%(asctime)s %(name)s %(levelname)s: %(message)s')
        logging.info('GHA Matrix initialising...')

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

    def generate_includes_from_list(self, item, list, param1="module", param2="test"):
        """
        Generates a list of includes based on the provided item and list.
        """
        includes = []
        for list_item in list:
            include = {
                param1: item,
                param2: list_item,
            }
            includes.append(include)
        return includes
    
    def wrap_includes(self, includes):
        """
        Wraps the includes in a dictionary with the key "include".
        """
        return {
            "include": includes
        }
    
    ##### HERE introduce outputting the json to GITHUB_OUTPUT asbed on the variable name specified!
    def output_json(self, final_includes, output_var="PYTHON_OUTPUT"):
        if "GITHUB_OUTPUT" in os.environ:
            # Write to GITHUB_OUTPUT as a variable named from the -o argument passed into this script
            with open(os.environ["GITHUB_OUTPUT"], "a") as fh:
                # example output: 'PYTHON_OUTPUT={"include":[{"module":"module1","test":"unit"},{"module":"module1","test":"bdd"},{"module":"module2","test":"unit"}]}'
                # note, if output_var is not supplied then the the default GITHUB_OUTPUT variable will be named PYTHON_OUTPUT
                #       if using multiple python scripts then this variable needs to change otherwise running this again will overwrite the GITHUB_OUTPUT variable!
                print(f"{output_var}={str(json.dumps(final_includes))}", file=fh)
        else:
            # called by a python script/module so returning the dictionary object
            return final_includes
    
if __name__ == "__main__":

    print("Running the MatrixHelper script directly...")

    # Create an instance of the MatrixHelper class
    app = MatrixHelper()
    
    # Configure logging to output to both file and console
    app.output_logging()
    
    # Generate a list of includes for module1
    item = "module1"
    list = ["unit", "bdd"]
    # Generate includes using the helper method. Note, using the extra parameter defaults of "module" and "test"
    includes = app.generate_includes_from_list(item, list)
    #print(includes)

    # Generate a list of includes for module2
    item = "module2"
    list = ["unit"]
    # Merge all the includes into a single list
    includes.extend(
        app.generate_includes_from_list(item, list)
    )
    final_includes = app.wrap_includes(includes)
    app.output_json(final_includes)
