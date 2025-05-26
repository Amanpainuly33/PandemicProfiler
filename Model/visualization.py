import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

class COVIDVisualizer:
    def __init__(self, df):
        self.df = df
        self.df['Date'] = pd.to_datetime(self.df['Date'], format='%d-%m-%Y')
        
    def create_timeline(self, state=None):
        """Create an interactive timeline of COVID cases"""
        if state:
            df = self.df[self.df['State/UnionTerritory'] == state]
        else:
            df = self.df.groupby('Date').agg({
                'Confirmed': 'sum',
                'Deaths': 'sum',
                'Cured': 'sum'
            }).reset_index()
            
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['Date'], y=df['Confirmed'],
                                name='Confirmed Cases',
                                line=dict(color='red')))
        fig.add_trace(go.Scatter(x=df['Date'], y=df['Deaths'],
                                name='Deaths',
                                line=dict(color='black')))
        fig.add_trace(go.Scatter(x=df['Date'], y=df['Cured'],
                                name='Recovered',
                                line=dict(color='green')))
        
        fig.update_layout(
            title='COVID-19 Timeline',
            xaxis_title='Date',
            yaxis_title='Number of Cases',
            hovermode='x unified'
        )
        
        return fig
    
    def create_state_heatmap(self):
        """Create a heatmap of cases by state"""
        latest_data = self.df.sort_values('Date').groupby('State/UnionTerritory').last()
        
        fig = px.choropleth_mapbox(
            latest_data,
            locations='State/UnionTerritory',
            geojson=None,  # You'll need to add GeoJSON data for India
            color='Confirmed',
            hover_name='State/UnionTerritory',
            hover_data=['Confirmed', 'Deaths', 'Cured'],
            color_continuous_scale='Reds',
            mapbox_style='carto-positron',
            zoom=3,
            center={'lat': 20.5937, 'lon': 78.9629},
            opacity=0.5
        )
        
        fig.update_layout(
            title='COVID-19 Cases by State',
            margin={'r': 0, 't': 30, 'l': 0, 'b': 0}
        )
        
        return fig
    
    def create_growth_rate_chart(self, state=None):
        """Create a chart showing case growth rate"""
        if state:
            df = self.df[self.df['State/UnionTerritory'] == state]
        else:
            df = self.df.groupby('Date').agg({
                'Confirmed': 'sum'
            }).reset_index()
            
        df['Growth_Rate'] = df['Confirmed'].pct_change() * 100
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['Date'],
            y=df['Growth_Rate'],
            name='Growth Rate',
            line=dict(color='blue')
        ))
        
        fig.update_layout(
            title='COVID-19 Case Growth Rate',
            xaxis_title='Date',
            yaxis_title='Growth Rate (%)',
            hovermode='x unified'
        )
        
        return fig
    
    def create_prediction_plot(self, actual_data, predictions, state=None):
        """Create a plot comparing actual vs predicted cases"""
        fig = go.Figure()
        
        # Plot actual data
        fig.add_trace(go.Scatter(
            x=actual_data['Date'],
            y=actual_data['Confirmed'],
            name='Actual Cases',
            line=dict(color='blue')
        ))
        
        # Plot predictions
        fig.add_trace(go.Scatter(
            x=predictions['ds'],
            y=predictions['yhat'],
            name='Predicted Cases',
            line=dict(color='red')
        ))
        
        # Add confidence intervals
        fig.add_trace(go.Scatter(
            x=predictions['ds'],
            y=predictions['yhat_upper'],
            fill=None,
            mode='lines',
            line_color='rgba(255,0,0,0.2)',
            name='Upper Bound'
        ))
        
        fig.add_trace(go.Scatter(
            x=predictions['ds'],
            y=predictions['yhat_lower'],
            fill='tonexty',
            mode='lines',
            line_color='rgba(255,0,0,0.2)',
            name='Lower Bound'
        ))
        
        fig.update_layout(
            title=f'COVID-19 Predictions {"for " + state if state else ""}',
            xaxis_title='Date',
            yaxis_title='Number of Cases',
            hovermode='x unified'
        )
        
        return fig
    
    def create_recovery_rate_chart(self, state=None):
        """Create a chart showing recovery rate over time"""
        if state:
            df = self.df[self.df['State/UnionTerritory'] == state]
        else:
            df = self.df.groupby('Date').agg({
                'Confirmed': 'sum',
                'Cured': 'sum'
            }).reset_index()
            
        df['Recovery_Rate'] = (df['Cured'] / df['Confirmed']) * 100
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['Date'],
            y=df['Recovery_Rate'],
            name='Recovery Rate',
            line=dict(color='green')
        ))
        
        fig.update_layout(
            title='COVID-19 Recovery Rate',
            xaxis_title='Date',
            yaxis_title='Recovery Rate (%)',
            hovermode='x unified'
        )
        
        return fig
    
    def create_state_comparison(self, states):
        """Create a comparison chart for multiple states"""
        fig = go.Figure()
        
        for state in states:
            state_data = self.df[self.df['State/UnionTerritory'] == state]
            fig.add_trace(go.Scatter(
                x=state_data['Date'],
                y=state_data['Confirmed'],
                name=state,
                mode='lines'
            ))
        
        fig.update_layout(
            title='COVID-19 Cases by State Comparison',
            xaxis_title='Date',
            yaxis_title='Number of Cases',
            hovermode='x unified'
        )
        
        return fig 