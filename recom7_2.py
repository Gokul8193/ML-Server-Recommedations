import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder, MinMaxScaler
import random
import os
import json
import ast

# -------------------------------------------
# 1. Load and preprocess dataset
# -------------------------------------------
input_dir = os.path.join(os.path.dirname(__file__), "input_params")
df = pd.read_csv(os.path.join(input_dir, "merged_df12.csv"), low_memory=False)
df = df.sample(frac=0.5, random_state=42).reset_index(drop=True)
print("Number of NaN values per column:")
pd.set_option('display.max_rows', None)
print(df.isnull().sum())
df['ad_group_id'] = df.groupby('campaign_id')['ad_group_id'].transform(
    lambda x: x.fillna(x.mode() if not x.mode().empty else 0))
df['Date'] = df['Date'].ffill().bfill()
num_impute_cols = ['impressions', 'clicks', 'cost_usd', 'ctr', 'average_cpc_usd']
for col in num_impute_cols:
    df[col] = df.groupby(['campaign_id', 'ad_group_id', 'Date'])[col].transform(
        lambda x: x.fillna(x.mean() if not x.isnull().all() else 0))
df.loc[(df['impressions'] == 0) & (df['clicks'] == 0) & (df['ctr'] == 0) & df['conversion_rate_Interactions'].isna(),
       'conversion_rate_Interactions'] = 0
df.loc[(df['impressions'] == 0) & (df['clicks'] == 0) & (df['ctr'] == 0) & df['conversion_rate_Conversions'].isna(),
       'conversion_rate_Conversions'] = 0
df['conversion_rate_Interactions'] = df['conversion_rate_Interactions'].fillna(df['conversion_rate_Interactions'].mean())
df['conversion_rate_Conversions'] = df['conversion_rate_Conversions'].fillna(df['conversion_rate_Conversions'].mean())
df['conversion_rate_Conversion_rate_(%)'] = np.where(
    df['conversion_rate_Interactions'] == 0,
    0,
    round(100 * df['conversion_rate_Conversions'] / df['conversion_rate_Interactions'], 2)
)
df['Keyword_Quality_Keyword'] = df['Keyword_Quality_Keyword'].ffill().bfill()
grouped_kw = df.groupby('Keyword_Quality_Keyword')
df['Keyword_Quality_Estimated_Quality_Score'] = df['Keyword_Quality_Estimated_Quality_Score'].fillna(
    grouped_kw['Keyword_Quality_Estimated_Quality_Score'].transform(lambda x: x.fillna(x.mean()))
)
df['Keyword_Quality_KW_types'] = df['Keyword_Quality_KW_types'].fillna(
    grouped_kw['Keyword_Quality_KW_types'].transform(lambda x: x.mode() if not x.mode().empty else None)
)
for col in df.columns[df.isnull().any()]:
    non_null_vals = df[col].dropna()
    n_missing = df[col].isnull().sum()
    if n_missing > 0 and len(non_null_vals) > 0:
        df.loc[df[col].isnull(), col] = random.choices(non_null_vals.tolist(), k=n_missing)
drop_cols = ['bidding_strategy_budget_amount_consumed', 'bidding_strategy_target_roas', 'bidding_strategy_target_cpa_micros']
df.drop(columns=[c for c in drop_cols if c in df.columns], inplace=True)
df.drop_duplicates(inplace=True)

# ----------------------------
# Filter only campaign_id = "22988974238"
# ----------------------------
df['campaign_id'] = df['campaign_id'].astype(str)
df = df[df['campaign_id'] == '22988974238'].reset_index(drop=True)

