########## =========== GENERATE CHARTS FOR GDP REPORT =========== ##########

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib import font_manager
import seaborn as sns
import pandas as pd
from datetime import datetime
import os

light_grey = "#C5C6C7" 
light_grey_2 = "#B8BBBE"
grey = "#6A6E73" 
dark_grey = "#656565"
dark_grey_2 = "#555555"
dark_grey_3 = "#3C3C3C"
rose_red = "#B03A2E"
emerald = "#004647"
jade = "#84AE95"
hunter = "#002829"
beige = "#F2EFE9"
chart_background = "white"

VISUALS_PATH = "output/charts"
STYLE_PATH = "inputs/housebudget-ebgaramond.mplstyle"
FONT_PATH = "inputs/EBGaramond-VariableFont_wght.ttf"

CUSTOM_FONT = font_manager.FontProperties(fname=FONT_PATH)


def apply_style():
    if os.path.exists(STYLE_PATH):
        plt.style.use(STYLE_PATH)
    else:
        print("Style file not found. Using default style.")
        plt.style.use("default")

## MARK: Overview
def overview_chart(pct_change_raw, current_q):
    
    ## Data prep
    gdp_past_2yrs = pct_change_raw.query("LineDescription == 'Gross domestic product' and TimePeriod >= '2022Q1'")[["TimePeriod", "DataValue"]]
    gdp_past_2yrs['date'] = [x[-2:] + "\n" + x[:-2] for x in gdp_past_2yrs.TimePeriod]
    first_q = gdp_past_2yrs.iloc[0]["TimePeriod"]

    ## Setup
    apply_style()
    # plt.rcParams['font.sans-serif'] = "EB Garamond"
    fig, ax = plt.subplots(figsize=(8,3.5))
    fig.set_facecolor(chart_background)
    ax.set_facecolor(chart_background)

    ## Plot
    bars = sns.barplot(data=gdp_past_2yrs, x="date", y="DataValue", ax=ax, color=light_grey_2)

    ## Labels
    ax.set_title(f"Annualized real GDP growth since {first_q[-2:]} {first_q[:4]}", fontsize=16, pad=20, color=dark_grey_3)
    ax.set_xlabel("")
    ax.set_ylabel("")

    ## Format
    ax.set_yticks([])
    ax.xaxis.set_tick_params(length=0, labelcolor=dark_grey_2)
    ax.spines['bottom'].set_position(('outward', 8))  # Move the bottom spine outward 
    bars.patches[-1].set_facecolor(emerald) # color the most recent bar
    bars.patches[-1].set_width(0.85) # widen the most recent bar
    sns.despine(left=True, bottom=True)

    for i, val in enumerate(gdp_past_2yrs["DataValue"]):
        if gdp_past_2yrs.iloc[i]["TimePeriod"] == current_q:
            color = emerald
            fontweight = "bold"
            fontsize = 15
            adjust = 0
            va = 'bottom'
        else:
            color = dark_grey_2
            fontweight = "normal"
            fontsize = 11.2
            adjust = 0.5 if val > 0 else -0.4
            adjust = 0 if (val > 0 and val < 0.7) else adjust # bar is too short to fit the label
            va = 'bottom' if val > 0 else 'top'
        bars.text(i, val - adjust, f"{val:.1f}", color=color, ha='center', va=va, fontweight=fontweight, fontsize=fontsize)

    ## Save
    fig_since22 = ax.get_figure()
    fig_since22.savefig(f"{VISUALS_PATH}/since22.png", bbox_inches='tight', dpi=300)

