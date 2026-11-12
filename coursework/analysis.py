# DATA70121 Coursework: EDA & Regression
# Analysis of the MavenRail data (Python 3.12, pandas, statsmodels, seaborn)
#
# Run from the folder that contains MavenRail.csv and ToPredict_with_refund.csv:
#     python coursework/analysis.py
# Tables are printed to the console; figures are saved in coursework/figures/.

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.formula.api as smf
from scipy import stats

DATA_DIR = Path(__file__).resolve().parent.parent
FIG_DIR = Path(__file__).resolve().parent / "figures"
FIG_DIR.mkdir(exist_ok=True)

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 30)

# Colours used for the two ticket classes in every figure
CLASS_ORDER = ["Standard", "First Class"]
CLASS_COLOURS = {"Standard": "#2a78d6", "First Class": "#eb6834"}


# ---------------------------------------------------------------------------
# 0. Read and clean the data
# ---------------------------------------------------------------------------

def read_rail(path, date_format):
    """Read one of the rail files and tidy the column types."""
    # keep_default_na=False stops pandas turning the railcard label "None"
    # into a missing value; genuinely blank cells are still read as NaN.
    df = pd.read_csv(path, keep_default_na=False, na_values=[""])

    # Shorter column names without dots, so they can be used in model formulas
    df.columns = [c.replace(".", "") for c in df.columns]

    for col in ["Departure", "ScheduledArrival", "ActualArrival"]:
        df[col] = pd.to_datetime(df[col], format=date_format)

    # Response as 0/1
    df["Refund"] = (df["RefundRequest"] == "Yes").astype(int)
    return df


rail = read_rail(DATA_DIR / "MavenRail.csv", "%Y-%m-%d %H:%M")
to_predict = read_rail(DATA_DIR / "ToPredict_with_refund.csv", "%d/%m/%Y %H:%M")


# ---------------------------------------------------------------------------
# 1. Description of the data
# ---------------------------------------------------------------------------

print("\n===== 1. DESCRIPTION OF THE DATA =====")
print("Rows and columns:", rail.shape)
print("\nColumn types:\n", rail.dtypes)
print("\nMissing values per column:\n", rail.isna().sum())
print("\nFirst departure:", rail["Departure"].min(), "| last departure:", rail["Departure"].max())
print("Exact duplicate rows:", rail.duplicated().sum())

categorical = ["PaymentMethod", "Railcard", "TicketClass", "TicketType",
               "JourneyStatus", "ReasonforDelay", "RefundRequest"]
for col in categorical:
    counts = rail[col].value_counts(dropna=False)
    print(f"\n{col}:")
    print(pd.DataFrame({"n": counts, "%": (100 * counts / len(rail)).round(1)}))

print("\nDeparture stations:", rail["DepartureStation"].nunique(),
      "| arrival stations:", rail["ArrivalStation"].nunique(),
      "| routes:", rail.groupby(["DepartureStation", "ArrivalStation"]).ngroups)
print("\nPrice (GBP):\n", rail["Price"].describe().round(2))

# Arrival delay in minutes (only defined when the train actually arrived)
rail["DelayMinutes"] = (rail["ActualArrival"] - rail["ScheduledArrival"]).dt.total_seconds() / 60
print("\nDelay in minutes by journey status:\n",
      rail.groupby("JourneyStatus")["DelayMinutes"].describe().round(1))

print("\nRefund requests by journey status:\n",
      pd.crosstab(rail["JourneyStatus"], rail["RefundRequest"], margins=True))


# ---------------------------------------------------------------------------
# 2. EDA: ticket price in Standard and First Class
# ---------------------------------------------------------------------------

print("\n===== 2. PRICE BY TICKET CLASS =====")


def price_summary(x):
    """Summary statistics for one group of prices."""
    q1, q3 = x.quantile([0.25, 0.75])
    iqr = q3 - q1
    outliers = ((x < q1 - 1.5 * iqr) | (x > q3 + 1.5 * iqr)).sum()
    return pd.Series({
        "n": len(x),
        "Mean": x.mean(),
        "SD": x.std(),
        "Min": x.min(),
        "Q1": q1,
        "Median": x.median(),
        "Q3": q3,
        "Max": x.max(),
        "IQR": iqr,
        "Skewness": stats.skew(x),
        "Outliers (1.5 IQR rule)": outliers,
        "Outliers (%)": 100 * outliers / len(x),
    })


summary = rail.groupby("TicketClass")["Price"].apply(price_summary).unstack().loc[CLASS_ORDER]
print(summary.round(2).T)

# Supporting test: are prices in the two classes drawn from the same distribution?
standard = rail.loc[rail["TicketClass"] == "Standard", "Price"]
first = rail.loc[rail["TicketClass"] == "First Class", "Price"]
u_stat, u_p = stats.mannwhitneyu(first, standard, alternative="two-sided")
print(f"\nMann-Whitney U = {u_stat:.0f}, p = {u_p:.3g}")
print(f"P(First Class price > Standard price) = {u_stat / (len(first) * len(standard)):.3f}")

# Median price by class within each ticket type (is the gap there for every type?)
print("\nMedian price by ticket type and class:\n",
      rail.pivot_table(index="TicketType", columns="TicketClass", values="Price",
                       aggfunc="median")[CLASS_ORDER])

sns.set_theme(style="whitegrid", context="paper", font_scale=1.05)
plt.rcParams.update({"figure.dpi": 110, "savefig.dpi": 300, "axes.titleweight": "bold",
                     "axes.titlelocation": "left", "grid.color": "#e6e6e3",
                     "axes.edgecolor": "#b9b8b3"})