# -------------------------------------------
# 2. Encode categorical columns
# -------------------------------------------
categorical_cols = [
    'Keyword_Quality_Keyword', 'Keyword_Quality_KW_types', 'Device_performance_Device',
    'Keyword_performance_Keyword_Text', 'Keyword_performance_Keyword_Match_Type',
    'bid_Adjustments_device_type', 'bid_Adjustments_device_type_name', 'day_of_week',
    'keywords_meta_keyword_text', 'keywords_meta_match_type', 'search_term_search_term',
    'bidding_strategy_bidding_strategy_type', 'Negative_keywords', 'geographic_report_geo_target_constant'
]
df_cat = df[categorical_cols].copy()
df_num = df.drop(columns=categorical_cols)
high_card_cols = [
    'Keyword_Quality_Keyword', 'Keyword_performance_Keyword_Text',
    'keywords_meta_keyword_text', 'search_term_search_term', 'Negative_keywords',
    'geographic_report_geo_target_constant'
]
low_card_cols = [c for c in categorical_cols if c not in high_card_cols]
df_enc = df_cat.copy()
label_encoders = {}
one_hot_groups = {}
for col in high_card_cols:
    if col in df_enc:
        le = LabelEncoder()
        df_enc[f"{col}_encoded"] = le.fit_transform(df_enc[col].astype(str))
        label_encoders[col] = le
        df_enc.drop(columns=[col], inplace=True)
if low_card_cols:
    df_enc = pd.get_dummies(df_enc, columns=low_card_cols, prefix=low_card_cols)
    for col in low_card_cols:
        one_hot_groups[col] = [c for c in df_enc.columns if c.startswith(f"{col}_")]

# -------------------------------------------
# 3. Handle dates and campaigns
# -------------------------------------------
df_date_camp = df_num[['Date', 'campaign_id', 'ad_group_id']].copy()
df_num = df_num.drop(columns=['Date', 'campaign_id', 'ad_group_id'])
for col in ['campaign_id', 'ad_group_id']:
    le = LabelEncoder()
    df_date_camp[col] = le.fit_transform(df_date_camp[col].astype(str))
    label_encoders[col] = le
df_date_camp['Date'] = pd.to_datetime(df_date_camp['Date'])
df_date_camp['Date_Year'] = df_date_camp['Date'].dt.year
df_date_camp['Date_Month'] = df_date_camp['Date'].dt.month
df_date_camp['Date_Day'] = df_date_camp['Date'].dt.day
df_date_camp.drop(columns=['Date'], inplace=True)

# -------------------------------------------
# 4. Scale relevant columns
# -------------------------------------------
scale_rename = [
    'ad_performance_Avg._CPC', 'ad_performance_Cost_per_Acquisition', 'Device_performance_Cost_per_Conversion',
    'Keyword_performance_average_cpc', 'Keyword_performance_cost_per_conversion',
    'Keyword_performance_estimated_first_position_cpc', 'geographic_report_cost_per_conversion'
]
for col in scale_rename:
    if col in df_num:
        df_num[f"{col}_usd"] = df_num[col] / 1_000_000
        df_num.drop(columns=[col], inplace=True)

# -------------------------------------------
# 5. Final dataset assembly
# -------------------------------------------
final_df = pd.concat([
    df_num.reset_index(drop=True),
    df_date_camp.reset_index(drop=True),
    df_enc.reset_index(drop=True)
], axis=1)
final_df.drop_duplicates(inplace=True)
final_df.reset_index(drop=True, inplace=True)

# -------------------------------------------
# 6. Log transform skewed numeric columns
# -------------------------------------------
skew_cols = ['impressions', 'clicks', 'cost_usd', 'ctr', 'average_cpc_usd','conversions_Master','cost_per_conversion_usd']
for c in skew_cols:
    if c in final_df:
        final_df[c] = np.log1p(final_df[c].fillna(0) + 1e-9)

# -------------------------------------------
# 7. Convert bools to int
# -------------------------------------------
for col in final_df.select_dtypes(include='bool').columns:
    final_df[col] = final_df[col].astype(int)

# -------------------------------------------
# 8. Define targets and features
# -------------------------------------------
target_cols = ['impressions', 'clicks', 'cost_usd', 'ctr', 'average_cpc_usd', 'ad_performance_Conversions']
for c in target_cols:
    if c not in final_df.columns:
        raise KeyError(f"Missing target column: {c}")
