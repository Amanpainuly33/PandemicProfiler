from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import numpy as np
import os
import joblib
from datetime import datetime, timedelta
import sys
from dateutil import parser

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import after setting up path
from model.covid_prediction_model import COVIDPredictionModel

# Define date constants
MIN_DATE = datetime(2020, 1, 22)
MAX_DATE = datetime(2020, 8, 12)

app = Flask(__name__)

# Configure CORS properly
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5173"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"],
        "supports_credentials": True
    }
})

# Initialize model
model = None
_df = None # Use a different name to avoid confusion with the global df

def load_data():
    global _df # Use the renamed global variable
    if _df is not None:
        # If DataFrame is already loaded and filtered, return it
        # This assumes the 'Country/Region' filter is static
        return _df

    try:
        data_path = os.path.join(project_root, 'model', 'covid_19_data.csv')
        if not os.path.exists(data_path):
            print(f"Data file not found at: {data_path}")
            return None
            
        temp_df = pd.read_csv(data_path)
        
        # Filter for India first
        if 'Country/Region' in temp_df.columns:
            temp_df = temp_df[temp_df['Country/Region'].str.lower() == 'india'].copy() # Use .str.lower() for case-insensitive comparison and .copy()
            if temp_df.empty:
                print("No data found for Country/Region 'India'.")
                _df = None # Ensure _df is None if no India data
                return None
        else:
            print("Column 'Country/Region' not found in CSV. Cannot filter for India.")
            # Decide how to proceed: return None, or return unfiltered if that's acceptable
            # For now, let's return None as the request is specific to India.
            _df = None
            return None
            
        required_columns = ['ObservationDate', 'Province/State', 'Confirmed', 'Deaths', 'Recovered']
        missing_columns = [col for col in required_columns if col not in temp_df.columns]
        if missing_columns:
            print(f"Missing required columns after filtering for India: {missing_columns}")
            _df = None
            return None
            
        # Standardize date parsing
        try:
            temp_df['Date'] = pd.to_datetime(temp_df['ObservationDate'], errors='coerce')
        except Exception as e:
            print(f"Error converting ObservationDate to datetime: {str(e)}")
            _df = None
            return None

        temp_df.dropna(subset=['Date'], inplace=True)

        temp_df = temp_df.rename(columns={
            'Province/State': 'State/UnionTerritory',
            # 'Confirmed', 'Deaths', 'Recovered' are standard and likely don't need renaming if CSV matches
        })
        
        # Ensure correct timezone handling for filtering
        temp_df['Date'] = temp_df['Date'].dt.tz_localize(None)
        
        temp_df = temp_df[(temp_df['Date'] >= MIN_DATE) & (temp_df['Date'] <= MAX_DATE)]
        
        numeric_columns = ['Confirmed', 'Deaths', 'Cured'] # Assuming 'Recovered' was renamed to 'Cured'
        
        # Check if 'Cured' column exists after renaming, if not, it means 'Recovered' wasn't in the original required_columns or CSV
        if 'Cured' not in temp_df.columns and 'Recovered' in temp_df.columns: # Fallback if 'Recovered' was not renamed
             temp_df.rename(columns={'Recovered': 'Cured'}, inplace=True)
        elif 'Cured' not in temp_df.columns and 'Recovered' not in temp_df.columns:
            print("Neither 'Cured' nor 'Recovered' column found.")
            _df = None
            return None


        for col in numeric_columns:
            if col in temp_df.columns:
                temp_df[col] = pd.to_numeric(temp_df[col], errors='coerce').fillna(0).astype(int)
            else:
                print(f"Warning: Numeric column '{col}' not found. It will be missing from output.")
                # Decide if this is critical. For now, we proceed without it if missing.
        
        _df = temp_df.copy()
        return _df
    except Exception as e:
        print(f"Error loading data: {str(e)}")
        _df = None 
        return None

def initialize_model():
    global model
    global _df # Use the renamed global variable
    try:
        model_files_dir = os.path.join(project_root, 'model', 'model_files')
        if not os.path.exists(model_files_dir):
            os.makedirs(model_files_dir)
        
        model_path = os.path.join(model_files_dir, 'covid_model.joblib')
        
        # Attempt to load data first
        current_df = load_data()
        if current_df is None:
            print("Failed to load data, cannot initialize model.")
            return

        if os.path.exists(model_path):
            try:
                model = joblib.load(model_path)
                # Potentially, add a check here to see if the model needs retraining
                # based on data changes or a time interval.
            except Exception as load_exc:
                print(f"Failed to load existing model: {load_exc}. Retraining...")
                model = COVIDPredictionModel()
                model.train_models(current_df)
                joblib.dump(model, model_path)
        else:
            print("No existing model found. Training new model...")
            model = COVIDPredictionModel()
            model.train_models(current_df)
            joblib.dump(model, model_path)
    except Exception as e:
        print(f"Error initializing model: {str(e)}")
        model = None

