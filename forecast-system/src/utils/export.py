"""
Export utilities for forecast results
"""

import pandas as pd
import numpy as np
from typing import Optional, List
from pathlib import Path
import json


class ForecastExporter:
    """Export forecast results to various formats"""

    @staticmethod
    def to_csv(result,
               filepath: str,
               include_historical: bool = True,
               include_metrics: bool = True):
        """
        Export forecast to CSV

        Args:
            result: ForecastResult object
            filepath: Output file path
            include_historical: Include historical fitted values
            include_metrics: Include metrics sheet
        """
        # Main forecast
        result.forecast_df.to_csv(filepath, index=False)

        # Create additional files if requested
        base_path = Path(filepath).parent
        base_name = Path(filepath).stem

        if include_historical and result.historical_df is not None:
            historical_path = base_path / f"{base_name}_historical.csv"
            result.historical_df.to_csv(historical_path, index=False)

        if include_metrics:
            metrics_df = pd.DataFrame([result.metrics])
            metrics_path = base_path / f"{base_name}_metrics.csv"
            metrics_df.to_csv(metrics_path, index=False)

        print(f"Forecast exported to {filepath}")

    @staticmethod
    def to_excel(result,
                filepath: str,
                include_historical: bool = True,
                include_metrics: bool = True,
                include_components: bool = True):
        """
        Export forecast to Excel with multiple sheets

        Args:
            result: ForecastResult object
            filepath: Output file path
            include_historical: Include historical sheet
            include_metrics: Include metrics sheet
            include_components: Include components sheet (if available)
        """
        with pd.ExcelWriter(filepath, engine='xlsxwriter') as writer:
            # Forecast sheet
            result.forecast_df.to_excel(writer, sheet_name='Forecast', index=False)

            # Historical sheet
            if include_historical and result.historical_df is not None:
                result.historical_df.to_excel(writer, sheet_name='Historical', index=False)

            # Metrics sheet
            if include_metrics:
                metrics_df = pd.DataFrame([result.metrics])
                metrics_df.to_excel(writer, sheet_name='Metrics', index=False)

            # Components sheet
            if include_components and result.components is not None:
                result.components.to_excel(writer, sheet_name='Components', index=False)

            # Model parameters
            params_df = pd.DataFrame([result.model_params])
            params_df.to_excel(writer, sheet_name='Parameters', index=False)

            # Summary sheet
            summary_data = {
                'Model': [result.model_name],
                'Forecast Periods': [len(result.forecast_df)],
                'Historical Periods': [len(result.historical_df) if result.historical_df is not None else 0],
                'MAPE': [result.metrics.get('mape', None)],
                'MAE': [result.metrics.get('mae', None)],
                'RMSE': [result.metrics.get('rmse', None)],
                'R²': [result.metrics.get('r2', None)]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)

        print(f"Forecast exported to {filepath}")

    @staticmethod
    def to_json(result, filepath: str):
        """
        Export forecast to JSON

        Args:
            result: ForecastResult object
            filepath: Output file path
        """
        output = {
            'model_name': result.model_name,
            'forecast': result.forecast_df.to_dict('records'),
            'metrics': result.metrics,
            'model_params': result.model_params
        }

        if result.historical_df is not None:
            output['historical'] = result.historical_df.to_dict('records')

        if result.confidence_intervals is not None:
            output['confidence_intervals'] = result.confidence_intervals.to_dict('records')

        with open(filepath, 'w') as f:
            json.dump(output, f, indent=2, default=str)

        print(f"Forecast exported to {filepath}")

    @staticmethod
    def to_html_report(result,
                      filepath: str,
                      historical_data: Optional[pd.DataFrame] = None,
                      include_plots: bool = True):
        """
        Export comprehensive HTML report

        Args:
            result: ForecastResult object
            filepath: Output file path
            historical_data: Historical data for plotting
            include_plots: Include visualization plots
        """
        html_parts = []

        # Header
        html_parts.append("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Forecast Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                h1 { color: #333; }
                h2 { color: #666; }
                table { border-collapse: collapse; width: 100%; margin: 20px 0; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #4CAF50; color: white; }
                .metric { display: inline-block; margin: 10px; padding: 15px; background: #f0f0f0; border-radius: 5px; }
                .metric-value { font-size: 24px; font-weight: bold; color: #4CAF50; }
                .metric-label { font-size: 12px; color: #666; }
            </style>
        </head>
        <body>
        """)

        # Title
        html_parts.append(f"<h1>Forecast Report - {result.model_name}</h1>")

        # Summary metrics
        html_parts.append("<h2>Performance Metrics</h2>")
        html_parts.append("<div>")
        for key, value in result.metrics.items():
            if key in ['mape', 'smape']:
                formatted_value = f"{value:.2%}"
            else:
                formatted_value = f"{value:,.2f}"

            html_parts.append(f"""
                <div class="metric">
                    <div class="metric-label">{key.upper()}</div>
                    <div class="metric-value">{formatted_value}</div>
                </div>
            """)
        html_parts.append("</div>")

        # Forecast table
        html_parts.append("<h2>Forecast Values</h2>")
        html_parts.append(result.forecast_df.to_html(index=False, classes='forecast-table'))

        # Model parameters
        html_parts.append("<h2>Model Parameters</h2>")
        params_html = "<ul>"
        for key, value in result.model_params.items():
            params_html += f"<li><strong>{key}:</strong> {value}</li>"
        params_html += "</ul>"
        html_parts.append(params_html)

        # Plots
        if include_plots and historical_data is not None:
            html_parts.append("<h2>Visualization</h2>")

            from .visualization import ForecastVisualizer
            viz = ForecastVisualizer()

            # Create plot
            fig = viz.plot_forecast_interactive(result, historical_data)

            # Convert to HTML
            plot_html = fig.to_html(include_plotlyjs='cdn')
            html_parts.append(plot_html)

        # Footer
        html_parts.append("""
        </body>
        </html>
        """)

        # Write to file
        with open(filepath, 'w') as f:
            f.write('\n'.join(html_parts))

        print(f"HTML report exported to {filepath}")

    @staticmethod
    def compare_models_to_excel(results: dict, filepath: str):
        """
        Export comparison of multiple models to Excel

        Args:
            results: Dictionary of {model_name: ForecastResult}
            filepath: Output file path
        """
        with pd.ExcelWriter(filepath, engine='xlsxwriter') as writer:
            # Metrics comparison
            metrics_comparison = []
            for model_name, result in results.items():
                row = {'Model': model_name}
                row.update(result.metrics)
                metrics_comparison.append(row)

            metrics_df = pd.DataFrame(metrics_comparison)
            metrics_df.to_excel(writer, sheet_name='Metrics Comparison', index=False)

            # Forecasts from each model
            for model_name, result in results.items():
                sheet_name = f"{model_name[:25]}_Forecast"  # Excel sheet name limit
                result.forecast_df.to_excel(writer, sheet_name=sheet_name, index=False)

        print(f"Model comparison exported to {filepath}")