## MARK: Composition
def composition_chart(composition_chart_data, current_q):

    ## Prep data
    composition_chart_data = composition_chart_data.pivot(columns="NAME", values="DataValue", index="sign")
    column_order = composition_chart_data.sum().sort_values(ascending=False).index
    composition_chart_data = composition_chart_data[column_order] 

    ## Setup
    apply_style()
    # plt.rcParams['font.family'] = CUSTOM_FONT_NAME
    fig, ax = plt.subplots(figsize=(9,4))
    fig.set_facecolor(chart_background)
    ax.set_facecolor(chart_background)
    start_color = 200
    end_color = 0
    custom_pal = sns.diverging_palette(start_color, end_color, l=60)
    sns.set_palette(custom_pal)

    ## Plot
    composition_chart_data.plot(kind="barh", stacked=True, ax=ax, position=-1, width=0.8)

    ## Labels
    title = f"Percentage point contributions to GDP growth in {current_q[-2:]} {current_q[:4]}"
    ax.set_title(title, fontsize=16, pad=25, x=-0.065, ha='left', color=dark_grey_3, fontproperties=CUSTOM_FONT)
    ax.set_ylabel("")

    ## Format
    sns.despine(left=True, bottom=True)
    for container in ax.containers:
        labels = [f'{v.get_width():.1f}' if v.get_width() != 0 else '' for v in container]
        ax.bar_label(container, labels=labels, label_type='center', fontweight='bold', fontsize=13, color=dark_grey_3)
    ax.set_yticks([])
    ax.set_xticks([])
    ax.legend(loc='center', bbox_to_anchor=(0.5, 1), frameon=False, ncols=4, columnspacing=0.7, labelcolor=dark_grey_3) # move legend to the top

    ## Annotations
    total_sum = composition_chart_data.sum().sum() # Calculate the sum of the two bars
    bracket_x = composition_chart_data.sum(axis=1).max()  # Add a bracket
    bracket_y = [1.15, 2.25]  
    ax.plot([bracket_x+0.3, bracket_x+0.3], bracket_y, color=light_grey, lw=2)
    ax.plot([bracket_x+0.3, bracket_x+0.2], [bracket_y[0], bracket_y[0]], color=light_grey, lw=2) # add two lines at the end of the bracket
    ax.plot([bracket_x+0.3, bracket_x+0.2], [bracket_y[1], bracket_y[1]], color=light_grey, lw=2)
    ax.text(bracket_x+0.4, sum(bracket_y)/2, f'{total_sum:.1f} percent growth', fontsize=14, ha='left', va='center', color=dark_grey_3) # Annotate the bracket with the sum

    ## Fig 
    fig_contributors = plt.gcf()
    fig.savefig(f"{VISUALS_PATH}/contributors.png", bbox_inches='tight', dpi=300)

## MARK: Changes
def changes_chart(pct_change_raw, current_q, prior_q):
    
    ## Data prep 
    line_description_replace = {"Services": "Consumer spending, services", 
                            "Goods": "Consumer spending, goods", 
                            "Gross private domestic investment": "Private investment", 
                            "Government consumption expenditures and gross investment": "Government spending and investment"}
    series_codes = ["DGDSRL", "DSERRL", "A006RL", "A020RL", "A021RL", "A822RL"] # Exclude overall consumer spending

    chart_data = (
        pct_change_raw
        .query("(TimePeriod == @current_q | TimePeriod == @prior_q) and SeriesCode in @series_codes")
        .pivot(index=["SeriesCode", "LineDescription", "LineNumber"], columns="TimePeriod", values="DataValue")
        .reset_index()
        .replace({"LineDescription": line_description_replace})
        .drop(columns="LineNumber")
        .set_index("LineDescription")
        .sort_values(by=current_q, ascending=True)
        )

    pal = sns.light_palette(emerald)

    ## Setup
    fig, ax = plt.subplots(figsize=(8,4.5))
    apply_style()
    # plt.rcParams['font.family'] = CUSTOM_FONT_NAME
    fig.set_facecolor(chart_background)
    ax.set_facecolor(chart_background)

    ## Plot
    chart_data.plot(kind="barh", ax=ax, width=0.5, color=[light_grey, pal[-2]])

    ## Labels
    title = f"Growth in GDP components in {current_q[-2:]} {current_q[:4]}"
    ax.set_title(title, fontsize=16, pad=25, x=-0.42, color=dark_grey_3)
    ax.set_ylabel("")

    ## Format
    sns.despine(left=True, bottom=True)
    ax.set_xticks([])
    ax.yaxis.set_tick_params(width=0)
    ax.grid(False)

    handles, labels = ax.get_legend_handles_labels()
    labels = [label[-2:] + " " + label[:4] for label in labels]
    ax.legend(loc='center left', bbox_to_anchor=(-0.438, 1.03), frameon=False, ncol=2, labels=labels, labelcolor=dark_grey_3)

    for ytick in ax.get_yticklabels():
        ytick.set_horizontalalignment('left')
        ytick.set_x(-0.4)
        ytick.set_color(dark_grey_3)

    ## Label the bars
    for i in ax.patches:
        color = i.get_facecolor() if i.get_facecolor() == (0.1828294484126073, 0.4098312873493175, 0.41315284279564213, 1.0) else dark_grey # get_width pulls left or right; get_y pushes up or down
        fontweight = "normal" if color == dark_grey else "bold"
        ax.text(i.get_width(), i.get_y() + 0.05, f'{i.get_width():.1f}%', fontsize=12, color=color, fontweight=fontweight)
    
    ## Save
    fig_growth_comparison = ax.get_figure()
    fig.savefig(f"{VISUALS_PATH}/growth_comparison.png", bbox_inches='tight', dpi=300)


