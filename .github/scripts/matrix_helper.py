"""
Name/Description etc.. goes here
"""

#import argparse
import logging
#import os
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
    
    def convert_to_json(self, data):
        """
        Outputs the given data as JSON.
        """
        json_output = json.dumps(data)
        logging.info(f"JSON Output: {json_output}")
        #print(json_output)

    def wrap_includes_in_json(self, includes):
        """
        Wraps the includes in a JSON object ready for use in a Github Actions Matrix
        """
        json_output = {
            "include": includes
        }
        return json.dumps(json_output)
    
if __name__ == "__main__":

    print("Running the MatrixHelper script directly...")

    # Create an instance of the MatrixHelper class
    matrix_helper = MatrixHelper()
    
    # Configure logging to output to both file and console
    matrix_helper.output_logging()
    
    # Generate a list of includes for module1
    item = "module1"
    list = ["unit", "bdd"]
    # Generate includes using the helper method. Note, using the extra parameter defaults of "module" and "test"
    includes = matrix_helper.generate_includes_from_list(item, list)
    #print(includes)

    # Generate a list of includes for module2
    item = "module2"
    list = ["unit"]
    # Merge all the includes into a single list
    includes.extend(
        matrix_helper.generate_includes_from_list(item, list)
    )
    # Wrap the includes in a JSON object for Github Actions
    json_output = matrix_helper.wrap_includes_in_json(includes)
    # Print the generated includes for demonstration purposes
    print(json_output)
