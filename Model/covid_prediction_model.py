import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
import prophet
from prophet import Prophet
import warnings
warnings.filterwarnings('ignore')

class COVIDPredictionModel:
    def __init__(self):
        self.rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.prophet_model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=True,
            changepoint_prior_scale=0.05
        )
        self.scaler = StandardScaler()
        
    def preprocess_data(self, df_input):
        """Preprocess the time series data"""
        if df_input is None:
            print("Input DataFrame is None in preprocess_data")
            return None
        df = df_input.copy() # Work on a copy

        try:
            # Ensure 'Date' column is in datetime format
            # The load_data function in app.py should have already handled this.
            # This is a safeguard or for standalone use of the model.
            if not pd.api.types.is_datetime64_any_dtype(df['Date']):
                if 'ObservationDate' in df.columns:
                    df['Date'] = pd.to_datetime(df['ObservationDate'], errors='coerce')
                else:
                    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            
            df.dropna(subset=['Date'], inplace=True)
            df = df.sort_values('Date')
            
            df['Day'] = df['Date'].dt.day
            df['Month'] = df['Date'].dt.month
            df['Year'] = df['Date'].dt.year
            df['DayOfWeek'] = df['Date'].dt.dayofweek

            # Ensure numeric columns are correct before rolling average
            numeric_cols_for_ma = ['Confirmed', 'Deaths']
            for col in numeric_cols_for_ma:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                else:
                    print(f"Warning: Column {col} not found for rolling average.")
                    df[col] = 0 # Add column with 0 if missing to avoid error
            
            # Calculate rolling averages safely
            if 'State/UnionTerritory' in df.columns and 'Confirmed' in df.columns:
                df['Confirmed_MA7'] = df.groupby('State/UnionTerritory')['Confirmed'].transform(
                    lambda x: x.rolling(window=7, min_periods=1).mean()
                )
            else:
                 df['Confirmed_MA7'] = 0

            if 'State/UnionTerritory' in df.columns and 'Deaths' in df.columns:
                df['Death_MA7'] = df.groupby('State/UnionTerritory')['Deaths'].transform(
                    lambda x: x.rolling(window=7, min_periods=1).mean()
                )
            else:
                df['Death_MA7'] = 0
            
            return df
        except Exception as e:
            print(f"Error in preprocess_data: {str(e)}")
            return None
    
    def prepare_prophet_data(self, df_input, state=None):
        """Prepare data for Prophet model"""
        if df_input is None:
            print("Input DataFrame is None in prepare_prophet_data")
            return None
        df = df_input.copy()

        if state:
            if 'State/UnionTerritory' in df.columns:
                df = df[df['State/UnionTerritory'] == state]
            else:
                print(f"State column 'State/UnionTerritory' not found for filtering state {state}")
                return None # Or handle as appropriate
        
        # Aggregate data by date
        prophet_df = df.groupby('Date').agg({
            'Confirmed': 'sum',
            'Deaths': 'sum',
            # 'Cured' is not used by Prophet y, but can be kept if needed elsewhere
            # 'Cured': 'sum' 
        }).reset_index()
        
        prophet_df = prophet_df.rename(columns={'Date': 'ds', 'Confirmed': 'y'})
        
        return prophet_df
    
    def train_models(self, df):
        """Train both Random Forest and Prophet models"""
        # Preprocess data
        processed_df = self.preprocess_data(df)
        
        # Prepare features for Random Forest
        features = ['Day', 'Month', 'Year', 'DayOfWeek', 'Confirmed_MA7', 'Death_MA7']
        X = processed_df[features]
        y = processed_df['Confirmed']
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42
        )
        
        # Train Random Forest
        self.rf_model.fit(X_train, y_train)
        
        # Train Prophet
        prophet_df = self.prepare_prophet_data(df)
        self.prophet_model.fit(prophet_df)
        
        return X_test, y_test
    
    def predict(self, df, days_to_predict=30):
        """Make predictions using both models"""
        # Random Forest predictions
        processed_df = self.preprocess_data(df)
        features = ['Day', 'Month', 'Year', 'DayOfWeek', 'Confirmed_MA7', 'Death_MA7']
        X = processed_df[features]
        X_scaled = self.scaler.transform(X)
        rf_predictions = self.rf_model.predict(X_scaled)
        
        # Prophet predictions
        future_dates = self.prophet_model.make_future_dataframe(periods=days_to_predict)
        prophet_forecast = self.prophet_model.predict(future_dates)
        
        return {
            'rf_predictions': rf_predictions,
            'prophet_forecast': prophet_forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
        }
    
    def evaluate_models(self, X_test, y_test):
        """Evaluate model performance"""
        # Random Forest evaluation
        rf_predictions = self.rf_model.predict(X_test)
        rf_mse = mean_squared_error(y_test, rf_predictions)
        rf_r2 = r2_score(y_test, rf_predictions)
        
        return {
            'rf_mse': rf_mse,
            'rf_r2': rf_r2
        }
    
    def get_state_predictions(self, df, state, days_to_predict=30):
        """Get predictions for a specific state"""
        # Filter data for the state
        state_df = df[df['State/UnionTerritory'] == state]
        
        # Prepare Prophet data for the state
        prophet_df = self.prepare_prophet_data(state_df, state)
        
        # Train state-specific Prophet model
        state_prophet = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=True,
            changepoint_prior_scale=0.05
        )
        state_prophet.fit(prophet_df)
        
        # Make predictions
        future_dates = state_prophet.make_future_dataframe(periods=days_to_predict)
        state_forecast = state_prophet.predict(future_dates)
        
        return state_forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]

def main():
    # Load data
    df = pd.read_csv('timeseries_india.csv')
    
    # Initialize and train model
    model = COVIDPredictionModel()
    X_test, y_test = model.train_models(df)
    
    # Evaluate models
    evaluation = model.evaluate_models(X_test, y_test)
    print("Model Evaluation:")
    print(f"Random Forest MSE: {evaluation['rf_mse']:.2f}")
    print(f"Random Forest R2 Score: {evaluation['rf_r2']:.2f}")
    
    # Make predictions
    predictions = model.predict(df)
    
    # Get state-specific predictions
    state_predictions = model.get_state_predictions(df, 'Maharashtra')
    
    return model, predictions, state_predictions

if __name__ == "__main__":
    main() 