X = final_df.drop(columns=target_cols)
y = final_df[target_cols]
feature_cols = list(X.columns)

# -------------------------------------------
# 9. Load models and ensemble weights
# -------------------------------------------
rf_model = joblib.load('artifacts3/models/rf_multi_model.pkl')
xgb_model = joblib.load('artifacts3/models/xgb_multi_model.pkl')
ensemble_weights = joblib.load('artifacts3/models/ensemble_weights.pkl')
LOG_TRANSFORMED = True

# -------------------------------------------
# 10. Helper encode and align functions
# -------------------------------------------
def get_features(model):
    return list(model.feature_names_in_)
def align_features(df, model):
    expected = get_features(model)
    df = df.copy()
    for col in df.columns:
        if col not in expected:
            df.drop(columns=[col], inplace=True)
    for col in expected:
        if col not in df.columns:
            df[col] = 0
    return df[expected]
def encode_inputs(df_input):
    parts = []
    temp = df_input.copy()
    for col, le in label_encoders.items():
        if col in temp.columns:
            temp[col] = temp[col].astype(str)
            known = set(le.classes_)
            temp[col] = temp[col].apply(lambda x: x if x in known else 'unknown')
            if 'unknown' not in le.classes_:
                le.classes_ = np.append(le.classes_, 'unknown')
            enc = pd.Series(le.transform(temp[col]), name=f"{col}_encoded")
            parts.append(enc)
            temp.drop(columns=[col], inplace=True)
    low_cat_cols = list(one_hot_groups.keys())
    present_low = [c for c in low_cat_cols if c in temp.columns]
    if len(present_low) > 0:
        oh_df = pd.get_dummies(temp[present_low], prefix=present_low)
        for col in present_low:
            for exp_col in one_hot_groups[col]:
                if exp_col not in oh_df.columns:
                    oh_df[exp_col] = 0
        temp.drop(columns=present_low, inplace=True)
        parts.append(oh_df[sorted(oh_df.columns)].reset_index(drop=True))
    for col in temp.columns:
        if temp[col].dtype == object:
            fallback = LabelEncoder()
            temp[col] = fallback.fit_transform(temp[col].astype(str))
    parts.append(temp.reset_index(drop=True))
    encoded = pd.concat(parts, axis=1)
    if len(encoded.select_dtypes(include=['object']).columns) > 0:
        raise ValueError("Non-numeric columns remain in encoded features")
    return encoded
def decode_df(df):
    for col, le in label_encoders.items():
        enc_col = f"{col}_encoded"
        if enc_col in df.columns:
            try:
                df[col] = le.inverse_transform(df[enc_col].astype(int))
                df.drop(columns=[enc_col], inplace=True)
            except Exception:
                pass
        elif col in df.columns and df[col].dtype in (int, float):
            try:
                df[col] = le.inverse_transform(df[col].astype(int))
            except Exception:
                pass
    for col, group in one_hot_groups.items():
        def get_val(row):
            for c in group:
                if row.get(c, 0) == 1:
                    return c[len(col)+1:]
            return None
        if all(c in df.columns for c in group):
            df[col] = df.apply(get_val, axis=1)
            df.drop(columns=group, inplace=True)
    return df
def track_predictions(df_input):
    encoded = encode_inputs(df_input)
    rf_in = align_features(encoded, rf_model)
    xgb_in = align_features(encoded, xgb_model)
    rf_pred = rf_model.predict(rf_in)
    xgb_pred = xgb_model.predict(xgb_in)
    if LOG_TRANSFORMED:
        rf_pred = np.expm1(rf_pred)
        xgb_pred = np.expm1(xgb_pred)
    preds = np.zeros_like(rf_pred)
    for i, target in enumerate(ensemble_weights.keys()):
        w_rf = ensemble_weights[target]
        w_xgb = 1 - w_rf
        preds[:, i] = w_rf * rf_pred[:, i] + w_xgb * xgb_pred[:, i]
    pred_df = pd.DataFrame(preds, columns=ensemble_weights.keys())
    combined = pd.concat([df_input.reset_index(drop=True), pred_df.reset_index(drop=True)], axis=1)
    return pred_df, combined

