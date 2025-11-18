"""
Visualization utilities for forecast results
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Optional, List
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots


class ForecastVisualizer:
    """Visualize forecast results"""

    def __init__(self, style: str = 'seaborn'):
        """Initialize visualizer"""
        plt.style.use(style if style in plt.style.available else 'default')
        sns.set_palette("husl")

    @staticmethod
    def plot_forecast(result,
                     historical_data: Optional[pd.DataFrame] = None,
                     title: str = "Forecast Results",
                     figsize: tuple = (15, 8)):
        """
        Plot forecast with confidence intervals

        Args:
            result: ForecastResult object
            historical_data: Optional historical data to plot
            title: Plot title
            figsize: Figure size

        Returns:
            matplotlib figure
        """
        fig, ax = plt.subplots(figsize=figsize)

        # Plot historical data if provided
        if historical_data is not None:
            ax.plot(historical_data['ds'],
                   historical_data['y'],
                   label='Historical',
                   color='black',
                   linewidth=2)

        # Plot historical fitted values
        if result.historical_df is not None and len(result.historical_df) > 0:
            ax.plot(result.historical_df['ds'],
                   result.historical_df['yhat'],
                   label='Fitted',
                   color='blue',
                   linestyle='--',
                   alpha=0.7)

        # Plot forecast
        ax.plot(result.forecast_df['ds'],
               result.forecast_df['yhat'],
               label='Forecast',
               color='red',
               linewidth=2,
               marker='o')

        # Plot confidence intervals
        if 'yhat_lower' in result.forecast_df.columns:
            ax.fill_between(result.forecast_df['ds'],
                           result.forecast_df['yhat_lower'],
                           result.forecast_df['yhat_upper'],
                           alpha=0.3,
                           color='red',
                           label='Confidence Interval')

        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Value', fontsize=12)
        ax.set_title(f"{title} - {result.model_name}", fontsize=14, fontweight='bold')
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        return fig

    @staticmethod
    def plot_forecast_interactive(result,
                                 historical_data: Optional[pd.DataFrame] = None,
                                 title: str = "Forecast Results"):
        """
        Create interactive plotly forecast plot

        Args:
            result: ForecastResult object
            historical_data: Optional historical data
            title: Plot title

        Returns:
            plotly figure
        """
        fig = go.Figure()

        # Historical data
        if historical_data is not None:
            fig.add_trace(go.Scatter(
                x=historical_data['ds'],
                y=historical_data['y'],
                mode='lines',
                name='Historical',
                line=dict(color='black', width=2)
            ))

        # Fitted values
        if result.historical_df is not None and len(result.historical_df) > 0:
            fig.add_trace(go.Scatter(
                x=result.historical_df['ds'],
                y=result.historical_df['yhat'],
                mode='lines',
                name='Fitted',
                line=dict(color='blue', width=1, dash='dash'),
                opacity=0.7
            ))

        # Confidence interval
        if 'yhat_upper' in result.forecast_df.columns:
            fig.add_trace(go.Scatter(
                x=result.forecast_df['ds'],
                y=result.forecast_df['yhat_upper'],
                mode='lines',
                name='Upper Bound',
                line=dict(width=0),
                showlegend=False
            ))

            fig.add_trace(go.Scatter(
                x=result.forecast_df['ds'],
                y=result.forecast_df['yhat_lower'],
                mode='lines',
                name='Confidence Interval',
                fill='tonexty',
                fillcolor='rgba(255, 0, 0, 0.2)',
                line=dict(width=0)
            ))

        # Forecast
        fig.add_trace(go.Scatter(
            x=result.forecast_df['ds'],
            y=result.forecast_df['yhat'],
            mode='lines+markers',
            name='Forecast',
            line=dict(color='red', width=2),
            marker=dict(size=8)
        ))

        fig.update_layout(
            title=f"{title} - {result.model_name}",
            xaxis_title="Date",
            yaxis_title="Value",
            hovermode='x unified',
            template='plotly_white'
        )

        return fig

    @staticmethod
    def plot_multiple_forecasts(results: dict,
                               historical_data: Optional[pd.DataFrame] = None,
                               title: str = "Model Comparison",
                               figsize: tuple = (15, 8)):
        """
        Plot multiple forecast results for comparison

        Args:
            results: Dictionary of {model_name: ForecastResult}
            historical_data: Optional historical data
            title: Plot title
            figsize: Figure size

        Returns:
            matplotlib figure
        """
        fig, ax = plt.subplots(figsize=figsize)

        # Plot historical
        if historical_data is not None:
            ax.plot(historical_data['ds'],
                   historical_data['y'],
                   label='Historical',
                   color='black',
                   linewidth=2,
                   alpha=0.7)

        # Plot each forecast
        colors = plt.cm.Set1(np.linspace(0, 1, len(results)))

        for (model_name, result), color in zip(results.items(), colors):
            ax.plot(result.forecast_df['ds'],
                   result.forecast_df['yhat'],
                   label=f'{model_name} (MAPE: {result.metrics.get("mape", 0):.2%})',
                   linewidth=2,
                   marker='o',
                   markersize=4,
                   color=color)

        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Value', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        return fig

    @staticmethod
    def plot_metrics_comparison(results: dict, figsize: tuple = (12, 6)):
        """
        Plot metrics comparison across models

        Args:
            results: Dictionary of {model_name: ForecastResult}
            figsize: Figure size

        Returns:
            matplotlib figure
        """
        # Extract metrics
        metrics_df = pd.DataFrame({
            name: result.metrics
            for name, result in results.items()
        }).T

        # Select key metrics
        key_metrics = ['mape', 'mae', 'rmse', 'r2']
        available_metrics = [m for m in key_metrics if m in metrics_df.columns]

        if not available_metrics:
            print("No metrics available for comparison")
            return None

        # Create subplots
        n_metrics = len(available_metrics)
        fig, axes = plt.subplots(1, n_metrics, figsize=figsize)

        if n_metrics == 1:
            axes = [axes]

        for ax, metric in zip(axes, available_metrics):
            metrics_df[metric].plot(kind='bar', ax=ax, color='steelblue')
            ax.set_title(metric.upper(), fontweight='bold')
            ax.set_ylabel('Value')
            ax.grid(True, alpha=0.3, axis='y')
            ax.tick_params(axis='x', rotation=45)

        plt.tight_layout()
        return fig

    @staticmethod
    def plot_residuals(result,
                      historical_data: pd.DataFrame,
                      figsize: tuple = (15, 10)):
        """
        Plot residual analysis

        Args:
            result: ForecastResult object
            historical_data: Historical data with actual values
            figsize: Figure size

        Returns:
            matplotlib figure
        """
        # Calculate residuals
        merged = pd.merge(
            historical_data[['ds', 'y']],
            result.historical_df,
            on='ds',
            how='inner'
        )

        residuals = merged['y'] - merged['yhat']

        # Create subplots
        fig, axes = plt.subplots(2, 2, figsize=figsize)

        # 1. Residuals over time
        axes[0, 0].plot(merged['ds'], residuals, marker='o', linestyle='-', alpha=0.6)
        axes[0, 0].axhline(y=0, color='r', linestyle='--')
        axes[0, 0].set_title('Residuals Over Time')
        axes[0, 0].set_xlabel('Date')
        axes[0, 0].set_ylabel('Residual')
        axes[0, 0].grid(True, alpha=0.3)

        # 2. Histogram of residuals
        axes[0, 1].hist(residuals, bins=30, edgecolor='black', alpha=0.7)
        axes[0, 1].set_title('Distribution of Residuals')
        axes[0, 1].set_xlabel('Residual')
        axes[0, 1].set_ylabel('Frequency')
        axes[0, 1].grid(True, alpha=0.3, axis='y')

        # 3. Actual vs Predicted
        axes[1, 0].scatter(merged['y'], merged['yhat'], alpha=0.6)
        min_val = min(merged['y'].min(), merged['yhat'].min())
        max_val = max(merged['y'].max(), merged['yhat'].max())
        axes[1, 0].plot([min_val, max_val], [min_val, max_val], 'r--')
        axes[1, 0].set_title('Actual vs Predicted')
        axes[1, 0].set_xlabel('Actual')
        axes[1, 0].set_ylabel('Predicted')
        axes[1, 0].grid(True, alpha=0.3)

        # 4. Q-Q plot
        from scipy import stats
        stats.probplot(residuals, dist="norm", plot=axes[1, 1])
        axes[1, 1].set_title('Q-Q Plot')
        axes[1, 1].grid(True, alpha=0.3)

        plt.tight_layout()
        return fig

    @staticmethod
    def create_dashboard(result,
                        historical_data: pd.DataFrame,
                        title: str = "Forecast Dashboard"):
        """
        Create comprehensive dashboard

        Args:
            result: ForecastResult object
            historical_data: Historical data
            title: Dashboard title

        Returns:
            plotly figure with subplots
        """
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Forecast with Confidence Intervals',
                'Metrics Summary',
                'Actual vs Predicted',
                'Forecast Table'
            ),
            specs=[
                [{"type": "scatter"}, {"type": "bar"}],
                [{"type": "scatter"}, {"type": "table"}]
            ]
        )

        # 1. Forecast plot
        fig.add_trace(
            go.Scatter(x=historical_data['ds'], y=historical_data['y'],
                      mode='lines', name='Historical',
                      line=dict(color='black')),
            row=1, col=1
        )

        fig.add_trace(
            go.Scatter(x=result.forecast_df['ds'], y=result.forecast_df['yhat'],
                      mode='lines+markers', name='Forecast',
                      line=dict(color='red')),
            row=1, col=1
        )

        # 2. Metrics bar chart
        metrics = result.metrics
        metric_names = list(metrics.keys())[:5]  # Top 5 metrics
        metric_values = [metrics[k] for k in metric_names]

        fig.add_trace(
            go.Bar(x=metric_names, y=metric_values, name='Metrics'),
            row=1, col=2
        )

        # 3. Actual vs Predicted
        if result.historical_df is not None:
            merged = pd.merge(historical_data[['ds', 'y']], result.historical_df, on='ds')
            fig.add_trace(
                go.Scatter(x=merged['y'], y=merged['yhat'],
                          mode='markers', name='Actual vs Predicted'),
                row=2, col=1
            )

        # 4. Forecast table
        table_df = result.forecast_df.head(10)
        fig.add_trace(
            go.Table(
                header=dict(values=list(table_df.columns)),
                cells=dict(values=[table_df[col] for col in table_df.columns])
            ),
            row=2, col=2
        )

        fig.update_layout(height=800, title_text=title, showlegend=True)

        return fig
