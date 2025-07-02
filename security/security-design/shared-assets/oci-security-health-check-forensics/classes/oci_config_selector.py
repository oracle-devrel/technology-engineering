"""
Copyright (c) 2025, Oracle and/or its affiliates.  All rights reserved.
This software is dual-licensed to you under the Universal Permissive License (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl or Apache License 2.0 as shown at http://www.apache.org/licenses/LICENSE-2.0. You may choose either license.

oci_config_selector.py
@author base: Jacco Steur
Supports Python 3 and above

coding: utf-8
"""
import configparser
import os
import questionary
import tempfile

class OCIConfigSelector:
    def __init__(self, oci_config_file, tqt_config_file, csv_dir):
        """
        Initializes the OCIConfigSelector with paths to both config files.
        The paths support '~' to denote the user's home directory.
        :param oci_config_file: Path to the main OCI config file (DEFAULT domain).
        :param tqt_config_file: Path to the TQT config file (additional tenancies).
        :param csv_dir: Base directory for CSV files.
        """
        # Expand the user home directory (e.g., '~/.oci/config')
        self.oci_config_file = os.path.expanduser(oci_config_file)
        self.tqt_config_file = os.path.expanduser(tqt_config_file)
        self.csv_dir = csv_dir
        self.config = configparser.ConfigParser()
        self.combined_config_content = None
        self.read_and_combine_configs()

    def read_and_combine_configs(self):
        """
        Reads both config files, concatenates their content, and loads the combined config.
        """
        combined_content = []
        
        # Read the main OCI config file (DEFAULT domain)
        if os.path.exists(self.oci_config_file):
            try:
                with open(self.oci_config_file, 'r') as f:
                    oci_content = f.read().strip()
                    if oci_content:
                        combined_content.append(oci_content)
                        print(f"Loaded DEFAULT domain from: {self.oci_config_file}")
            except Exception as e:
                print(f"Warning: Could not read OCI config file {self.oci_config_file}: {e}")
        else:
            print(f"Warning: OCI config file not found: {self.oci_config_file}")
        
        # Read the TQT config file (additional tenancies)
        if os.path.exists(self.tqt_config_file):
            try:
                with open(self.tqt_config_file, 'r') as f:
                    tqt_content = f.read().strip()
                    if tqt_content:
                        combined_content.append(tqt_content)
                        print(f"Loaded additional tenancies from: {self.tqt_config_file}")
            except Exception as e:
                print(f"Warning: Could not read TQT config file {self.tqt_config_file}: {e}")
        else:
            print(f"Warning: TQT config file not found: {self.tqt_config_file}")
        
        # Combine the content
        if combined_content:
            self.combined_config_content = '\n\n'.join(combined_content)
            
            # Create a temporary file to load the combined configuration
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.config') as temp_file:
                temp_file.write(self.combined_config_content)
                temp_config_path = temp_file.name
            
            try:
                # Read the combined configuration
                read_files = self.config.read(temp_config_path)
                if not read_files:
                    raise FileNotFoundError(f"Unable to read combined config from temporary file")
                print(f"Successfully combined and loaded configuration from both files")
            finally:
                # Clean up the temporary file
                try:
                    os.unlink(temp_config_path)
                except:
                    pass
        else:
            raise FileNotFoundError("No valid configuration content found in either config file")

    def get_combined_config_content(self):
        """
        Returns the combined configuration content as a string.
        Useful for debugging or logging purposes.
        """
        if self.combined_config_content is None:
            raise ValueError("No combined configuration content available. Check if config files were read successfully.")
        return self.combined_config_content

    def list_sections(self):
        """
        Returns a list of sections available in the combined config.
        Note: The DEFAULT section is not included in this list because configparser
        treats it as a special section containing default values.
        """
        return self.config.sections()

    def select_section(self):
        """
        Uses questionary to prompt the user to select one of the available sections,
        select the DEFAULT section, or create a new section.
        Returns a tuple: (section_name, prefix) where prefix is the value of the
        prefix attribute under the section if it exists, otherwise None.
        """
        sections = self.list_sections()
        # Add "Create New Section" as an option
        choices = ["DEFAULT"] + sections + ["Create New Section"]

        answer = questionary.select(
            "Select a section (use arrow keys and press ENTER):",
            choices=choices,
            default="DEFAULT"
        ).ask()

        if answer == "Create New Section":
            answer = self.create_new_section()
        else:
            print(f"You selected: {answer}")

        # Check for the 'prefix' attribute in the selected section.
        if answer == "DEFAULT":
            # For DEFAULT, check the defaults() dictionary.
            prefix = self.config.defaults().get("prefix", None)
        else:
            prefix = self.config.get(answer, "prefix") if self.config.has_option(answer, "prefix") else None

        return answer, prefix

    def create_new_section(self):
        """
        Creates a new section in the TQT config file.
        Asks the user whether they have CSV files or connection details.
        For CSV files: asks for the prefix and shows the path where files must be pasted.
        For connection details: prompts for necessary details and adds them to the new section.
        """
        section_name = questionary.text("Enter the name for the new section:").ask()
        # Check if the section already exists
        if section_name in self.config.sections():
            print(f"Section '{section_name}' already exists. Please choose a different name.")
            return self.select_section()[0]  # Re-prompt for selection and return the section name

        option = questionary.select(
            "Do you have CSV files or connection details?",
            choices=["CSV files", "Connection Details"]
        ).ask()

        if option == "CSV files":
            prefix = questionary.text("Provide the prefix for the CSV files:").ask()
            # Determine the path where the CSV files should be pasted.
            csv_path = os.path.join(self.csv_dir, section_name, section_name + '_<YYYYMMDD>_<HHMMSS>')
            print(f"Please paste your CSV files with prefix '{prefix}' into the following directory:\n{csv_path}")
            # Optionally, create the directory if it does not exist.
            if not os.path.exists(csv_path):
                os.makedirs(csv_path)
                print(f"Created directory: {csv_path}")
            
            # Save the CSV prefix in the TQT config file for future reference.
            self._add_section_to_tqt_config(section_name, {"prefix": prefix})
            
            # Return the new section name.
            print(f"New section '{section_name}' added to TQT config file. Restart to select and load your data.")
            exit()

        elif option == "Connection Details":
            oci_user = questionary.text("Enter OCI user:").ask()
            fingerprint = questionary.text("Enter fingerprint:").ask()
            tenancy = questionary.text("Enter tenancy:").ask()
            region = questionary.text("Enter region:").ask()
            key_file = questionary.text("Enter key file path:").ask()

            # Create new section with connection details in TQT config.
            config_data = {
                "user": oci_user,
                "fingerprint": fingerprint,
                "tenancy": tenancy,
                "region": region,
                "key_file": key_file
            }
            self._add_section_to_tqt_config(section_name, config_data)
            print(f"New section '{section_name}' added to TQT config file.")
            return section_name

        else:
            print("Invalid option selected.")
            return self.create_new_section()  # Recurse until a valid option is provided.

    def _add_section_to_tqt_config(self, section_name, config_data):
        """
        Adds a new section to the TQT config file.
        :param section_name: Name of the section to add
        :param config_data: Dictionary of key-value pairs for the section
        """
        # Create the TQT config file if it doesn't exist
        os.makedirs(os.path.dirname(self.tqt_config_file), exist_ok=True)
        
        # Read existing TQT config if it exists
        tqt_config = configparser.ConfigParser()
        if os.path.exists(self.tqt_config_file):
            tqt_config.read(self.tqt_config_file)
        
        # Add the new section
        tqt_config.add_section(section_name)
        for key, value in config_data.items():
            tqt_config.set(section_name, key, value)
        
        # Write back to the TQT config file
        with open(self.tqt_config_file, "w") as configfile:
            tqt_config.write(configfile)
        
        # Refresh the combined configuration
        self.read_and_combine_configs()