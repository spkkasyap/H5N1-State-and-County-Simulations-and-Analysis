import pandas as pd
import datetime

df = pd.read_csv("data/raw/tmrcas_state.txt", sep="\t")

# Function to convert decimal year to day-of-year integer (Jan 1 = 1)
def decimal_year_to_day(decimal_year):
    year = int(decimal_year)
    remainder = decimal_year - year
    
    # Check for leap year
    days_in_year = 366 if (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)) else 365
    
    # Compute exact date
    start_of_year = datetime.datetime(year, 1, 1)
    date = start_of_year + datetime.timedelta(days=remainder * days_in_year)
    
    # Convert to "day of year" (Jan 1 = 1)
    return date.timetuple().tm_yday

state_abbrev_to_name = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California",
    "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "FL": "Florida", "GA": "Georgia",
    "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa",
    "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire",
    "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York", "NC": "North Carolina",
    "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania",
    "RI": "Rhode Island", "SC": "South Carolina", "SD": "South Dakota", "TN": "Tennessee",
    "TX": "Texas", "UT": "Utah", "VT": "Vermont", "VA": "Virginia", "WA": "Washington",
    "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming"
}

# Apply to both date columns
df['dateOfEntry_day'] = df['dateOfEntry'].apply(decimal_year_to_day)
df['TMRCA_day'] = df['TMRCA'].apply(decimal_year_to_day)
df['State_full'] = df['State'].map(state_abbrev_to_name)

df['dateOfEntry_day'] = df['dateOfEntry_day'].astype(int)
df['TMRCA_day'] = df['TMRCA_day'].astype(int)

df.to_csv("data/processed/tmrcas_state_formatted.txt", sep="\t", index=False)

print(df)