# -------------------------------------------
# 12. Generate values map for manual input generation
# -------------------------------------------
values_map = {}
for f in feature_cols:
    if f in df.columns and not pd.api.types.is_numeric_dtype(df[f]):
        values_map[f] = df[f].dropna().unique().tolist()
    elif f in df.columns:
        values_map[f] = df[f].dropna().to_numpy()
    else:
        values_map[f] = [0, 1, 2]

# -------------------------------------------
# Add explicit values (20 parameters with schedule inputs)
# -------------------------------------------
explicit_values = {
    'Device_performance_Device': ['DESKTOP', 'MOBILE', 'TABLET', 'SMART_TV'],
    'Keyword_Quality_KW_types': ['EXACT', 'PHRASE', 'BROAD', 'NEGATIVE'],
    'bidding_strategy_bidding_strategy_type': ['MANUAL_CPC', 'TARGET_CPA', 'MAXIMIZE_CONVERSIONS', 'TARGET_ROAS'],
    'day_of_week': ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY', 'SUNDAY'],
    'Negative_keywords': ['NONE', 'COMPETITOR', 'BRAND_PROTECTION', 'LOCATION_BLOCK'],
    'Keyword_Quality_Keyword': ['best shoes', 'running shoes', 'discount shoes', 'sport shoes', 'winter boots'],
    'Device_performance_Cost_per_Conversion_usd': [0.5, 1.0, 1.5, 2.0],
    'search_term_search_term': ['cheap shoes', 'shoe store near me', 'online shoe deals', 'sports footwear'],
    'bid_Adjustments_device_type': ['DESKTOP', 'MOBILE', 'TABLET'],
    'Keyword_performance_Keyword_Text': ['buy shoes', 'shoe sale', 'sneaker deals'],
    'Keyword_performance_Keyword_Match_Type': ['EXACT', 'BROAD', 'PHRASE'],
    'keywords_meta_keyword_text': ['athletic shoes', 'formal shoes', 'kids shoes'],
    'keywords_meta_match_type': ['PHRASE', 'EXACT', 'BROAD'],
    'geographic_report_geo_target_constant': ['United States', 'Canada', 'United Kingdom', 'Germany'],
    'Date_Year': [2025, 2026],
    'Date_Month': [1, 4, 7, 10, 12],
    'Date_Day': [1, 7, 15, 23, 31],
    'Keyword_Quality_Estimated_Quality_Score': [2, 3, 4, 5, 6, 7, 8, 9, 10],
    'Device_performance_Avg_CPC_usd': [0.50, 0.75, 1.00, 1.25, 1.50],
    'ad_schedule_start_hour': [0, 6, 9, 12, 15, 18, 21],
    'ad_schedule_end_hour': [3, 9, 12, 15, 18, 21, 24]
}
for key, vals in explicit_values.items():
    values_map[key] = vals

# -------------------------------------------
# 13. Generate manual input variations
# -------------------------------------------
def generate_manual_variations(features, n=100):
    vals = []
    for _ in range(n):
        d = {}
        for f in features:
            if f in values_map:
                if isinstance(values_map[f], np.ndarray):
                    d[f] = np.random.choice(values_map[f])
                else:
                    d[f] = random.choice(values_map[f])
            else:
                d[f] = 1
        vals.append(d)
    df_var = pd.DataFrame(vals)
    missing_cols = set(features) - set(df_var.columns)
    for col in missing_cols:
        df_var[col] = 0
    df_var = df_var[features]
    return df_var
