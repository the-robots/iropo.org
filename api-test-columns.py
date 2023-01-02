# Import the necessary libraries
import pandas as pd
import requests

# Read the Excel file into a DataFrame
df = pd.read_excel('localAndStateAgencies-NC.xlsx')

# Get a list of all the column names in the DataFrame
column_names = df.columns.tolist()

# Extract the second column from the DataFrame as a list (assuming the ORI column is the second column)
identifiers = df[column_names[1]].tolist()

