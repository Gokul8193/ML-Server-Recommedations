from flask import Flask, jsonify, request
import os
import pandas as pd

app = Flask(__name__)

# Paths to CSV files
CLICKS_CSV = "/home/minorilabs/Desktop/Google ads Client/google-ads-python/examples/reporting/input_params/SCheduled/clicks_unique_values.csv"
CONVERSIONS_CSV = "/home/minorilabs/Desktop/Google ads Client/google-ads-python/examples/reporting/input_params/SCheduled/conversions_unique_values.csv"

@app.route('/recommendation', methods=['POST'])
def get_recommendation():
    try:
        # Parse the request data
        data = request.get_json()
        if not data or 'campaign_id' not in data or 'ad_group_id' not in data:
            return jsonify({"error": "Missing 'campaign_id' or 'ad_group_id' in request body"}), 400

        campaign_id = str(data['campaign_id'])
        ad_group_id = str(data['ad_group_id'])

        # Load the CSV files
        try:
            clicks_df = pd.read_csv(CLICKS_CSV)
            conversions_df = pd.read_csv(CONVERSIONS_CSV)
        except FileNotFoundError:
            return jsonify({"error": "CSV files not found. Please ensure they exist."}), 500
        except Exception as e:
            return jsonify({"error": f"Error loading CSV files: {str(e)}"}), 500

        # Debugging: Print the first few rows of the dataframes
        print("Clicks DataFrame:")
        print(clicks_df.head())
        print("Conversions DataFrame:")
        print(conversions_df.head())

        # Filter data based on campaign_id and ad_group_id
        clicks_filtered = clicks_df[
            (clicks_df['campaign_id'].astype(str) == campaign_id) & (clicks_df['ad_group_id'].astype(str) == ad_group_id)
        ]
        conversions_filtered = conversions_df[
            (conversions_df['campaign_id'].astype(str) == campaign_id) & (conversions_df['ad_group_id'].astype(str) == ad_group_id)
        ]

        # Debugging: Print the filtered data
        print("Filtered Clicks DataFrame:")
        print(clicks_filtered)
        print("Filtered Conversions DataFrame:")
        print(conversions_filtered)

        # Check if there are matching rows
        if clicks_filtered.empty and conversions_filtered.empty:
            return jsonify({"message": "No recommendations found for the given campaign_id and ad_group_id"}), 404

        # Combine recommendations from both datasets
        recommendations = {
            "optimize_for_clicks_recommendations": clicks_filtered.to_dict(orient='records'),
            "optimize_for_conversions_recommendations": conversions_filtered.to_dict(orient='records')
        }

        return jsonify({
            "message": "Recommendations retrieved successfully",
            "recommendations": recommendations
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)