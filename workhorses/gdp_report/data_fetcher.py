import pandas as pd
import requests
import time
import beaapi
import os

BEA_API_KEY = os.environ.get('BEA_API_KEY')

## Data Helper Functions
def get_data_with_retry(api_key, datasetname, TableName, Frequency, Year, retries=3, delay=5):
    for attempt in range(retries):
        try:
            return beaapi.get_data(api_key, datasetname=datasetname, TableName=TableName, Frequency=Frequency, Year=Year)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 503:
                print(f"Service unavailable. Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                raise
    raise Exception("Failed to retrieve data after multiple attempts")

def debt_to_penny_fetcher(week_ago_debttopenny):
    treasury_link = f"https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_to_penny?fields=record_date,tot_pub_debt_out_amt&filter=record_date:gte:{week_ago_debttopenny}"
    p = requests.get(treasury_link)
    data = p.json()
    debt_df = (
        pd.DataFrame(data['data'])
        .sort_values('record_date')
        .assign(tot_pub_debt_out_amt=lambda x: x['tot_pub_debt_out_amt'].astype(float))
    )
    return debt_df

def fetch_all_data(api_key, week_ago_debttopenny):
    pct_change_raw = get_data_with_retry(api_key, 'NIPA', 'T10101', 'Q', 'X')
    gdp_raw = get_data_with_retry(api_key, 'NIPA', 'T10105', 'Q', 'X')
    contributors_raw = get_data_with_retry(api_key, 'NIPA', 'T10102', 'Q', 'X')
    debt_df = debt_to_penny_fetcher(week_ago_debttopenny)
    return pct_change_raw, gdp_raw, contributors_raw, debt_df