price_ticks = [1, 2, 5, 10, 20, 50, 100, 250]

# --- Figure 1: boxplots (log scale because prices are strongly right-skewed) ---
fig, ax = plt.subplots(figsize=(7, 2.6))
sns.boxplot(data=rail, x="Price", y="TicketClass", order=CLASS_ORDER, hue="TicketClass",
            palette=CLASS_COLOURS, legend=False, width=0.55, linewidth=1,
            flierprops={"marker": "o", "markersize": 3, "alpha": 0.35}, ax=ax)
means = rail.groupby("TicketClass")["Price"].mean().loc[CLASS_ORDER]
ax.scatter(means.values, range(len(CLASS_ORDER)), marker="D", s=30, color="white",
           edgecolor="black", zorder=5, label="Mean")
ax.set_xscale("log")
ax.set_xticks(price_ticks, [f"£{t}" for t in price_ticks])
ax.set_xlabel("Ticket price (log scale)")
ax.set_ylabel("")
ax.legend(loc="lower right", frameon=False)
fig.tight_layout()
fig.savefig(FIG_DIR / "fig1_boxplot.png")
plt.close(fig)

# --- Figure 2: histograms with common bins, scaled to density ---
# Density (not counts) is used because Standard has about nine times as many tickets.
bins = np.arange(0, 275, 5)
fig, axes = plt.subplots(2, 1, figsize=(7, 4.2), sharex=True, sharey=True)
for ax, cls in zip(axes, CLASS_ORDER):
    prices = rail.loc[rail["TicketClass"] == cls, "Price"]
    ax.hist(prices, bins=bins, density=True, color=CLASS_COLOURS[cls],
            edgecolor="white", linewidth=0.4)
    ax.axvline(prices.median(), color="black", linestyle="--", linewidth=1,
               label=f"Median £{prices.median():.0f}")
    ax.axvline(prices.mean(), color="black", linestyle=":", linewidth=1.2,
               label=f"Mean £{prices.mean():.1f}")
    ax.set_title(f"{cls} (n = {len(prices):,})")
    ax.set_ylabel("Density")
    ax.legend(frameon=False)
axes[-1].set_xlabel("Ticket price (£, bins of £5)")
fig.tight_layout()
fig.savefig(FIG_DIR / "fig2_histograms.png")
plt.close(fig)

# --- Figure 3: kernel density estimates of log10(price) ---
# Estimating the density on the log scale avoids the KDE leaking below £0
# and shows the several modes hidden in the first histogram bins.
fig, ax = plt.subplots(figsize=(7, 3))
for cls in CLASS_ORDER:
    prices = rail.loc[rail["TicketClass"] == cls, "Price"]
    sns.kdeplot(x=np.log10(prices), ax=ax, color=CLASS_COLOURS[cls], fill=True,
                alpha=0.25, linewidth=2, label=cls)
ax.set_xticks(np.log10(price_ticks), [f"£{t}" for t in price_ticks])
ax.set_xlabel("Ticket price (log scale)")
ax.set_ylabel("Density of log10(price)")
ax.legend(frameon=False)
fig.tight_layout()
fig.savefig(FIG_DIR / "fig3_kde.png")
plt.close(fig)


# ---------------------------------------------------------------------------
# 3. Refund requests and MediumPrice (journeys that were not on time)
# ---------------------------------------------------------------------------

print("\n===== 3. LOGISTIC REGRESSION ON MediumPrice =====")

not_on_time = rail[rail["JourneyStatus"] != "On Time"].copy()
not_on_time["MediumPrice"] = ((not_on_time["Price"] > 10) & (not_on_time["Price"] <= 30)).astype(int)
print("Journeys not on time:", len(not_on_time))
print("\nMediumPrice by refund request:\n",
      pd.crosstab(not_on_time["MediumPrice"], not_on_time["RefundRequest"], margins=True))

# The response is binary (refund requested or not), so a logistic regression is used:
#     log( p / (1 - p) ) = b0 + b1 * MediumPrice
model_q3 = smf.logit("Refund ~ MediumPrice", data=not_on_time).fit(disp=False)
print(model_q3.summary())

b0, b1 = model_q3.params["Intercept"], model_q3.params["MediumPrice"]
print(f"\nb0 = {b0:.4f}, b1 = {b1:.4f}, odds ratio exp(b1) = {np.exp(b1):.3f}")
print("95% CI for the odds ratio:", np.exp(model_q3.conf_int().loc["MediumPrice"]).round(3).tolist())


def inverse_logit(eta):
    return 1 / (1 + np.exp(-eta))


# A GBP 5 ticket is outside (10, 30], so MediumPrice = 0; a GBP 25 ticket is inside, so MediumPrice = 1
for price in [5, 25]:
    medium = int(10 < price <= 30)
    eta = b0 + b1 * medium
    print(f"Price GBP {price}: MediumPrice = {medium}, linear predictor = {b0:.4f} + {b1:.4f} x {medium} "
          f"= {eta:.4f}, P(refund) = 1 / (1 + exp({-eta:.4f})) = {inverse_logit(eta):.4f}")

# Check with predict(), with 95% confidence intervals
new_q3 = pd.DataFrame({"Price": [5, 25], "MediumPrice": [0, 1]})
pred_q3 = model_q3.get_prediction(new_q3).summary_frame()
print("\n", pd.concat([new_q3, pred_q3[["predicted", "ci_lower", "ci_upper"]]], axis=1).round(4))
