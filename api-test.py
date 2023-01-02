# Import the necessary libraries
import pandas as pd
import requests

# Read the Excel file into a DataFrame and skip the first two rows
df = pd.read_excel('localAndStateAgencies-NC.xlsx')

# Get a list of all the column names in the DataFrame
column_names = df.columns.tolist()
print(column_names)

# Extract the second column from the DataFrame as a list (assuming the ORI column is the second column)
# identifiers = df[column_names[1]].tolist()

# Extract the fourth column from the DataFrame as a list
identifiers = df[column_names[3]].tolist()

# Set the base URL for the API endpoint
api_endpoint = "https://api.usa.gov/crime/fbi/sapi/api/data/nibrs/animal-cruelty/offender/agencies/{}/count?API_KEY=${{ secrets.fbiapi }}"

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
    pages = data['pages']
    agency = data['agency']


    # Use the extracted data to build the HTML for a table row
    row = f"<tr><td>{agency}</td><td>{pages}</td></tr>"

    # Append the row HTML to the rows string
    rows += row
  else:
    # If the request was not successful, print an error message
    print(f"Error: {response.status_code}")

# Use JavaScript or a library like jQuery to append the rows to the table on the web page
# Assume that the table body has an ID of "table-body"
document.getElementById("table-body").innerHTML = rows
