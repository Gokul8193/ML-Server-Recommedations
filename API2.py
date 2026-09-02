from flask import Flask, jsonify, request
import os
import pandas as pd

app = Flask(__name__)

# Paths to CSV files
CLICKS_CSV = "/home/minorilabs/Desktop/Google ads Client/google-ads-python/examples/reporting/input_params/SCheduled/clicks_unique_values.csv"
CONVERSIONS_CSV = "/home/minorilabs/Desktop/Google ads Client/google-ads-python/examples/reporting/input_params/SCheduled/conversions_unique_values.csv"
CLICKS_MINORI_CSV = "/home/minorilabs/Desktop/Google ads Client/google-ads-python/examples/reporting/input_params/SCheduled/clicks_unique_values_minori.csv"
CONVERSIONS_MINORI_CSV = "/home/minorilabs/Desktop/Google ads Client/google-ads-python/examples/reporting/input_params/SCheduled/conversions_unique_values_minori.csv"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCHEDULED_DIR = os.path.join(BASE_DIR, "input_params", "Scheduled")
CLICKS_CSV = os.path.join(
    SCHEDULED_DIR,
    "clicks_unique_values.csv"
)

CONVERSIONS_CSV = os.path.join(
    SCHEDULED_DIR,
    "conversions_unique_values.csv"
)

CLICKS_MINORI_CSV = os.path.join(
    SCHEDULED_DIR,
    "clicks_unique_values_minori.csv"
)

CONVERSIONS_MINORI_CSV = os.path.join(
    SCHEDULED_DIR,
    "conversions_unique_values_minori.csv"
)

@app.route('/recommendation', methods=['POST'])
def get_recommendation():
    try:
        # Parse the request data
        data = request.get_json()
        if not data or 'Customer_id' not in data:
            return jsonify({"error": "Missing 'Customer_id' in request body"}), 400

        customer_id = str(data['Customer_id'])

        # Load the CSV files
        try:
            clicks_df = pd.read_csv(CLICKS_CSV)
            conversions_df = pd.read_csv(CONVERSIONS_CSV)
            clicks_minori_df = pd.read_csv(CLICKS_MINORI_CSV)
            conversions_minori_df = pd.read_csv(CONVERSIONS_MINORI_CSV)
        except FileNotFoundError:
            return jsonify({"error": "CSV files not found. Please ensure they exist."}), 500
        except Exception as e:
            return jsonify({"error": f"Error loading CSV files: {str(e)}"}), 500

        # Debugging: Print the first few rows of the dataframes
        print("Clicks DataFrame:")
        print(clicks_df.head())
        print("Conversions DataFrame:")
        print(conversions_df.head())
        print("Clicks Minori DataFrame:")
        print(clicks_minori_df.head())
        print("Conversions Minori DataFrame:")
        print(conversions_minori_df.head())

        # Filter data based on Customer_id
        clicks_filtered = clicks_df[clicks_df['Customer_id'].astype(str) == customer_id]
        conversions_filtered = conversions_df[conversions_df['Customer_id'].astype(str) == customer_id]
        clicks_minori_filtered = clicks_minori_df[clicks_minori_df['Customer_id'].astype(str) == customer_id]
        conversions_minori_filtered = conversions_minori_df[conversions_minori_df['Customer_id'].astype(str) == customer_id]

        # Debugging: Print the filtered data
        print("Filtered Clicks DataFrame:")
        print(clicks_filtered)
        print("Filtered Conversions DataFrame:")
        print(conversions_filtered)
        print("Filtered Clicks Minori DataFrame:")
        print(clicks_minori_filtered)
        print("Filtered Conversions Minori DataFrame:")
        print(conversions_minori_filtered)

        # Check if there are matching rows
        if (clicks_filtered.empty and conversions_filtered.empty and
            clicks_minori_filtered.empty and conversions_minori_filtered.empty):
            return jsonify({"message": "No recommendations found for the given Customer_id"}), 404

        # Combine recommendations from all datasets
        recommendations = {
            "optimize_for_clicks_recommendations": clicks_filtered.to_dict(orient='records') + clicks_minori_filtered.to_dict(orient='records'),
            "optimize_for_conversions_recommendations": conversions_filtered.to_dict(orient='records') + conversions_minori_filtered.to_dict(orient='records')
        }

        return jsonify({
            "message": "Recommendations retrieved successfully",
            "recommendations": recommendations
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)