import sys
import os
import argparse


class RequirementsHandler:
    """ Write requirements files w/ creds for use in pip installing github repo deps """
    def __init__(self):
        self.public_placeholder = "LEAF_SOURCE_CREDENTIALS"
        self.private_placeholder = "LEAF_PRIVATE_SOURCE_CREDENTIALS"

        self.items_to_process = [
            ["unit_tests", "requirements.txt",
                [self.public_placeholder]],
            ["integration_tests", "requirements.txt",
                [self.public_placeholder]],
        ]

    def _get_temp_and_codefresh_dirs(self):
        temp_dir_outside_container = os.environ.get("TEMP_DIR_OUTSIDE_CONTAINER")
        codefresh_volume = os.environ.get("CF_VOLUME_PATH")
        if not temp_dir_outside_container or not codefresh_volume:
            print("Environment variables not set.")
            sys.exit(1)
        return temp_dir_outside_container, codefresh_volume

    def _write_env_var_to_file(self, env_var_file_location, new_file_location, codefresh_volume):
        with open(f"{codefresh_volume}/env_vars_to_export", 'a', encoding="utf-8") as file:
            file.write(f'{env_var_file_location}={new_file_location}\n')

    def _replace_credentials(self, requirements, target_strings):
        for target_string in target_strings:
            replacement_string = os.environ.get(f"EPHEMERAL_{target_string}".upper())
            if replacement_string is not None:
                requirements = requirements.replace("${" + target_string + "}", replacement_string)
            else:
                print(f"Required env var EPHEMERAL_{target_string} is not defined.")
                sys.exit(1)
        return requirements

    def _write_credentialed_requirements(self, new_file_location, requirements):
        try:
            with open(new_file_location, 'w', encoding="utf-8") as credentialed_requirements_file:
                credentialed_requirements_file.write(requirements)
        except OSError as e:
            print(f"Unable to open {new_file_location}: {e}")
            sys.exit(1)

    def replace_to_new_file(self, item):
        """ Write the credential in a copy of requirements file """
        temp_dir, codefresh_volume = self._get_temp_and_codefresh_dirs()
        name, file_location, target_strings = item

        new_file_location = os.path.join(temp_dir, f"{name}_with_creds_requirements.txt")
        env_var_file_location = f"{name}_with_creds_requirements".upper()

        self._write_env_var_to_file(env_var_file_location, new_file_location, codefresh_volume)

        try:
            with open(file_location, 'r', encoding="utf-8") as requirements_file:
                requirements = requirements_file.read()

            requirements = self._replace_credentials(requirements, target_strings)
            self._write_credentialed_requirements(new_file_location, requirements)

        except OSError as e:
            print(f"Unable to open {file_location}: {e}")
            sys.exit(1)

    def process_items(self, item_name):
        """ Process the full list of items, or just one, depending on use case """
        for item_to_process in self.items_to_process:
            name, *_ = item_to_process
            if item_name in ('all', name):
                self.replace_to_new_file(item_to_process)

    def main(self):
        """ Create credentialed requirements file for all or one item in a list of items """
        parser = argparse.ArgumentParser(description='Process items')
        parser.add_argument('item', nargs='?', default='all', help='Specify item to process or "all" for all items')
        args = parser.parse_args()

        self.process_items(args.item)


if __name__ == "__main__":
    req_handler = RequirementsHandler()
    req_handler.main()