## MARK: Revisions
def draw_row(ax, data, row, name_x, original_x, revised_x, difference_x, num_kws):
    if data[0] in ["Nonresidential investment", "Residential investment", "Federal", "State and local"]:
        name_x = 0.25
    ax.text(name_x, row, data[0], ha='left', va='center', fontsize=12, color=dark_grey_3)
    ax.text(original_x, row, f"{data[1]:.1f}", **num_kws)
    ax.text(revised_x, row, f"{data[2]:.1f}", **num_kws)
    color = "green" if data[3] > 0 else rose_red if data[3] < 0 else "black"
    num_kws["color"] = color
    num_kws["fontweight"] = "bold"
    ax.text(difference_x, row, f"{data[3]:.1f}", **num_kws)


def revisions_chart(no_disposable, release_stage, original):
    ## Data prep
    table_data = (
        no_disposable[["variable", "original", "revised", "difference"]].copy()
        .reset_index(drop=True)
        .rename(columns={"variable": "Component", "original": original, "revised": release_stage, "difference": "Difference"})
        .assign(Component=lambda x: x["Component"].str.replace("government spending", "").str.strip()) # replace the "Federal government spending" row with "Federal" and "State and local government spending" with "State and local"
    )

    ## Setup
    fig, ax = plt.subplots(figsize=(8, 6))
    fig.patch.set_facecolor(chart_background)
    ax.patch.set_facecolor(chart_background)

    gap_between = 1.2
    name_x = 0.1
    original_x = 2.5
    revised_x = original_x + gap_between
    difference_x = revised_x + gap_between

    num_rows, num_cols = table_data.shape
    ax.set_ylim(-1, num_rows + 1)
    ax.set_xlim(0, num_cols + gap_between)
    ax.axis("off")

    ## Plot rows
    for row in range(num_rows):
        number_kws = dict(ha='center', va='center', fontsize=12, color=dark_grey)
        reversed_row = num_rows - 1 - row
        data = table_data.iloc[reversed_row].values
        draw_row(ax, data, row, name_x, original_x, revised_x, difference_x, number_kws)

    ## Plot columns
    col_kws = dict(ha='center', va='center', fontsize=12, color="k", fontweight='bold')
    col_x_cords = [original_x, revised_x, difference_x]
    for col, x_cord in zip(table_data.columns[1:], col_x_cords):
        ax.text(x_cord, num_rows, col, **col_kws)

    ## Gridlines
    for row in range(num_rows):
        ax.plot(
            [0, num_cols + gap_between],
            [row -.5, row - .5],
            ls=':', lw='.5', c='grey'
        )

    y = num_rows - 0.31
    ax.plot([1.9, num_cols + gap_between], [y, y], lw='.5', c='black')

    ## Rectangle
    rect = mpatches.Rectangle(
        (difference_x-0.4, -0.5),  # bottom left starting position (x,y)
        0.9,  # width
        num_rows + .2,  # height
        ec='none',
        fc='grey',
        alpha=.08,
        zorder=-1
    )
    ax.add_patch(rect)

    ## Title
    ax.set_title(f"Revisions to Growth in {release_stage}", 
                loc='center', y = 0.98,
                fontsize=16, fontweight='bold', color=dark_grey_3)

    ## Save
    fig_revisions = plt.gcf()
    fig_revisions.savefig(f"{VISUALS_PATH}/revisions.png", bbox_inches='tight', dpi=300)



## MARK: Main
def generate_charts(pct_change_raw, main_contibutors_df, no_disposable, current_q, prior_q, release_stage, original):
    
    overview_chart(pct_change_raw, current_q)
    
    composition_chart(main_contibutors_df, current_q)
    
    changes_chart(pct_change_raw, current_q, prior_q)
    
    revisions_chart(no_disposable, release_stage, original)

    
