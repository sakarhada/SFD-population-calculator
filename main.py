import pandas as pd

# ---------------------------------------------------------------------------
# 1. Load & rename columns
# ---------------------------------------------------------------------------
data = pd.read_csv("/content/sample_data/househhold_data_SFD.csv", encoding="latin1")

COLUMN_CODE = {
    "Q1 Are toilets available and used or is open defecation practiced?": "Q1",
    "Q1.1 Where does open defecation take place?": "Q1_1",
    "Q1.2 Is the toilet or latrine failed, damaged, collapsed or flooded?": "Q1_2",
    "Q1.2.1 Where does the toilet discharge to? (what type of containment technology, if any)": "Q1_2_1",
    "Q1.2.1.1 If no container or septic tank, where does the outlet or overflow discharge to?": "Q1_2_1_1",
    "Q1.2.1.2 What is the containment technology connected to?": "Q1_2_1_2",
    "Q2.1 What is the rock type in the unsaturated zone": "Q2_1",
    "Q2.2 What is the depth to the groundwater table?": "Q2_2",
    "Q2.3 Lateral distance between sanitation facility and groundwater source": "Q2_3",
    "Q2.4 Is the sanitation facility located uphill of groundwater source?": "Q2_4",
    "Q2.5 Source of drinking water?": "Q2_5",
    "Q2.6 What is the water production technology used?": "Q2_6",
}
data.rename(columns=COLUMN_CODE, inplace=True)


# ---------------------------------------------------------------------------
# 2. Bucket the numeric distance fields into categories (NaN-safe)
# ---------------------------------------------------------------------------
def categorize_V_distance(depth):
    """Vertical distance to groundwater source."""
    if pd.isna(depth):
        return pd.NA
    if depth < 5:
        return "Less than 5m"
    elif depth <= 10:
        return "5-10m"
    return "More than 10m"


def categorize_H_distance(distance):
    """Horizontal (lateral) distance to groundwater source."""
    if pd.isna(distance):
        return pd.NA
    return "Less than 10 meter" if distance < 10 else "More than or equal to 10m"


data["Q2_2"] = data["Q2_2"].apply(categorize_V_distance)
data["Q2_3"] = data["Q2_3"].apply(categorize_H_distance)


# ---------------------------------------------------------------------------
# 3. Map text responses to numeric codes
# ---------------------------------------------------------------------------
Q1_code = {"No toilet (Open defecation)": 1, "Toilet available": 2}
Q1_1_code = {"to water body": 1, "to open ground": 2, "dont know where": 3}
Q1_2_code = {
    "Toilet is functioning correctly": 1,
    "Toilet is failed, damaged, collapsed or flooded": 2,
    "Containment is failed, damaged, collapsed, or flooded": 3,
}
Q1_2_1_code = {
    "No onsite container": 1,
    "Septic tank": 2,
    "Fully lined tank": 3,
    "Lined tank with impermeable walls and open bottom": 4,
    "Lined pit with semi-permeable walls and open bottom": 5,
    "Unlined pit": 6,
    "Pit (all types), never emptied but abandoned when full and covered with soil": 7,
    "Pit (all types), never emptied, abandoned when full but not adequately covered with soil": 8,
}
_OUTLET_DESTINATIONS = {
    "to centralized combined sewer": 1,
    "to centralized foul/separate sewer": 2,
    "to decentralized combined sewer": 3,
    "to decentralized foul/separate sewer": 4,
    "to soakpit": 5,
    "to open drain or storm sewer": 6,
    "to water body": 7,
    "to open ground": 8,
    "to don't know where": 9,
}
Q1_2_1_1_code = dict(_OUTLET_DESTINATIONS)
Q1_2_1_2_code = {**_OUTLET_DESTINATIONS, "no outlet or overflow": 10}
Q2_1_code = {
    "fine sand, silt and clay": 1,
    "weathered basement": 2,
    "medium sand": 3,
    "Course sand and gravel": 4,
    "sandstones/limestones fractured rock": 5,
}
Q2_2_code = {"Less than 5m": 1, "5-10m": 2, "More than 10m": 3}
Q2_3_code = {"Less than 10 meter": 1, "More than or equal to 10m": 2}
Q2_4_code = {"Yes": 1, "No": 2}
Q2_5_code = {"Groundwater": 1, "Other source": 2}
Q2_6_code = {
    "Protected boreholes, protected dug wells or protected spring where adequate sanitary measures are in place": 1,
    "Unprotected boreholes, dug wells, or springs": 2,
    "No groundwater sources used": 3,
}

data["Q1"] = data["Q1"].map(Q1_code)
data["Q1_1"] = data["Q1_1"].map(Q1_1_code)
data["Q1_2"] = data["Q1_2"].map(Q1_2_code)
data["Q1_2_1"] = data["Q1_2_1"].map(Q1_2_1_code)
data["Q1_2_1_1"] = data["Q1_2_1_1"].map(Q1_2_1_1_code)
data["Q1_2_1_2"] = data["Q1_2_1_2"].map(Q1_2_1_2_code)
data["Q2_1"] = data["Q2_1"].map(Q2_1_code)
data["Q2_2"] = data["Q2_2"].map(Q2_2_code)
data["Q2_3"] = data["Q2_3"].map(Q2_3_code)
data["Q2_4"] = data["Q2_4"].map(Q2_4_code)
data["Q2_5"] = data["Q2_5"].map(Q2_5_code)
data["Q2_6"] = data["Q2_6"].map(Q2_6_code)


