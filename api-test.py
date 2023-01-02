# Import the necessary libraries
import os
import requests

# Check if the file exists
if os.path.exists('localAndStateAgencies-NC.xlsx'):
  # Open the file in read mode
  with open('localAndStateAgencies-NC.xlsx', 'r') as f:
    # Read the contents of the file into a list of strings
    identifiers = f.readlines()
else:
  # If the file does not exist, print an error message
  print("Error: File not found")

# Set the base URL for the API endpoint
api_endpoint = "https://api.usa.gov/crime/fbi/sapi/api/data/nibrs/animal-cruelty/offender/agencies/{}/count?API_KEY=46pdC8k9DkXmNtyAMPHobBPCZ2cXHgs0grLnRc31"

# Initialize an empty string to hold the HTML for the table rows
rows = ''

# Iterate through the list of identifiers
for identifier in identifiers:
  # Construct the full API endpoint URL
  url = api_endpoint.format(identifier.strip())

  # Send a GET request to the API endpoint
  response = requests.get(url)

  # Check if the request was successful
  if response.status_code == 200:
    # Extract the data from the response object
    data = response.json()
    agency_name = data['agency_name']
    animal_cruelty_offenders = data['animal_cruelty_offenders']

    # Use the extracted data to build the HTML for a table row
    row = f"<tr><td>{agency_name}</td><td>{animal_cruelty_offenders}</td></tr>"

    # Append the row HTML to the rows string
    rows += row
  else:
    # If the request was not successful, print an error message
    print(f"Error: {response.status_code}")

# Use JavaScript or a library like jQuery to append the rows to the table on the web page
# Assume that the table body has an ID of "table-body"
document.getElementById("table-body").innerHTML = rows

