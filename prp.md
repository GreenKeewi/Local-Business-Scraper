Build a script that generates a CSV of Canadian local service businesses by looping through industries × cities.

Task

For every industry and every city, find local businesses and collect their website and basic info.

Industries (use exactly these)
Law Firm
Dental Clinic
Orthodontist
Physiotherapy Clinic
Chiropractor
Med Spa
Roofing Company
HVAC Company
Plumber
Electrician
Landscaping Company
Pest Control Service
Home Renovation Contractor
Accounting Firm
Real Estate Agency
Auto Repair Shop
Cleaning Service
IT Support Company

Cities (Canada)
Toronto, ON
Mississauga, ON
Brampton, ON
Markham, ON
Vaughan, ON
Hamilton, ON
London, ON
Kitchener, ON
Waterloo, ON
Guelph, ON
Oakville, ON
Burlington, ON
Milton, ON
Ottawa, ON
Montreal, QC
Quebec City, QC
Laval, QC
Vancouver, BC
Surrey, BC
Burnaby, BC
Richmond, BC
Victoria, BC
Kelowna, BC
Calgary, AB
Edmonton, AB
Red Deer, AB
Winnipeg, MB
Regina, SK
Saskatoon, SK
Halifax, NS
Moncton, NB
Fredericton, NB
Charlottetown, PE
St. John’s, NL

Data to Collect (CSV columns – exact order)
site_url
business_name
industry
company_name
city


company_name = same as business_name

site_url may be empty only if allowed by config

Config (.env)
SITE_INCLUSION=true   // true = include businesses without a site
SITE_INCLUSION=false  // false = skip businesses without a site
OUTPUT_FILE=local_businesses.csv
MAX_RESULTS_PER_SEARCH=200

Requirements

Loop through every city × every industry

Find multiple businesses per search

Deduplicate businesses

If SITE_INCLUSION=false, skip rows with no website

Output one CSV file when finished

Do not add extra fields

Do not add analysis or explanations

Logic Overview (strict)
for each city
  for each industry
    search for businesses
    for each business
      if no website and SITE_INCLUSION=false → skip
      else → add to CSV

Output

Generate one CSV file containing all results.
