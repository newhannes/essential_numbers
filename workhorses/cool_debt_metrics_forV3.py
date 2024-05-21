##### ------------ COOL DEBT METRICS STATIC ------------ #####
# MARK: # COOL DEBT METRICS #
import streamlit as st
from full_fred.fred import Fred
import pandas as pd
FRED_API_KEY = st.secrets["FRED_API_KEY"]
fred = Fred()
st.cache_data
def get_fred_data(series_id, nickname, start_date=None, end_date=None, frequency=None, units=None, to_datetime=False, to_numeric=False, to_float=False, errors="raise", yoy=False, mom=False):
    data = fred.get_series_df(series_id, observation_start=start_date, observation_end=end_date, frequency=frequency, units=units)
    data = data.drop(columns=['realtime_start', 'realtime_end']).rename(columns={'value': nickname})
    if to_datetime:
        data["date"] = pd.to_datetime(data['date'])
    if to_numeric:
        data[nickname] = pd.to_numeric(data[nickname].replace('.', float('nan')), errors=errors)
    if to_float:
        data[nickname] = data[nickname].replace('.', float('nan')).astype(float, errors=errors)
    if yoy:
        data[f"{nickname} YoY"] = round(data[nickname].pct_change(periods=12) * 100, 1)
    if mom:
        data[f"{nickname} MoM"] = round(data[nickname].pct_change() * 100, 1)
    return data