@app.route('/api/states', methods=['GET'])
def get_states():
    current_df = load_data() # Use a local variable
    if current_df is None:
        return jsonify({"error": "Failed to load data"}), 500
    
    try:
        # Ensure 'State/UnionTerritory' column exists after renaming
        if 'State/UnionTerritory' not in current_df.columns:
            print("Column 'State/UnionTerritory' not found in DataFrame.")
            return jsonify({"error": "Data processing error: State column missing"}), 500

        states = sorted(current_df['State/UnionTerritory'].dropna().unique().tolist())
        if not states:
            return jsonify({"error": "No states found in data"}), 404 # 404 might be more appropriate
            
        return jsonify({"states": states})
    except Exception as e:
        print(f"Error getting states: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/data', methods=['GET'])
def get_data():
    current_df = load_data() # Use a local variable
    if current_df is None:
        return jsonify({"error": "Failed to load data"}), 500
        
    try:
        state = request.args.get('state')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        filtered_df = current_df.copy()
        
        if state:
            filtered_df = filtered_df[filtered_df['State/UnionTerritory'] == state]
        
        if start_date_str and end_date_str:
            try:
                start_dt = parser.parse(start_date_str).replace(tzinfo=None)
                end_dt = parser.parse(end_date_str).replace(tzinfo=None)
            except Exception as date_parse_exc:
                print(f"Error parsing dates: {date_parse_exc}")
                return jsonify({"error": "Invalid date format"}), 400

            start_dt = max(start_dt, MIN_DATE)
            end_dt = min(end_dt, MAX_DATE)
            
            filtered_df = filtered_df[(filtered_df['Date'] >= start_dt) & (filtered_df['Date'] <= end_dt)]
        
        if filtered_df.empty:
            return jsonify({
                'dates': [], 'confirmed': [], 'deaths': [], 'cured': []
            }), 200 # Return empty data instead of error if filters result in no data

        daily_data = filtered_df.groupby('Date').agg({
            'Confirmed': 'sum',
            'Deaths': 'sum',
            'Cured': 'sum'
        }).reset_index()
        
        return jsonify({
            'dates': daily_data['Date'].dt.strftime('%Y-%m-%d').tolist(),
            'confirmed': daily_data['Confirmed'].astype(int).tolist(),
            'deaths': daily_data['Deaths'].astype(int).tolist(),
            'cured': daily_data['Cured'].astype(int).tolist()
        })
    except Exception as e:
        print(f"Error in get_data: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/predictions', methods=['GET'])
def get_predictions():
    try:
        state = request.args.get('state')
        days = int(request.args.get('days', 30))
        
        if not model:
            initialize_model()
            
        if model is None:
            return jsonify({"error": "Failed to initialize model"}), 500
        
        df = load_data()
        if df is None:
            return jsonify({"error": "Failed to load data"}), 500
        
        if state:
            predictions = model.get_state_predictions(df, state, days)
        else:
            predictions = model.predict(df, days)
            predictions = predictions['prophet_forecast']
        
        if predictions is None:
            return jsonify({"error": "Failed to generate predictions"}), 500
            
        return jsonify({
            'dates': predictions['ds'].dt.strftime('%Y-%m-%d').tolist(),
            'predictions': predictions['yhat'].tolist(),
            'lower_bound': predictions['yhat_lower'].tolist(),
            'upper_bound': predictions['yhat_upper'].tolist()
        })
    except Exception as e:
        print(f"Error in get_predictions: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/growth-rate', methods=['GET'])
def get_growth_rate():
    try:
        state = request.args.get('state')
        df = load_data()
        if df is None:
            return jsonify({"error": "Failed to load data"}), 500
        
        if state:
            df = df[df['State/UnionTerritory'] == state]
        
        daily_data = df.groupby('Date').agg({'Confirmed': 'sum'}).reset_index()
        daily_data['Growth_Rate'] = daily_data['Confirmed'].pct_change() * 100
        daily_data['Growth_Rate'] = daily_data['Growth_Rate'].fillna(0)
        
        if daily_data.empty:
            return jsonify({"error": "No data found for growth rate calculation"}), 404
        
        return jsonify({
            'dates': daily_data['Date'].dt.strftime('%Y-%m-%d').tolist(),
            'growth_rate': daily_data['Growth_Rate'].round(2).tolist()
        })
    except Exception as e:
        print(f"Error in growth rate calculation: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/recovery-rate', methods=['GET'])
def get_recovery_rate():
    try:
        state = request.args.get('state')
        df = load_data()
        if df is None:
            return jsonify({"error": "Failed to load data"}), 500
        
        if state:
            df = df[df['State/UnionTerritory'] == state]
        
        daily_data = df.groupby('Date').agg({
            'Confirmed': 'sum',
            'Cured': 'sum'
        }).reset_index()
        
        daily_data['Recovery_Rate'] = (daily_data['Cured'] / daily_data['Confirmed'] * 100).fillna(0)
        
        if daily_data.empty:
            return jsonify({"error": "No data found for recovery rate calculation"}), 404
        
        return jsonify({
            'dates': daily_data['Date'].dt.strftime('%Y-%m-%d').tolist(),
            'recovery_rate': daily_data['Recovery_Rate'].round(2).tolist()
        })
    except Exception as e:
        print(f"Error in recovery rate calculation: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/state-comparison', methods=['GET'])
def get_state_comparison():
    states = request.args.getlist('states[]')
    df = load_data()
    
    result = {}
    for state in states:
        state_data = df[df['State/UnionTerritory'] == state]
        result[state] = {
            'dates': state_data['Date'].dt.strftime('%Y-%m-%d').tolist(),
            'confirmed': state_data['Confirmed'].tolist()
        }
    
    return jsonify(result)

if __name__ == '__main__':
    _df = None  # Reset DataFrame cache on app start
    initialize_model()
    app.run(debug=True, port=5000) 