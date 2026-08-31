import json
import os
import pandas as pd
from datetime import datetime

# Paths to files
clicks_json_path = "/home/minorilabs/Desktop/Google ads Client/google-ads-python/examples/reporting/input_params_minori/SCheduled/best_clicks_low_cpc_input_changes_top5.json"
conversions_json_path = "/home/minorilabs/Desktop/Google ads Client/google-ads-python/examples/reporting/input_params_minori/SCheduled/ranked_filtered_top5_conversions.json"
geotargets_path = "/home/minorilabs/Desktop/Google ads Client/google-ads-python/examples/reporting/input_params_minori/SCheduled/geotargets-2025-10-29.csv"

# Output file paths
clicks_unique_path = "/home/minorilabs/Desktop/Google ads Client/google-ads-python/examples/reporting/input_params/SCheduled/clicks_unique_values_minori.json"
conversions_unique_path = "/home/minorilabs/Desktop/Google ads Client/google-ads-python/examples/reporting/input_params/SCheduled/conversions_unique_values_minori.json"
clicks_unique_csv_path = "/home/minorilabs/Desktop/Google ads Client/google-ads-python/examples/reporting/input_params/SCheduled/clicks_unique_values_minori.csv"
conversions_unique_csv_path = "/home/minorilabs/Desktop/Google ads Client/google-ads-python/examples/reporting/input_params/SCheduled/conversions_unique_values_minori.csv"


def load_geotargets():
    """Load and process geotargets CSV file"""
    df = pd.read_csv(geotargets_path)
    df['Criteria ID'] = df['Criteria ID'].astype(str)
    return df


def convert_device_values(values):
    """Convert numeric device type values to their string representations"""
    converted = []
    for value in values:
        if isinstance(value, str) and value.replace('.', '').isdigit():
            value = float(value)
        if value == 2:
            converted.append('MOBILE')
        elif value == 4:
            converted.append('DESKTOP')
        elif value == 3:
            converted.append('TABLET')
        elif value == 6:
            converted.append('CONNECTED_TV')
        else:
            converted.append(value)
    return converted


def convert_geo_values(values, geotargets_df):
    """Convert geographic target constants to detailed info"""
    converted = []
    for value in values:
        if isinstance(value, str):
            value_str = value.split('.')[0]
        else:
            value_str = str(int(value))
        match = geotargets_df[geotargets_df['Criteria ID'] == value_str]
        if not match.empty:
            canonical_name = match['Canonical Name'].values[0]
            country_code = match['Country Code'].values[0]
            target_type = match['Target Type'].values[0]
            converted.append(f"{canonical_name} ({country_code}, {target_type})")
        else:
            converted.append(value)
    return converted


def convert_keyword_types(values):
    """Convert numeric keyword quality types to labels."""
    keyword_mapping = {
        0: "UNSPECIFIED",
        1: "UNKNOWN",
        2: "EXACT",
        3: "PHRASE",
        4: "BROAD"
    }
    converted = []
    for value in values:
        if isinstance(value, str) and value.replace('.', '').isdigit():
            value = float(value)
        if isinstance(value, float) and value.is_integer():
            value = int(value)
        converted.append(keyword_mapping.get(value, value))
    return converted


def load_json_data(file_path):
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except Exception as e:
        print(f"Error loading {file_path}: {str(e)}")
        return None


def process_data(data, geotargets_df):
    result = {}
    for key, values in data.items():
        if isinstance(values, list):
            if key in ['bid_Adjustments_device_type', 'Device_performance_Device']:
                values = convert_device_values(values)
            elif key == 'geographic_report_geo_target_constant':
                values = convert_geo_values(values, geotargets_df)
            elif key == 'Keyword_Quality_KW_types':
                values = convert_keyword_types(values)

            if key in ['ad_group_id', 'campaign_id']:
                unique_values = list(set(
                    map(lambda x: str(int(float(x))) if isinstance(x, str) and x.replace('.', '').isdigit()
                        else str(int(x)), values)))
            else:
                unique_values = list(set(map(str, values)))
            result[key] = unique_values
    return result


def json_to_table(json_dict, output_csv_path):
    """Append JSON data to CSV instead of overwriting."""
    rows = []
    ad_group_ids = json_dict.get("ad_group_id", [])
    other_columns = {k: v for k, v in json_dict.items() if k != "ad_group_id"}
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for ad_group_id in ad_group_ids:
        row = {"ad_group_id": ad_group_id, "timestamp": timestamp}
        for key, values in other_columns.items():
            row[key] = ", ".join(map(str, values))
        rows.append(row)

    new_df = pd.DataFrame(rows)

    if os.path.exists(output_csv_path):
        try:
            existing_df = pd.read_csv(output_csv_path)
            final_df = pd.concat([existing_df, new_df], ignore_index=True)
        except Exception as e:
            print(f"Error reading existing CSV, recreating file: {e}")
            final_df = new_df
    else:
        final_df = new_df

    final_df.to_csv(output_csv_path, index=False)
    print(f"Data appended to {output_csv_path}")


def extract_customer_id(resource_names):
    """Extract unique customer IDs from resource_name list."""
    customer_ids = set()
    for res in resource_names:
        try:
            customer_id = res.split('/')[1]
            customer_ids.add(customer_id)
        except Exception:
            continue
    return list(customer_ids)


def update_with_customer_id(json_path, csv_path):
    """Add Customer_id to JSON and CSV outputs."""
    with open(json_path, 'r') as f:
        data = json.load(f)
    resource_names = data.get('resource_name', [])
    customer_ids = extract_customer_id(resource_names)
    data['Customer_id'] = customer_ids

    # Save updated JSON
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=2)

    # Update CSV
    df = pd.read_csv(csv_path)
    df['Customer_id'] = ', '.join(customer_ids)
    df.to_csv(csv_path, index=False)
    print(f"Added Customer_id to {csv_path} and {json_path}")


# Load geotargets data
geotargets_df = load_geotargets()

# Process clicks JSON
clicks_data = load_json_data(clicks_json_path)
if clicks_data:
    clicks_unique = process_data(clicks_data, geotargets_df)
    with open(clicks_unique_path, 'w') as f:
        json.dump(clicks_unique, f, indent=2)
    print(f"Processed clicks data saved to {clicks_unique_path}")
    json_to_table(clicks_unique, clicks_unique_csv_path)
    update_with_customer_id(clicks_unique_path, clicks_unique_csv_path)

# Process conversions JSON
conversions_data = load_json_data(conversions_json_path)
if conversions_data:
    conversions_unique = process_data(conversions_data, geotargets_df)
    with open(conversions_unique_path, 'w') as f:
        json.dump(conversions_unique, f, indent=2)
    print(f"Processed conversions data saved to {conversions_unique_path}")
    json_to_table(conversions_unique, conversions_unique_csv_path)
    update_with_customer_id(conversions_unique_path, conversions_unique_csv_path)