st.cache_data
def main():
    import matplotlib.pyplot as plt
    import seaborn as sns
    import matplotlib.dates as mdates
    from matplotlib import ticker
    from datetime import date
    from datetime import datetime
    import requests 
    import json
    import tempfile
    FRED_API_KEY = st.secrets["FRED_API_KEY"]
    BLS_API_KEY = st.secrets["BLS_API_KEY"]
    fred = Fred()
    today = date.today().strftime("%Y-%m-%d")
    gold = "#967D4A"
    jade = "#84AE95"
    emerald = "#004647"
    darker_emerald = "#002F2F"
    hunter = "#002829"


    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()

    #### --------- DEBT TO FEDERAL ASSETS --------- ####
    # MARK: DEBT TO ASSETS
    ## --- Get Data from FRED --- ##
    # both are quarterly data 
    startdate = "1966-01-01"
    financial_assets = fred.get_series_df("FGTFASQ027S", observation_start=startdate, observation_end=today).rename(columns={"value": "Financial Assets"}).drop(columns=["realtime_start", "realtime_end"])
    total_debt = fred.get_series_df("GFDEBTN", observation_start=startdate, observation_end=today).rename(columns={"value": "Total Debt"}).drop(columns=["realtime_start", "realtime_end"])
    debt_to_assets = total_debt.join(financial_assets, how="inner",  lsuffix='_total_debt', rsuffix='_financial_assets')
    debt_to_assets[["Total Debt", "Financial Assets"]] = debt_to_assets[["Total Debt", "Financial Assets"]].apply(pd.to_numeric)
    debt_to_assets['debt_to_assets'] = debt_to_assets['Total Debt'] / debt_to_assets['Financial Assets']
    debt_to_assets = debt_to_assets[['date_total_debt', "Total Debt", "Financial Assets", "debt_to_assets"]]
    debt_to_assets['date_total_debt'] = pd.to_datetime(debt_to_assets['date_total_debt'])

    ## --- Textual Analysis --- ##
    quarter_dict = {1: 'Q1', 2: 'Q1', 3: 'Q1', 4: 'Q2', 5: 'Q2', 6: 'Q2', 7: 'Q3', 8: 'Q3', 9: 'Q3', 10: 'Q4', 11: 'Q4', 12: 'Q4'}
    average = round(debt_to_assets['debt_to_assets'].mean(), 1)
    most_recent = round(debt_to_assets['debt_to_assets'].iloc[-1],1)
    most_recent_date = debt_to_assets['date_total_debt'].iloc[-1]
    most_recent_quarter = quarter_dict[int(most_recent_date.month)]
    most_recent_year = most_recent_date.year
    most_recent_debt = round(debt_to_assets['Total Debt'].iloc[-1] / 1e6, 2)
    most_recent_assets = round(debt_to_assets['Financial Assets'].iloc[-1]/1e6, 2)
    text_debt_to_assets = f"""
    <ul>
        <li>For {most_recent_quarter} {most_recent_year}, the gross federal debt was ${most_recent_debt:,} trillion and the federal asset level was ${most_recent_assets} trillion, a debt to assets ratio of <b>{most_recent}</b>.</li>
        <li>Since {startdate[:4]}, the debt to assets ratio has averaged <b>{average}</b>.</li>
        <li>The current ratio is <b>{round((most_recent - average)/average *100)}%</b> above the average for this period.</li>
    </ul>
    """

    ## --- Chart Time --- ##
    # Set up
    sns.set_style("white")
    plt.rcParams["font.family"] = "Playfair Display"
    plt.figure(figsize=(12, 4))
    # Plot
    ax = sns.lineplot(x='date_total_debt', y='debt_to_assets', data=debt_to_assets, linewidth=3, color=emerald)
    # Labels
    plt.title(f'Ratio of Gross Debt to Federal Assets Since {startdate[:4]}', fontsize=18, loc="left", fontweight='bold', color="black")
    plt.xlabel('')
    plt.ylabel("Ratio")
    # Formatting
    plt.ylim(0, debt_to_assets['debt_to_assets'].max()*1.1) # make axis zero-bound
    plt.grid(axis="y", alpha=0.3)
    sns.despine()
    # Show/Save
    plt.savefig(temp_dir+"/debt_to_assets.png", dpi=900, bbox_inches='tight')


    #### -------- RATIO OF DEBT TO TOTAL WAGES -------- ####
    # MARK: DEBT TO WAGES
    # This is annual data. While BLS has quarterly data, I am having trouble comparing quarterly wages paid to the level of debt in that quarter. 
    # I would need to have the debt ADDED in that quarter to compare to the wages PAID in that quarter.
    ### --- BLS API --- ###
    headers = {'Content-type': 'application/json'}
    startyear = "2004"
    endyear = "2023"

    def bls_df(series, startyear, endyear):
        data = json.dumps({"seriesid": series, "startyear": startyear, "endyear": endyear, "catalog": True, "registrationkey": BLS_API_KEY, "annualaverage":True})
        p = requests.post("https://api.bls.gov/publicAPI/v2/timeseries/data/", data=data, headers=headers)
        json_data = json.loads(p.text)
        data = {"series_id": [], "year": [], "period": [], "value": [], "footnotes": []}
        for series in json_data['Results']['series']:
            if series['data'] == []:
                print("No data found for series:", series['seriesID'])
            else:
                seriesId = series['seriesID']
                for item in series['data']:
                    year = item['year']
                    period = item['period']
                    value = item['value']
                    footnotes = ""
                    for footnote in item['footnotes']:
                        if footnote:
                            footnotes = footnotes + footnote['text'] + ','
                    data["series_id"].append(seriesId)
                    data["year"].append(year)
                    data["period"].append(period)
                    data["value"].append(value)
                    data["footnotes"].append(footnotes[0:-1])
        df = pd.DataFrame(data)
        return df
    ### --- FRED DEBT per Year --- ###
    annual_debt = fred.get_series_df("GFDEBTN", observation_start="2000-01-01", observation_end=today, frequency="a").drop(columns=['realtime_start', 'realtime_end']).rename(columns={"value": "Total Debt"})
    annual_debt['Total Debt'] = annual_debt['Total Debt'].astype(float) * 1e6
    annual_debt['year'] = annual_debt['date'].str[:4]
    ### --- Retreieve and Clean BLS Data --- ###
    quarterly_wages = bls_df(["ENUUS00030010"], startyear, endyear)
    quarterly_wages['value'] = quarterly_wages['value'].astype(float) * 1000
    quarterly_wages["quarter-yr"] = quarterly_wages["period"] + "-" + quarterly_wages["year"]
    quarterly_wages = quarterly_wages.rename(columns={"value": "Wages"})
    annual_wages = quarterly_wages.query("period == 'Q05'")
    ### --- Merge Data and Calculate Ratio --- ### 
    debt_to_wage = annual_debt.merge(annual_wages, on="year", how="inner")
    debt_to_wage['debt_to_wages'] = debt_to_wage['Total Debt'] / debt_to_wage['Wages']
    debt_to_wage = debt_to_wage[['year', 'Total Debt', 'Wages', 'debt_to_wages']]
    ### --- Textual Analysis --- ###
    average = round(debt_to_wage['debt_to_wages'].mean(), 2)
    most_recent = debt_to_wage['debt_to_wages'].iloc[-1]
    most_recent_year = debt_to_wage['year'].iloc[-1]
    most_recent_wages = debt_to_wage['Wages'].iloc[-1]
    most_recent_debt = debt_to_wage['Total Debt'].iloc[-1]
    earliest_year = debt_to_wage['year'].iloc[0]
    earliest = debt_to_wage['debt_to_wages'].iloc[0]
    earliest_debt = debt_to_wage['Total Debt'].iloc[0]
    earliest_wages = debt_to_wage['Wages'].iloc[0]
    earliest_difference = round((earliest_debt - earliest_wages) / 1e12, 2)
    most_recent_difference = round((most_recent_debt - most_recent_wages) / 1e12, 2)
    text_debt_to_wages = f"""
    <ul>
        <li>In {earliest_year}, the gross debt exceeded total wages paid to U.S. workers by <b>${earliest_difference} trillion </b> and the debt to wage ratio was <b>{round(earliest, 2)}</b>.</li>
        <li>As of {most_recent_year}, the gross debt exceeded total wages by <b>${most_recent_difference} trillion</b> and the debt to wage ratio was <b>{round(most_recent, 2)}</b>, a <b>{round((most_recent - earliest)/earliest *100)}%</b> increase since {earliest_year}.</li>
        <li>Since {earliest_year}, the debt to wage ratio has averaged {average}, the current debt to wage ratio is <b>{round((most_recent - average)/average *100)}%</b> above the average for this period.</li>
        
    </ul>
    """
    ### --- Plot --- ###
    # Set up
    sns.set_style("white")
    plt.rcParams["font.family"] = "Playfair Display"
    plt.figure(figsize=(12, 4))
    # Plot
    sns.lineplot(x='year', y='debt_to_wages', data=debt_to_wage, linewidth=3, color=emerald)
    # Labels
    plt.title(f'Ratio of Gross Debt to Total Wages Since {earliest_year}', fontsize=18, fontweight='bold', color="black", loc="left")
    plt.xlabel('')
    plt.ylabel('Debt to Wages')
    # Formatting
    plt.ylim(0, debt_to_wage['debt_to_wages'].max()*1.1) # make axis zero-bound
    plt.xticks(debt_to_wage['year'][::4])
    plt.grid(axis='y', alpha=0.3)
    sns.despine()
    # Show/Save
    plt.savefig(temp_dir+"/debt_to_wages.png", dpi=900, bbox_inches='tight')


    #### -------- MORTGAGE RATES/HOUSING PRICES SINCE JAN 2021 -------- ####
    # MARK: MORTGAGE
    ## -- FRED Data -- ##
    mortgage_rate = fred.get_series_df("MORTGAGE30US", observation_start="2021-01-20").drop(columns={'realtime_start', 'realtime_end'}).rename(columns={"value": "Mortgage Rate"})
    mortgage_rate['Mortgage Rate'] = mortgage_rate['Mortgage Rate'].astype(float)
    median_sales = fred.get_series_df("MSPUS", observation_start="2021-01-20").drop(columns={'realtime_start', 'realtime_end'}).rename(columns={"value": "Median Sales Price"})
    median_sales['Median Sales Price'] = median_sales['Median Sales Price'].astype(float)
    ## -- Textual Analysis -- ##
    average = mortgage_rate['Mortgage Rate'].mean()
    most_recent = mortgage_rate['Mortgage Rate'].iloc[-1]
    most_recent_date = pd.to_datetime(mortgage_rate['date'].iloc[-1]).strftime('%B %d, %Y')
    before = mortgage_rate['Mortgage Rate'].iloc[0]
    house_before_biden = round(median_sales['Median Sales Price'].iloc[0])
    house_now = round(median_sales['Median Sales Price'].iloc[-1])

    def mortgage_calculator(principal, rate, years):
        r = rate / 100 / 12
        n = years * 12
        payment = principal * r / (1 - (1 + r)**-n)
        return payment
    mortgage_before = round(mortgage_calculator(house_before_biden, before, 30))
    mortgage_now = round(mortgage_calculator(house_now, most_recent, 30))
    text_mortgage_rate = f"""
    <ul>
        <li>The 30 year fixed mortgage rate when Biden took office was <b>{before}%</b>.</li>
        <li>The 30 year fixed mortgage rate is now <b>{most_recent}%</b>, a <b>{round((most_recent - before)/before *100)}%</b> increase under Biden.</li>
        <li>Before Biden took office, the median sales price of a house was <b>${house_before_biden:,}</b>, now it is <b>${house_now:,}</b>, a <b>{round((house_now-house_before_biden)/house_before_biden*100)}%</b> increase under Biden</li>
        <li>For a typical mortgage before Biden the monthly payment was <b>${mortgage_before:,}</b>. Now, a typical mortgage payment would be <b>${mortgage_now:,}</b>, an increase of <b>${mortgage_now-mortgage_before:,}</b>.</li>
    </ul>
    """
    ## -- Plot Time -- ##
    # Set up
    mortgage_rate['date'] = pd.to_datetime(mortgage_rate['date'])
    sns.set_style("white")
    plt.rcParams["font.family"] = "Playfair Display"
    plt.figure(figsize=(12, 4))
    # Plot
    ax = sns.lineplot(x='date', y='Mortgage Rate', data=mortgage_rate, linewidth=3, color=emerald)
    # Labels
    plt.title('30 Year Fixed Mortgage Rate Since January 2021', fontsize=18, fontweight='bold', color="black", loc="left")
    plt.xlabel('')
    plt.ylabel('Mortgage Rate (%)')
    # Formatting
    #ax.xaxis.set_major_locator(mdates.MonthLocator(interval=5))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    plt.ylim(0, mortgage_rate['Mortgage Rate'].max()*1.1) # make axis zero-bound
    plt.grid(axis='y', alpha=0.3)
    sns.despine()
    # Show/Save
    plt.savefig(temp_dir+"/mortgage_rate.png", dpi=900, bbox_inches='tight')


    ### --- OUR BUDGET VS PRESIDENT BUDGET --- ###
    # MARK: OUR BUDGET VS PB
    ## GET LOCAL DATA ##
    df = pd.read_excel("data/gross_debt_gdp.xlsx", header=1)
    df = df.iloc[[4,19], 1:12]
    df['source'] = ["HBC", "Biden's Budget"]
    df_long = df.melt(id_vars='source', var_name='year', value_name='debt_gdp')
    df_long['debt_gdp'] = round(df_long['debt_gdp'] * 100)
    ## FRED Gross Debt to GDP ##
    gross_debt_to_gdp = fred.get_series_df('GFDGDPA188S').drop(columns=['realtime_start', 'realtime_end'])
    gross_debt_to_gdp['date'] = gross_debt_to_gdp['date'].apply(lambda x: x[0:4])
    gross_debt_to_gdp['value'] = round(gross_debt_to_gdp['value'].astype(float))
    gross_debt_to_gdp = gross_debt_to_gdp.query('date >= "2000"')
    gross_debt_to_gdp = gross_debt_to_gdp.rename(columns={'date': 'year', 'value': 'debt_gdp'})
    gross_debt_to_gdp['source'] = "Actual"



    ## COMBINE DATA ##
    df = pd.concat([df_long, gross_debt_to_gdp], axis=0)


    historic_data_2023 = df[(df['year'] == "2023") & (df['source'] == 'Actual')]['debt_gdp'].values[0] # Get the 'Historic Data's 2023 debt_gdp value
    sources = df[df['source'] != 'Actual']['source'].unique() # Get the unique sources other than 'Historic Data'
    new_rows = [pd.DataFrame({'year': ["2023"], 'debt_gdp': [historic_data_2023], 'source': [source]}) for source in sources] # For each source, create a new row with the 'Historic Data's 2023 debt_gdp value

    df = pd.concat([df] + new_rows, ignore_index=True)
    df['year'] = pd.to_numeric(df['year'])
    df = df.sort_values(by='year')

    ## -- Textual Analysis -- ##
    earliest_year = df['year'].min()
    latest_year = df['year'].max()
    earliest = df[df['year'] == earliest_year]['debt_gdp'].values[0].astype(int)
    current_year = 2023
    current = round(df.query(f"source == 'Actual' & year == {current_year}")["debt_gdp"].values[0])
    biden_latest = round(df.query(f"source == \"Biden's Budget\" & year == {latest_year}")['debt_gdp'].values[0])
    hbc_latest = round(df.query(f"source == 'HBC' & year == {latest_year}")['debt_gdp'].values[0])

    comparison_html = f"""
    Rather than address the rampant debt that exceeds the country's GDP by <b>{current}</b>% in {current_year}, President Biden's budget exacerbates this imbalance. The House Republican Budget offers a return to fiscal sanity.
    <ul>
        <li>Under the President's Budget, the gross debt to GDP ratio will be <b>{biden_latest}%</b> in {latest_year}, an increase of {biden_latest-current} percentage points since {current_year}.</li>
        <li>Under the House Republican Budget, the gross debt to GDP ratio will be <b>{hbc_latest}%</b> in {latest_year}, a decrease of {abs(hbc_latest-current)} percentage points since {current_year}</li>
    </ul>
    """
    ## -- Plot Time -- ##
    colors = {'HBC': darker_emerald, 'Biden\'s Budget': gold, 'Actual': jade}
    sources = ["HBC", "Biden's Budget", "Actual"] # Get the unique sources
    # Set the style and font
    sns.set_style("white")
    plt.rcParams["font.family"] = "Playfair Display"

    # Create a new figure
    plt.figure(figsize=(12, 4))

    # For each source, add a trace to the figure
    for source in sources:
        df_source = df[df['source'] == source]
        plt.fill_between(df_source['year'], df_source['debt_gdp'], color=colors.get(source, 'black'), alpha=0.5, label=source)
        plt.plot(df_source['year'], df_source['debt_gdp'], color=colors.get(source, 'black'))
    plt.legend()
    # Set the title and labels
    plt.title('House Republican Budget vs President Biden\'s Budget', fontsize=18, fontweight='bold', color="black", loc="left")
    plt.xlabel('')
    plt.gca().yaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.0f}%'))
    plt.ylabel('Gross Debt as Percentage of GDP')
    plt.grid(axis='y', alpha=0.3)
    sns.despine()
    plt.savefig(temp_dir+"/budget_comparison.png", dpi=900, bbox_inches='tight')



    #### ---- RATE OF INCREASE ---- ####
    # MARK: RATE OF INCREASE
    ###NOTE: I make a call to the debt to penny dataset in debt tracker. Not sure if I can consolidate to one call or not. 
    ## Treasury API ##
    # Get debt data
    treasury_link = 'https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_to_penny?page[size]=10000'
    p = requests.get(treasury_link)
    data = p.json()
    debt_df = pd.DataFrame(data['data'])
    # Clean debt data
    debt_df['tot_pub_debt_out_amt'] = debt_df['tot_pub_debt_out_amt'].astype(float)
    debt_df = debt_df[['record_date','tot_pub_debt_out_amt']]
    debt_df["record_date"] = pd.to_datetime(debt_df["record_date"])
    debt_df["date_year_ago"] = debt_df["record_date"] - pd.DateOffset(years=1)
    # Get the debt from a year ago (or the closest date to a year ago)
    debt_df.set_index("record_date", inplace=True) # Set 'record_date' as the index
    debt_df["debt_year_ago"] = debt_df["date_year_ago"].apply(lambda x: debt_df["tot_pub_debt_out_amt"].asof(x)) # Use 'asof' to find the closest date
    debt_df.reset_index(inplace=True)
    # Calculate Rate of Increase
    debt_df["year_increase"] = debt_df["tot_pub_debt_out_amt"] - debt_df["debt_year_ago"]
    debt_df['second_increase'] = round(debt_df['year_increase'] / 365 / 24 / 60 / 60)
    ## -- Textual Analysis -- ##
    average = round(debt_df['second_increase'].mean())
    most_recent = round(debt_df['second_increase'].iloc[-1])
    most_recent_date = debt_df['record_date'].iloc[-1].strftime('%B %d, %Y')
    #earliest = debt_df['second_increase'].dropna().iloc[0]
    #earliest_date = debt_df['record_date'].iloc[0].strftime('%Y')
    earliest_date = debt_df.dropna()['record_date'].iloc[0].strftime('%Y')
    pre_pandemic = round(debt_df[debt_df['record_date']==pd.to_datetime('2020-02-10')]['second_increase'].values[0])
    rate_increase_html = f"""
    Since {earliest_date}, the average increase in the gross debt every second has been <b>${average:,}</b>.
    <ul>
        <li>The current rate is <b>{round((most_recent - average)/average *100)}%</b> above the average for this period.</li>
        <li>The current rate is <b>{round((most_recent-pre_pandemic)/pre_pandemic*100)}%</b> above the pre-pandemic rate of ${pre_pandemic:,} per second.</li>
    </ul>
    """
    ## -- Plot Time -- ##
    debt_df['second_increase'] = debt_df['second_increase'] / 1000
    sns.set_style("white")
    plt.rcParams["font.family"] = "Playfair Display"
    plt.figure(figsize=(12, 4))
    sns.lineplot(x='record_date', y='second_increase', data=debt_df, linewidth=3, color=emerald)
    plt.title('Rate of Debt Accumulation Since 1994', fontsize=18, fontweight='bold', color="black", loc="left")
    plt.xlabel('')
    plt.gca().yaxis.set_major_formatter('${x:,.0f}k')
    plt.ylabel('Debt Increase per Second')
    plt.grid(axis='y', alpha=0.3)
    sns.despine()
    plt.savefig(temp_dir+"/debt_increase.png", dpi=600, bbox_inches='tight')


    #### ---- CBO Projections ---- ####
    # MARK: CBO PROJECTIONS
    ### FRED Gross Debt to GDP ###
    gross_debt_to_gdp = fred.get_series_df('GFDGDPA188S').drop(columns=['realtime_start', 'realtime_end'])
    gross_debt_to_gdp['date'] = gross_debt_to_gdp['date'].apply(lambda x: x[0:4])
    gross_debt_to_gdp['value'] = round(gross_debt_to_gdp['value'].astype(float))
    gross_debt_to_gdp = gross_debt_to_gdp.query('date > "1944"')

    ### CBO LTBO GROSS DEBT TO GDP ###
    cbo_ltbo = pd.read_excel("data/51119-2024-03-LTBO-budget.xlsx", sheet_name=1, header=9)
    cbo_ltbo = cbo_ltbo[["Fiscal year", "Gross federal debte"]].rename(columns={"Fiscal year": "date", "Gross federal debte": "value"}).dropna()
    cbo_ltbo['value'] = round(cbo_ltbo['value'])
    ### MERGE THE TWO DATASETS ###
    combined = pd.concat([gross_debt_to_gdp, cbo_ltbo], axis=0)
    combined['date'] = combined['date'].astype(str)
    ## -- Textual Analysis -- ##
    current_year = "2023"
    earliest_year = combined['date'].iloc[0]
    latest_year = combined['date'].iloc[-1]
    latest = round(combined[combined['date'] == latest_year]['value'].values[0])
    peak_actual = round(gross_debt_to_gdp['value'].max())
    peak_year = combined[combined['value'] == peak_actual]['date'].values[0]
    peak_before = round(combined.query(f"date < '{peak_year}'")['value'].max())
    peak_before_year = combined[combined['value'] == peak_before]['date'].values[0]
    average = round(combined.query(f"date < '{current_year}'")['value'].mean())
    random_html = f"""
    <ul>
        <li> The gross debt to GDP ratio peaked at {peak_actual}% in {peak_year}. This was the highest level since {peak_before}% in {peak_before_year}.</li>
        <li> The gross debt to GDP ratio averaged {average}% from {earliest_year} to {current_year}.</li>
        <li> Under current law, CBO projects our debt to GDP will reach <b>{latest}%</b> in {latest_year}. This is <b>{round(latest-average)} percentage points</b> above the historical average since {earliest_year}.</li>
    </ul>
    """
    ## -- Plot Time -- ##
    sns.set_style("white")
    plt.rcParams["font.family"] = "Playfair Display"
    plt.figure(figsize=(12, 4))
    plt.fill_between(combined['date'], combined['value'], color="#84AE95", alpha=0.8)
    plt.title("Gross Debt to GDP, Historical and Projected", fontsize=18, fontweight='bold', color="black", loc="left")
    plt.xticks(combined['date'][::10])
    plt.ylabel('Gross Debt as Percentage of GDP')
    plt.gca().yaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.0f}%'))
    sns.despine()
    # Add the annotations
    actual_value_2023 = round(combined.loc[combined['date'] == "2023", 'value'].values[0])
    projected_value_2054 = round(combined.loc[combined['date'] == "2054", 'value'].values[0])
    plt.annotate(f'Actual: {actual_value_2023}% in 2023', ("2023", actual_value_2023), textcoords="offset points", xytext=(-20,20), ha='center', color='black', arrowprops=dict(arrowstyle='->', color='black'))
    plt.annotate(f'Projected: {projected_value_2054}% in 2054', ("2054", projected_value_2054), textcoords="offset points", xytext=(-40,10), ha='center', color='black', arrowprops=dict(arrowstyle='->', color='black'))
    plt.savefig(temp_dir+"/cbo_projections.png", dpi=600, bbox_inches='tight')

    #### ---- GDP ADDED VS DEBT ADDED ---- ####
    # MARK: GDP VS DEBT
    ## -- FRED GDP -- ##
    start = "2022-01-01"
    today_quarter = quarter_dict[int(today[5:7])]
    gdp = fred.get_series_df("GDP", observation_start=start, observation_end=today).rename(columns={"value": "GDP"}).drop(columns=['realtime_start', 'realtime_end'])
    gdp['quarter'] = gdp['date'].apply(lambda x: f"{quarter_dict[int(x[5:7])]}")
    gdp['year'] = gdp['date'].apply(lambda x: x[:4])
    gdp["GDP"] = gdp["GDP"].astype(float) * 1e9
    gdp = gdp.query("quarter == 'Q4'").drop(columns=['date', 'quarter'])
    ## -- FRED Debt -- ##
    debt = fred.get_series_df("GFDEBTN", observation_start=start, observation_end=today).rename(columns={"value": "Debt"}).drop(columns=['realtime_start', 'realtime_end'])
    debt['quarter'] = debt['date'].apply(lambda x: f"{quarter_dict[int(x[5:7])]}")
    debt['year'] = debt['date'].apply(lambda x: x[:4])
    debt["Debt"] = debt["Debt"].astype(float) * 1e6
    debt = debt.query("quarter == 'Q4'").drop(columns=['date', 'quarter'])

    ## -- Textual Analysis -- ##
    gdp_increase = gdp['GDP'].iloc[-1] - gdp['GDP'].iloc[0]
    gdp_day = gdp_increase / 365
    debt_increase = debt['Debt'].iloc[-1] - debt['Debt'].iloc[0]
    debt_day = debt_increase / 365
    text_gdp_debt = f"""
    <ul>
        <li>In 2023, GDP grew by <b>${gdp_increase/1e12:.2f}</b> trillion and gross debt grew by <b>${debt_increase/1e12:.2f}</b> trillion.</li>
        <li>This equates to a <b>${gdp_day/1e9:,.2f} billion</b> increase in GDP every day and <b>${debt_day/1e9:,.2f} billion </b> increase in debt every day in 2023.</li>
        <li>In 2023, the growth in the gross debt was <b>{round((debt_increase/gdp_increase)*100)}%</b> higher than the growth in GDP.</li>
    </ul>
    """
    ## -- Chart Time -- ##
    # Data
    categories = ['GDP Added', 'Debt Added']
    values = [gdp_increase/1e12, debt_increase/1e12]
    # Plot
    sns.set_style("white")
    plt.rcParams["font.family"] = "Playfair Display"
    plt.figure(figsize=(12, 4))
    # Create horizontal bar chart
    bars = plt.barh(categories, values, color=[gold, emerald])
    # Add data values inside the bars
    for bar, category in zip(bars, categories):
        width = bar.get_width()
        plt.text(width - 0.07, bar.get_y() + bar.get_height() / 2, f'${width:.2f} trillion', ha='right', va='center', color='white', fontweight='bold', fontsize=14)
        plt.text(bar.get_x() + 0.05, bar.get_y() + bar.get_height() / 2, category, ha='left', va='center', color='white', fontweight="bold", fontsize=14)
    plt.title('GDP Added vs Debt Added in 2023', fontsize=18, fontweight='bold', color="black", loc="left")
    plt.xlabel('')
    plt.yticks([])
    plt.xticks([])
    sns.despine(left=True, bottom=True)
    plt.savefig(temp_dir+"/gdp_debt.png", dpi=600, bbox_inches='tight')
    

    ##### -------- Basic Debt Graph -------- ##### 
    ### --- FRED Data --- ###
    start_date = '2000-01-01'
    working_df = fred.get_series_df('GFDEBTN', observation_start=start_date, observation_end=today, frequency="a").drop(columns=['realtime_start', 'realtime_end'])
    working_df['value'] = pd.to_numeric(working_df['value'])
    working_df['date'] = pd.to_datetime(working_df['date'])
    working_df["value"] = working_df["value"] / 1e6 # Convert to trillions
    working_df['year'] = working_df['date'].dt.year

    ### --- Chart Time 2 --- ###

    sns.set_style("white")
    plt.rcParams['font.family'] = "Playfair Display"
    plt.figure(figsize=(12, 4))
    sns.lineplot(data=working_df, x="year", y="value", linewidth=3.5, color=gold)
    ymin, ymax = plt.gca().get_ylim()
    plt.fill_between(working_df['year'], working_df["value"], color=gold, alpha=0.85)
    plt.ylim(0, ymax)
    plt.grid(axis="y", alpha=0.3)
    plt.title(f"Gross Federal Debt Since {start_date[:4]} ", fontdict={ 'fontsize': 18, 'weight': 'bold'})
    plt.xlabel('')
    plt.ylabel('Trillions of Dollars', color='white')
    plt.gca().yaxis.set_major_formatter('${:,.0f}'.format)
    sns.despine()
    plt.savefig(temp_dir+"/basic_debt.png", dpi=600, bbox_inches='tight')

    ##### ------- Debt Timeline ------- #####
    # MARK: DEBT TIMELINE
    ### Treasury API ###
    # Get and clean HISTORICAL debt data
    fields = 'record_date, record_fiscal_year, debt_outstanding_amt'
    treasury_link = f'https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_outstanding?fields={fields}&page[size]=10000'
    p = requests.get(treasury_link)
    data = p.json()
    historic_debt = pd.DataFrame(data['data'])
    historic_debt['debt_outstanding_amt'] = historic_debt['debt_outstanding_amt'].astype(float)
    historic_debt['record_date'] = pd.to_datetime(historic_debt['record_date'])
    historic_debt["debt_trillions"] = historic_debt["debt_outstanding_amt"] / 1e12 # Convert to trillions
    # Get and clean CURRENT debt data
    fields = 'record_date, tot_pub_debt_out_amt'
    treasury_link = f'https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_to_penny?fields={fields}&filter=record_date:gte:2024-01-01&page[size]=10000'
    p = requests.get(treasury_link)
    data = p.json()
    current = pd.DataFrame(data['data'])
    current['tot_pub_debt_out_amt'] = current['tot_pub_debt_out_amt'].astype(float)
    current["in trillions"] = current["tot_pub_debt_out_amt"] / 1e12 # Convert to trillions
    current['record_date'] = pd.to_datetime(current['record_date'])
    ###### ------ Chart Time ------ ######
    plt.figure(figsize=(12,4))
    sns.set_style("white")
    plt.rcParams['font.family'] = 'Garet'
    sns.lineplot(data=historic_debt, x='record_date', y='debt_trillions', linewidth=4.5, color=emerald)
    plt.fill_between(historic_debt["record_date"], historic_debt['debt_trillions'], color=emerald, alpha=0.99)
    plt.title('History of the Debt', fontsize=18, pad=15, fontweight='bold', loc='left')
    plt.xlabel("")
    plt.ylabel("Debt Outstanding (Trillions)", labelpad=8)
    # Customize xticks (date range)
    start, end = pd.to_datetime('1800'), pd.to_datetime('2020')
    years = pd.date_range(start, end, freq='50YE').year
    plt.xticks(ticks=[pd.to_datetime(year, format='%Y') for year in years], labels=years)
    plt.gca().yaxis.set_major_formatter(ticker.StrMethodFormatter('${x:,.0f}T'))
    sns.despine(left=True, bottom=True)

    # Add annotations
    start_date = historic_debt.iloc[0, 0] # First date in dataset
    start_debt_actual = historic_debt.iloc[0, 2] # First debt in dataset, actual
    start_debt = historic_debt.iloc[0, 3] # First debt in dataset, in trillions
    plt.annotate(f"${start_debt_actual/1e6:,.0f} million in {start_date.year}", xy=(start_date, start_debt), xytext=(datetime(1790,1,1), 3.2), fontsize=9,
                arrowprops=dict(color='black', arrowstyle='->'))
    billion_date = datetime(1863,1,7)
    bil_text_date = datetime(1850,1,1)
    plt.annotate(f"$1 Billion in {billion_date.year}", xy=(billion_date, .001), xytext=(bil_text_date, 3.2),
                arrowprops=dict(color='black', arrowstyle='->'), fontsize=9)
    trillion_date = historic_debt.query("debt_trillions >= 1").iloc[0, 0] # First time debt exceeds $1 trillion, date
    tril_text_date = datetime(1940,1,1) # Used to position text
    plt.annotate(f"$1 Trillion in {trillion_date.year}", xy=(trillion_date, 1), xytext=(tril_text_date, 3.2),
                arrowprops=dict(color='black', arrowstyle='->'), fontsize=9)
    ten_trillion_date = historic_debt.query("debt_trillions >= 10").iloc[0, 0] # First time debt exceeds $10 trillion, date
    ten_tril_text_date = datetime(1961,1,1) # Used to position text
    plt.annotate(f"$10 Trillion in {ten_trillion_date.year}", xy=(ten_trillion_date, 10), xytext=(ten_tril_text_date, 10),
                arrowprops=dict(color='black', arrowstyle='->'), fontsize=9)
    twenty_trillion_date = historic_debt.query("debt_trillions >= 20").iloc[0, 0] # First time debt exceeds $20 trillion, date
    twenty_tril_text_date = datetime(1970,1,1) # Used to position text
    plt.annotate(f"$20 Trillion in {twenty_trillion_date.year}", xy=(twenty_trillion_date, 20), xytext=(twenty_tril_text_date, 20),
                arrowprops=dict(color='black', arrowstyle='->'), fontsize=9)
    # Add level before biden
    biden_date = datetime(2021,1,20)
    biden_text_date = datetime(1950,1,1)
    debt_before_biden_date = historic_debt.query("record_date < @biden_date").iloc[-1,0]
    debt_before_biden_debt = historic_debt.query("record_date < @biden_date").iloc[-1,3] #in trillions
    plt.annotate(f"Debt Before Biden: ${debt_before_biden_debt:.0f} Trillion", xy=(debt_before_biden_date, debt_before_biden_debt), xytext=(biden_text_date, debt_before_biden_debt),
                arrowprops=dict(color='black', arrowstyle='->'), fontsize=9)

    plt.text(current.iloc[-1]['record_date'] - pd.Timedelta(weeks=140), current.iloc[-1]['in trillions']*1.01, f"Debt Now: ${current.iloc[-1]['in trillions']:.2f} Trillion", fontsize=12, fontweight="bold",ha="center")
    # Save
    plt.savefig(temp_dir+"/debt_timeline.png", dpi=900, bbox_inches='tight')


    ####### ------- Credit Card Stuff ------- #######
    #MARK: CREDIT CARD
    ## -- API Calls -- ##
    deliquent_30 = get_fred_data('RCCCBACTDPD30P', '30_days', start_date="2019-10-01", to_datetime=True, to_numeric=True)
    num_accounts = get_fred_data('RCCCBNUMACT', 'num_accounts', start_date="2019-10-01", to_datetime=True, to_numeric=True)
    apr = get_fred_data('TERMCBCCALLNS', 'APR', to_datetime=True, to_float=True).dropna()
    biden = pd.to_datetime('2021-01-20')
    quarter_b4_biden = pd.to_datetime('2020-10-01')
    ## -- Textual Analysis -- ##
    # Deliquency and accounts number
    current_del = deliquent_30['30_days'].iloc[-1]
    current_acc = num_accounts['num_accounts'].iloc[-1]
    before_biden_del = deliquent_30.query("date == @quarter_b4_biden")['30_days'].values[0]
    before_biden_acc = num_accounts.query("date == @quarter_b4_biden")['num_accounts'].values[0]
    # Calculate the number of accounts that are deliquent
    current_del_acc = current_del/100 * current_acc
    before_biden_del_acc = before_biden_del/100 * before_biden_acc
    # APR rates
    apr_current = apr['APR'].iloc[-1]
    apr_before_biden = apr.query("date < @biden")['APR'].iloc[-1]

    html_credit_card = f"""
    <ul>
    <li>Before Biden took office the APR for credit cards was <b>{apr_before_biden:.2f}%</b> and the percentage of credit card accounts deliquent was <b>{before_biden_del:.2f}%</b>. </li> 
    <li>Now, the APR is <b>{apr_current:.2f}%</b> and the percentage of credit card accounts deliquent is <b>{current_del:.2f}%</b>.</li>
    <li>The APR has increased by <b>{apr_current - apr_before_biden:.2f}</b> percentage points and the deliquency rate has increased by <b>{current_del - before_biden_del:.2f}</b> percentage points.</li>
    <li>Since {quarter_b4_biden.year} there are <b>{current_del_acc - before_biden_del_acc:.1f} million</b> more deliquent credit card accounts.</li>
    </ul>
    """
    ### ---- Chart Time ---- ###
    # Set up
    chart_data = apr.query("date >= @quarter_b4_biden")
    plt.figure(figsize=(12, 4))
    sns.set_style("white")
    plt.rcParams['font.family'] = "Playfair Display"
    # Plot
    sns.lineplot(data=chart_data, x='date', y='APR', color=emerald, linewidth=3.5)
    # Labels
    plt.title(f"Credit Card Rates Since {chart_data['date'].iloc[0].strftime('%B %Y')}", fontsize=18, fontweight='bold', loc="left")
    plt.xlabel("")
    plt.ylabel("APR")
    # Formatting 
    #plt.xticks(chart_data["date"][::4])
    plt.gca().yaxis.set_major_formatter(ticker.PercentFormatter(decimals=0))
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    plt.grid(axis='y', alpha=0.3)
    sns.despine()
    # Show/Save
    plt.savefig(temp_dir+"/credit_card.png", dpi=900, bbox_inches='tight')


    #### ---- Manufacturers New Orders ---- ####
    # MARK: NEW ORDERS
    ### --- Query FRED API for Data --- ###
    start = "1974-01-01"
    # Manufacturers' New Orders: Nondefense Capital Goods Excluding Aircraft
    new_orders = get_fred_data("NEWORDER", "New Capital Orders", start_date=start, to_datetime=True, to_numeric=True, yoy=True)
    new_orders.set_index("date", inplace=True)
    new_orders.dropna(inplace=True)
    ### --- Textual Analysis --- ###
    current = new_orders.iloc[-1]
    #dollars = current["New Capital Orders"]
    yoy = current["New Capital Orders YoY"]
    before_biden = new_orders.loc["2021-01-01"]
    yoy_bb = before_biden["New Capital Orders YoY"]
    #dollars_bb = before_biden["New Capital Orders"]
    past_yr_avg = new_orders.iloc[-12:]["New Capital Orders YoY"].mean()

    new_orders_html = f"""
    <ul>
        <li> When Biden took office in January 2021, annual growth in new capital investments was <strong>{yoy_bb}%</strong>. </li>
        <li> Now, annual growth in new capital investments is <strong>{yoy}%</strong>. </li>
        <li> Over the past year, annual growth in new capital investments has averaged <strong>{past_yr_avg}%</strong>. </li>
    </ul>
    """
    ### --- Chart Time --- ###
    # Chart Data
    chart_data = new_orders.loc["2021-01-01":]
    sns.set_style("white")
    plt.rcParams['font.family'] = 'Playfair Display'
    plt.figure(figsize=(12, 4))
    sns.lineplot(data=chart_data, x=chart_data.index, y="New Capital Orders YoY", color=emerald, linewidth=3.5)
    title = f"New Orders for Nondefense Capital Goods Excluding Aircraft \n Since {chart_data.index[0].strftime('%B %Y')}"
    plt.title(title, fontsize=18, fontweight='bold', loc="left", pad=15)
    # Add a vertical line at a specific date
    line_date = pd.Timestamp("2022-02-01")
    plt.axvline(line_date, color=gold, linestyle="-", linewidth=2.5)

    # Add a label to the vertical line
    plt.annotate('Fed begins rate hikes', xy=(line_date, 0), xytext=(10, 190), textcoords='offset points')

    plt.ylabel("Annual Growth")
    plt.gca().yaxis.set_major_formatter(ticker.StrMethodFormatter("{x:.0f}%"))
    plt.xlabel("")
    plt.xticks()
    plt.grid(axis="y", alpha=0.3)
    #Show the x axis as Month and Year
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    sns.despine()
    plt.savefig(temp_dir+"/new_orders.png", dpi=900, bbox_inches='tight')



    #### ----- HOUSEHOLD DEBT PROJECTIONS ----- ####
    # MARK: HOUSEHOLD DEBT
    ## -- Load data -- ##
    data = pd.read_excel("data/051624 gross federal debt per household.xlsx", header=1).rename(columns={"Unnamed: 0":"Year"})
    data.columns = ["Year", "Gross Debt per Household"]
    data = data.dropna()
    data["Gross Debt per Household"] = data["Gross Debt per Household"] /1000
    data["Year"] = pd.to_numeric(data["Year"])

    ## -- Textual Analysis -- ##
    current_year = 2023
    current = data.loc[data["Year"] == current_year, "Gross Debt per Household"].values[0]
    projected = data.iloc[-1]["Gross Debt per Household"] 
    projected_year = data.iloc[-1]["Year"]

    household_html = f"""
    <ul>
        <li> In {current_year}, the gross federal debt per household was <b>${current:,.0f} thousand</b>.</li>
        <li> By {int(projected_year)}, the gross federal debt per household is projected to be <b>${projected/1000:,.0f} million</b>.</li>
    </ul>
    """
    ## -- Plot -- ##
    plt.figure(figsize=(12,4))
    sns.set_style("white")
    plt.rcParams["font.family"] = "Playfair Display"
    plt.grid(axis="y", alpha=0.3)
    sns.lineplot(x="Year", y="Gross Debt per Household", data=data, color=emerald, linewidth=1)
    plt.fill_between(data["Year"], data["Gross Debt per Household"], color=emerald, alpha=0.99)
    plt.title("Gross Debt Per Household, 2000-2054", fontsize=18, fontweight="bold", pad=20, loc="left")
    plt.xlabel("")
    # Add annotations
    current = data[data.Year == 2023]
    current_year = current["Year"].values[0]
    current_debt = current["Gross Debt per Household"].values[0]

    plt.annotate(f"Actual, {current_year} : ${current_debt:,.0f}K per household", 
                xy=(current_year, current_debt), 
                xytext=(2012, 425), fontsize=12, color=hunter, fontweight="bold",
                arrowprops=dict(arrowstyle="-", color=hunter, lw=1.5))

    last = data[data.Year == 2054]
    last_year = last["Year"].values[0]
    last_debt = last["Gross Debt per Household"].values[0]
    plt.annotate(f"Projected, {last_year} : ${last_debt/1000:,.2f} million per household",
                    xy=(last_year, last_debt), 
                    xytext=(2025, 1000), fontsize=12, color=hunter, fontweight="bold",
                    arrowprops=dict(arrowstyle="-", color=hunter, lw=1.5))

    plt.gca().yaxis.set_major_formatter(ticker.StrMethodFormatter("${x:,.0f}K"))
    sns.despine(bottom=True, left=True)
    plt.savefig(temp_dir+"/household_debt.png", dpi=600, bbox_inches='tight')

    # ---- RETURN ---- #
    return temp_dir, text_debt_to_assets, text_debt_to_wages, text_mortgage_rate, comparison_html, rate_increase_html, random_html, text_gdp_debt, html_credit_card, new_orders_html, household_html, today


###### -------- RUN THE SCRIPT -------- ######
#temp_dir, text_debt_to_assets, text_debt_to_wages, text_mortgage_rate, comparison_html, rate_increase_html, random_html, text_gdp_debt, html_credit_card, new_orders_html, today = main()
print("Cool Debt Metrics script complete.")