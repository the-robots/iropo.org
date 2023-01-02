# Import the necessary libraries
import pandas as pd
import requests

# Read the Excel file into a DataFrame
df = pd.read_excel('localAndStateAgencies-NC.xlsx')

# Extract the ORI column from the DataFrame as a list
identifiers = df['ORI'].tolist()

# Set the base URL for the API endpoint
api_endpoint = "https://api.usa.gov/crime/fbi/sapi/api/data/nibrs/animal-cruelty/offender/agencies/{}/count?API_KEY=46pdC8k9DkXmNtyAMPHobBPCZ2cXHgs0grLnRc31"

# Initialize an empty string to hold the HTML for the table rows# Import the necessary libraries
import pandas as pd
import requests

# Read the Excel file into a DataFrame
df = pd.read_excel('localAndStateAgencies-NC.xlsx')

# Extract the ORI column from the DataFrame as a list
identifiers = df['ORI'].tolist()

# Set the base URL for the API endpoint
api_endpoint = "https://api.usa.gov/crime/fbi/sapi/api/data/nibrs/animal-cruelty/offender/agencies/{}/count?API_KEY=46pdC8k9DkXmNtyAMPHobBPCZ2cXHgs0grLnRc31"

# Initialize an empty string to hold the HTML for the table rows
rows = ''

# Iterate through the list of identifiers
for identifier in identifiers:
  # Construct the full API endpoint URL
  url = api_endpoint.format(identifier)

  # Send a GET request to the API endpoint
  response = requests.get(url)

  # Check if the request was successful
  if response.status_code == 200:
    # Extract the data from the response object
    data = response.json()
    agency_name = data['agency_name']
    animal_cruelty_offenders = data['animal_cruelty_offenders']

    # Use the extracted data to build the HTML for a table row
rows = ''

# Iterate through the list of identifiers
for identifier in identifiers:
  # Construct the full API endpoint URL
  url = api_endpoint.format(identifier)

  # Send a GET request to the API endpoint
  response = requests.get(url)

  # Check if the request was successful
  if response.status_code == 200:
    # Extract the data from the response object
    data = response.json()
    agency_name = data['agency_name']
    animal_cruelty_offenders = data['animal_cruelty_offenders']

    # Use the extracted data to build the HTML for a table row
    row = f"<tr><td>{agency_name}</td

