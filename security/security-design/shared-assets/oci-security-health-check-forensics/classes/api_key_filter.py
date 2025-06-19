"""
Copyright (c) 2025, Oracle and/or its affiliates.  All rights reserved.
This software is dual-licensed to you under the Universal Permissive License (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl or Apache License 2.0 as shown at http://www.apache.org/licenses/LICENSE-2.0. You may choose either license.

api_key_filter.py
@author base: Jacco Steur
Supports Python 3 and above

coding: utf-8
"""
import pandas as pd
from datetime import datetime, timedelta
import re

class ApiKeyFilter:
    def __init__(self, column_name='api_keys', age_days=90, mode='older'):
        """
        Initialize the ApiKeyFilter.

        Parameters:
        - column_name (str): The name of the column containing API keys.
        - age_days (int): The age threshold in days.
        - mode (str): Either 'older' or 'younger' to filter dates accordingly.
                     'older' shows dates older than age_days
                     'younger' shows dates younger than or equal to age_days
        """
        self.column_name = column_name
        self.age_days = age_days
        self.mode = mode.lower()
        self.age_months = self.calculate_months(age_days)

    @staticmethod
    def calculate_months(age_days):
        """
        Calculate the number of months from the given days.

        Parameters:
        - age_days (int): The number of days.

        Returns:
        - int: The equivalent number of months.
        """
        return (age_days + 29) // 30  # Round up to the nearest month

    def filter(self, df):
        """
        Filter the DataFrame based on the age of API keys.

        Parameters:
        - df (pd.DataFrame): The DataFrame to filter.

        Returns:
        - pd.DataFrame: The filtered DataFrame.
        """
        # Define the date threshold
        today = datetime.now()
        threshold_date = today - timedelta(days=self.age_days)

        # Check if the specified column exists in the DataFrame
        if self.column_name not in df.columns:
            print(f"Error: Column '{self.column_name}' does not exist in the DataFrame.")
            return df

        # Extract the dates from the specified column
        def extract_dates(key_str):
            dates = []
            if pd.isnull(key_str):
                return dates
                
            # Handle different formats by splitting entries by comma
            entries = [entry.strip() for entry in key_str.split(',') if entry.strip()]
            
            date_formats = ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M']
            date_pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}(?::\d{2})?)'
            
            for entry in entries:
                try:
                    # Case 1: Just a date string
                    if re.match(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}(:\d{2})?$', entry.strip()):
                        for fmt in date_formats:
                            try:
                                date = datetime.strptime(entry.strip(), fmt)
                                dates.append(date)
                                break
                            except ValueError:
                                continue
                    
                    # Case 2: OCID with date (separated by spaces)
                    else:
                        # Look for date pattern in the entry
                        date_matches = re.findall(date_pattern, entry)
                        if date_matches:
                            for date_str in date_matches:
                                for fmt in date_formats:
                                    try:
                                        date = datetime.strptime(date_str, fmt)
                                        dates.append(date)
                                        break
                                    except ValueError:
                                        continue
                        # Fall back to original colon-based parsing if no date pattern found
                        elif ':' in entry:
                            # Split on the first occurrence of ':'
                            parts = entry.split(':', 1)
                            if len(parts) > 1:
                                date_part = parts[1].strip()
                                for fmt in date_formats:
                                    try:
                                        date = datetime.strptime(date_part, fmt)
                                        dates.append(date)
                                        break
                                    except ValueError:
                                        continue
                        else:
                            print(f"Warning: No valid date format found in entry: '{entry}'")
                except Exception as e:
                    print(f"Error parsing date in entry: '{entry}', error: {e}")
            
            return dates

        # Apply the date extraction to the specified column
        df['key_dates'] = df[self.column_name].apply(extract_dates)

        # Determine if any keys match the age criteria based on mode
        def check_dates(dates_list):
            if not dates_list:
                return False
            for date in dates_list:
                if self.mode == 'older' and date <= threshold_date:
                    return True
                elif self.mode == 'younger' and date >= threshold_date:  # Changed from > to >= for inclusive younger
                    return True
            return False

        # Apply the filter to the DataFrame
        mask = df['key_dates'].apply(check_dates)

        # Keep rows where the condition is met
        filtered_df = df[mask].copy()

        # Drop the temporary 'key_dates' column
        filtered_df.drop(columns=['key_dates'], inplace=True)

        return filtered_df