n_list = [
    10,20,30,40,50,60,70,80,90,100,150,200,250,
    300,350,400,450,500,550,600,650,700,750,800,
    850,900,950,1000,1050,1100,1150,1200,1250,1300,
    1350,1450,1400,1500,1550,1600,1650,1700,1750,
    1800,1850,1900,1950,2000,2050,2100,2150,2200,
    2250,2300,2350,2400,2450,2500,2550,2600,2650,
    2700,2750,2800,2850,2900,2950,3000,3050,3100,
    3150,3200,3250,3300,3350,3400,3450,3500,3550,
    3600,3650,3700,3750,3800,3850,2900,2950,4000,
    4050,4100,4150,4200,4250,4300,4350,4400,4450,
    4500,4550,4600,4650,4700,4750,4800,4850,4900,
    4950,5000
]
all_full_runs = []
for n in n_list:
    manual_input_df = generate_manual_variations(feature_cols, n=n)
    missing_cols = set(feature_cols) - set(manual_input_df.columns)
    if missing_cols:
        continue
    preds, full_history = track_predictions(manual_input_df)
    decoded_run_df = decode_df(full_history.copy())
    
    # Remove duplicate columns, keeping only the first occurrence
    if decoded_run_df.columns.duplicated().any():
        decoded_run_df = decoded_run_df.loc[:, ~decoded_run_df.columns.duplicated(keep='first')]
    
    decoded_run_df['n'] = n
    all_full_runs.append(decoded_run_df)

# Ensure all DataFrames have the same columns before concatenating
if all_full_runs:
    # Get all unique columns across all DataFrames
    all_cols = set()
    for df in all_full_runs:
        all_cols.update(df.columns)
    all_cols = sorted(list(all_cols))
    
    # Reindex all DataFrames to have the same columns
    for i, df in enumerate(all_full_runs):
        all_full_runs[i] = df.reindex(columns=all_cols)

final_full_decoded_df = pd.concat(all_full_runs, ignore_index=True)
def robust_decode_negative_keywords(value, le_neg):
    if isinstance(value, (int, float, np.integer, np.floating)):
        try:
            return le_neg.inverse_transform([int(value)])
        except Exception:
            return value
    if isinstance(value, str):
        try:
            parsed = ast.literal_eval(value)
            if isinstance(parsed, list):
                return parsed
            else:
                return value
        except Exception:
            return value
    return value
if 'Negative_keywords_encoded' in final_full_decoded_df.columns:
    le_neg = label_encoders.get('Negative_keywords')
    if le_neg is not None:
        final_full_decoded_df['Negative_keywords_encoded'] = final_full_decoded_df['Negative_keywords_encoded'].apply(
            lambda x: robust_decode_negative_keywords(x, le_neg)
        )
# -------------------------------------------
# 14. Analyze for high clicks and low CPC
# -------------------------------------------
df_preds = final_full_decoded_df
clicks_threshold = df_preds['clicks'].quantile(0.95)
cpc_threshold = df_preds['average_cpc_usd'].quantile(0.10)
filtered_df = df_preds[(df_preds['clicks'] >= clicks_threshold) & (df_preds['average_cpc_usd'] <= cpc_threshold)]
sorted_df = filtered_df.sort_values(by=['clicks', 'average_cpc_usd'], ascending=[False, True])
top_20_rows = sorted_df.head(100)
selected_columns = [
    'campaign_id',
    'ad_group_id',
    'Date_Day',
    'Negative_keywords_encoded',
    'Keyword_Quality_Estimated_Quality_Score',
    'resource_name',
    'ad_schedule_start_hour',
    'ad_schedule_end_hour',
    'Keyword_Quality_Keyword',
    'Keyword_performance_Keyword_Text',
    'keywords_meta_keyword_text',
    'search_term_search_term',
    'Keyword_Quality_KW_types',
    'bidding_strategy_bidding_strategy_type',
    'Budget',
    'bid_Adjustments_device_type',
    'day_of_week',
    'geographic_report_geo_target_constant',
    'Device_performance_Device',
    'Keyword_performance_Keyword_Match_Type',
    'keywords_meta_match_type',
    'cost_usd'
]
available_columns = [col for col in selected_columns if col in top_20_rows.columns]

