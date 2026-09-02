import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder, MinMaxScaler
import random

# -------------------------------------------
# 1. Load and preprocess dataset
# -------------------------------------------
import os

input_dir = os.path.join(os.path.dirname(__file__), "input_params")

df = pd.read_csv(os.path.join(input_dir, "merged_df12.csv"), low_memory=False)
df = df.sample(frac=0.5, random_state=42).reset_index(drop=True)
print("Number of NaN values per column:")
pd.set_option('display.max_rows', None)
print(df.isnull().sum())

df['ad_group_id'] = df.groupby('campaign_id')['ad_group_id'].transform(
    lambda x: x.fillna(x.mode()[0] if not x.mode().empty else 0))
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
    grouped_kw['Keyword_Quality_KW_types'].transform(lambda x: x.mode()[0] if not x.mode().empty else None)
)

for col in df.columns[df.isnull().any()]:
    non_null_vals = df[col].dropna()
    n_missing = df[col].isnull().sum()
    if n_missing > 0 and len(non_null_vals) > 0:
        df.loc[df[col].isnull(), col] = random.choices(non_null_vals.tolist(), k=n_missing)

drop_cols = ['bidding_strategy_budget_amount_consumed', 'bidding_strategy_target_roas', 'bidding_strategy_target_cpa_micros']
df.drop(columns=[c for c in drop_cols if c in df.columns], inplace=True)
df.drop_duplicates(inplace=True)

# -------------------------------------------
# 2. Encode categorical columns
# -------------------------------------------
categorical_cols = [
    'Keyword_Quality_Keyword', 'Keyword_Quality_KW_types', 'Device_performance_Device',
    'Keyword_performance_Keyword_Text', 'Keyword_performance_Keyword_Match_Type',
    'bid_Adjustments_device_type', 'bid_Adjustments_device_type_name', 'resource_name', 'day_of_week',
    'keywords_meta_keyword_text', 'keywords_meta_match_type', 'search_term_search_term',
    'bidding_strategy_bidding_strategy_type', 'Negative_keywords', 'geographic_report_geo_target_constant'
]

df_cat = df[categorical_cols].copy()
df_num = df.drop(columns=categorical_cols)

high_card_cols = [
    'Keyword_Quality_Keyword', 'Keyword_performance_Keyword_Text', 'resource_name',
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
skew_cols = ['impressions', 'clicks', 'cost_usd', 'ctr', 'average_cpc_usd']
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
target_cols = ['impressions', 'clicks', 'cost_usd', 'ctr', 'average_cpc_usd']
for c in target_cols:
    if c not in final_df.columns:
        raise KeyError(f"Missing target column: {c}")

X = final_df.drop(columns=target_cols)
y = final_df[target_cols]
feature_cols = list(X.columns)

# -------------------------------------------
# 9. Load models and ensemble weights
# -------------------------------------------
rf_model = joblib.load('artifacts/saved_models/rf_multi_model.pkl')
xgb_model = joblib.load('artifacts/saved_models/xgb_multi_model.pkl')
ensemble_weights = joblib.load('artifacts/saved_models/ensemble_weights.pkl')
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

# -------------------------------------------
# 13. Loop over n, generate manual variations, predict, decode, and save
# -------------------------------------------
n_list = [10,20,30,40,50,60,70,80,90,100,150,200,250,300,350,400,450,500]

all_full_runs = []

for n in n_list:
    manual_input_df = generate_manual_variations(feature_cols, n=n)
    missing_cols = set(feature_cols) - set(manual_input_df.columns)
    if missing_cols:
        continue
    preds, full_history = track_predictions(manual_input_df)
    decoded_run_df = decode_df(full_history.copy())
    decoded_run_df['n'] = n
    all_full_runs.append(decoded_run_df)

final_full_decoded_df = pd.concat(all_full_runs, ignore_index=True)

# -------------------------------------------
# 14. Analyze for high clicks and low CPC
# -------------------------------------------
df_preds = final_full_decoded_df

# Original scale conversion for clicks and average CPC assumed (already exponentiated in predictions)
# Define thresholds for clicks (75th percentile) and low CPC (50th percentile median)
clicks_threshold = df_preds['clicks'].quantile(0.100)
cpc_threshold = df_preds['average_cpc_usd'].quantile(0.3)

# Filter top clicks with low CPC entries
filtered_df = df_preds[(df_preds['clicks'] >= clicks_threshold) & (df_preds['average_cpc_usd'] <= cpc_threshold)]

# Sort by highest clicks and lowest average CPC
sorted_df = filtered_df.sort_values(by=['clicks', 'average_cpc_usd'], ascending=[False, True])

top_20_rows = sorted_df.head(20)

print("Top 20 input variations maximizing clicks while minimizing average CPC:")
print(top_20_rows[['clicks', 'average_cpc_usd']])

top_20_rows.to_csv('best_clicks_low_cpc_input_changes.csv', index=False)
print("Saved best clicks vs CPC balanced inputs to best_clicks_low_cpc_input_changes.csv")