# ---------------------------------------------------------------------------
# 4. Groundwater risk assessment
# ---------------------------------------------------------------------------
# Aquifer vulnerability combos considered "low risk" (rock type, depth-to-GW code)
_LOW_RISK_AQUIFER_COMBOS = {(1, 2), (1, 3), (2, 3), (3, 3)}


def gw1_for_row(row):
    """GW1: aquifer vulnerability for a single household, 'LR' or 'SR'."""
    return "LR" if (row["Q2_1"], row["Q2_2"]) in _LOW_RISK_AQUIFER_COMBOS else "SR"


def compute_dataset_risk_stats(df):
    """
    GW2 (lateral/uphill separation) and the % of drinking water sourced from
    groundwater are dataset-wide statistics, not per-row values, so they only
    need to be computed once for the whole survey.
    """
    def ratio(count_a, count_b):
        total = count_a + count_b
        return count_a / total if total else 0.0

    lateral_ok = ratio((df["Q2_3"] == 1).sum(), (df["Q2_3"] == 2).sum()) > 0.25
    uphill_ok = ratio((df["Q2_4"] == 1).sum(), (df["Q2_4"] == 2).sum()) > 0.25
    GW2 = "LR" if (lateral_ok and uphill_ok) else "SR"

    pct_groundwater_drinking = ratio((df["Q2_5"] == 1).sum(), (df["Q2_5"] == 2).sum())

    return GW2, pct_groundwater_drinking


GW2, PCT_GROUNDWATER_DRINKING = compute_dataset_risk_stats(data)


def is_significant_gw_risk(GW1, GW2, pct_groundwater_drinking, Q2_6):
    """
    True -> "significant risk" (T2...), False -> "low risk" (T1...).
    Equivalent to the original 5-term OR condition:
      Q2_6 == 1: significant iff GW2 == 'SR'  (GW1 irrelevant)
      Q2_6 == 2: significant iff GW1 == 'SR' or GW2 == 'SR'
      any other Q2_6 value: never significant
    """
    if pct_groundwater_drinking <= 0.25:
        return False
    if Q2_6 == 1:
        return GW2 == "SR"
    if Q2_6 == 2:
        return GW1 == "SR" or GW2 == "SR"
    return False


def escalate_if_significant(base_label, row):
    """Upgrade a 'T1...' label to 'T2...' if groundwater risk is significant."""
    GW1 = gw1_for_row(row)
    if is_significant_gw_risk(GW1, GW2, PCT_GROUNDWATER_DRINKING, row["Q2_6"]):
        return base_label.replace("T1", "T2", 1)
    return base_label


# ---------------------------------------------------------------------------
# 5. SFD grid category assignment
# ---------------------------------------------------------------------------
# For a functioning toilet (Q1_2 == 1), which outlet column to read and which
# outlet codes trigger a groundwater-risk escalation check, keyed by
# containment technology (Q1_2_1).
_OUTLET_CONFIG = {
    1: ("Q1_2_1_1", {5}),              # No onsite container
    2: ("Q1_2_1_1", {5}),              # Septic tank
    3: ("Q1_2_1_2", {5}),              # Fully lined tank
    4: ("Q1_2_1_2", {1, 2, 3, 4, 5, 10}),  # Lined tank, impermeable walls, open bottom
}
_OPEN_DEFECATION_LABELS = {1: "T1B11C7", 2: "T1B11C8", 3: "T1B11C9"}


def categorize_SFD(row):
    Q1, Q1_2, Q1_2_1 = row["Q1"], row["Q1_2"], row["Q1_2_1"]

    # Open defecation
    if Q1 == 1:
        return _OPEN_DEFECATION_LABELS.get(row["Q1_1"], 0)
    if Q1 != 2:
        return 0

    # Toilet exists but is failed/damaged, or containment is failed/damaged:
    # outcome depends only on where it discharges to, no groundwater check.
    if Q1_2 == 2:
        c = row["Q1_2_1_2"]
        return f"T1B9C{int(c)}" if pd.notna(c) else 0
    if Q1_2 == 3:
        c = row["Q1_2_1_2"]
        return f"T1B10C{int(c)}" if pd.notna(c) else 0
    if Q1_2 != 1:
        return 0

    # Toilet functioning correctly: branch on containment technology.
    if Q1_2_1 in _OUTLET_CONFIG:
        outlet_col, escalate_codes = _OUTLET_CONFIG[Q1_2_1]
        c = row[outlet_col]
        if pd.isna(c):
            return 0
        label = f"T1A{int(Q1_2_1)}C{int(c)}"
        return escalate_if_significant(label, row) if c in escalate_codes else label

    # Lined pit (semi-permeable) / unlined pit / abandoned-and-covered pit:
    # only "no outlet or overflow" (code 10) is a valid state, and it always
    # triggers a groundwater-risk check.
    if Q1_2_1 in (5, 6, 7):
        c = row["Q1_2_1_2"]
        if c != 10:
            return 0
        return escalate_if_significant(f"T1A{int(Q1_2_1)}C10", row)

    # Abandoned pit, not adequately covered: fixed category, no GW check.
    if Q1_2_1 == 8:
        return "T1B8C10" if row["Q1_2_1_2"] == 10 else 0

    return 0


data["SFD_Grid_Category"] = data.apply(categorize_SFD, axis=1)

print(data.head())
print(data["SFD_Grid_Category"].value_counts())