# ----------- MODIFICATION STARTS HERE -----------
top3_rows = top_20_rows.head(3)  # Select top 3 rows

# Always append top 3 rows to new file on each run
append_file = 'top3_clicks_low_cpc_history.csv'
if not os.path.isfile(append_file):
    top3_rows.to_csv(append_file, index=False, mode='w')
else:
    top3_rows.to_csv(append_file, index=False, mode='a', header=False)

top5_rows = top_20_rows.head(5)
output_dict = {}
for col in available_columns:
    vals = top5_rows[col].apply(lambda x: x.item() if hasattr(x, 'item') else x).tolist()
    output_dict[col] = vals
json_str = json.dumps(output_dict, indent=2)
print(json_str)
# Save JSON for best clicks/CPC
with open('best_clicks_low_cpc_input_changes_top5.json', 'w') as f:
    f.write(json_str)
print("Saved best clicks/CPC JSON to ranked_filtered_top5.json")
print("Top 20 input variations maximizing clicks while minimizing average CPC:")
print(top_20_rows[['clicks', 'average_cpc_usd']])
top_20_rows.to_csv('best_clicks_low_cpc_input_changes.csv', index=False)
print("Saved best clicks vs CPC balanced inputs to best_clicks_low_cpc_input_changes.csv")
print(f"Appended top 3 rows to {append_file}")
# ----------- MODIFICATION ENDS HERE ------------

# ----------- CONVERSIONS BLOCK BEGINS -----------
# Analyze for high conversions and low cost_per_conversion_usd
# Calculate cost per conversion (handle division by zero)
df_preds['cost_per_conversion_usd'] = df_preds.apply(
    lambda row: row['cost_usd'] / row['ad_performance_Conversions'] if row['ad_performance_Conversions'] > 0 else 0,
    axis=1
)

conversion_threshold = df_preds['ad_performance_Conversions'].quantile(0.95)
costconv_threshold = df_preds['cost_per_conversion_usd'].quantile(0.10)
filtered_conv_df = df_preds[
    (df_preds['ad_performance_Conversions'] >= conversion_threshold) &
    (df_preds['cost_per_conversion_usd'] <= costconv_threshold)
]
sorted_conv_df = filtered_conv_df.sort_values(by=['ad_performance_Conversions', 'cost_per_conversion_usd'], ascending=[False, True])
top_20_conv_rows = sorted_conv_df.head(100)

# Always append top 3 rows to new file on each run for conversions
top3_conv_rows = top_20_conv_rows.head(3)
append_conv_file = 'top3_conversions_clicks_low_cost_history.csv'
if not os.path.isfile(append_conv_file):
    top3_conv_rows.to_csv(append_conv_file, index=False, mode='w')
else:
    top3_conv_rows.to_csv(append_conv_file, index=False, mode='a', header=False)

# Output result structure for best conversion rows
top5_conv_rows = top_20_conv_rows.head(5)
output_conv_dict = {}
for col in available_columns:
    vals = top5_conv_rows[col].apply(lambda x: x.item() if hasattr(x, 'item') else x).tolist()
    output_conv_dict[col] = vals
json_str_conv = json.dumps(output_conv_dict, indent=2)
print(json_str_conv)
# Save JSON for best conversions/cost
with open('ranked_filtered_top5_conversions.json', 'w') as f:
    f.write(json_str_conv)
print("Saved best conversions/cost JSON to ranked_filtered_top5_conversions.json")
print("Top 20 input variations maximizing conversions while minimizing cost per conversion (usd):")
print(top_20_conv_rows[['ad_performance_Conversions', 'cost_per_conversion_usd']])
top_20_conv_rows.to_csv('best_conversions_low_cost_input_changes.csv', index=False)
print("Saved best conversions vs cost balanced inputs to best_conversions_low_cost_input_changes.csv")
print(f"Appended top 3 rows to {append_conv_file}")
# ----------- CONVERSIONS BLOCK ENDS -----------
