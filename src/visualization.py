"""
Visualization Module for Paper Trend Tracking

Creates:
- Keyword network graphs (clean, professional styling)
- Trend evolution charts
- Interactive dashboard (Plotly Dash)
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.offline import plot as plotly_plot
import networkx as nx
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from loguru import logger

try:
    from .database import DatabaseManager
    from .network_builder import NetworkBuilder, TrendAnalyzer, KeywordNetworkSnapshot
except ImportError:
    from database import DatabaseManager
    from network_builder import NetworkBuilder, TrendAnalyzer, KeywordNetworkSnapshot


class NetworkVisualizer:
    """Visualize keyword co-occurrence networks with professional styling"""
    
    def __init__(self, output_dir: str = "output/visualizations"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def plot_network(
        self,
        graph: nx.Graph,
        title: str = "Keyword Co-occurrence Network",
        top_n: int = 40,  # Reduced from 50 for cleaner view
        save: bool = True,
        show: bool = False
    ) -> str:
        """
        Create professional network visualization
        
        Args:
            graph: NetworkX graph
            title: Plot title
            top_n: Show only top N nodes by degree (reduced for clarity)
            save: Save to file
            show: Show in browser
        
        Returns:
            Path to saved HTML file
        """
        if graph.number_of_nodes() == 0:
            logger.warning("⚠️  Empty graph, creating placeholder")
            fig = go.Figure(layout=go.Layout(
                title=title,
                xaxis={'visible': False},
                yaxis={'visible': False},
                annotations=[{'text': 'No network data available', 'showarrow': False, 'font': {'size': 16}}]
            ))
            if save:
                output_path = self.output_dir / f"network_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                plotly_plot(fig, filename=str(output_path), auto_open=show)
                return str(output_path)
            return fig
        
        # Get top nodes by degree
        degrees = dict(graph.degree())
        top_nodes = sorted(degrees.keys(), key=lambda x: degrees[x], reverse=True)[:top_n]
        
        # Create subgraph
        G = graph.subgraph(top_nodes)
        
        # Compute layout using Kamada-Kawai for better aesthetics
        try:
            pos = nx.kamada_kawai_layout(G, scale=1.5)
        except:
            pos = nx.spring_layout(G, k=3, iterations=100, seed=42, weight=None)
        
        # Extract node positions
        node_x = [pos[node][0] for node in G.nodes()]
        node_y = [pos[node][1] for node in G.nodes()]
        node_labels = list(G.nodes())
        
        # Calculate node sizes with better scaling
        degree_values = [degrees[node] for node in G.nodes()]
        min_degree = min(degree_values) if degree_values else 1
        max_degree = max(degree_values) if degree_values else 1
        
        # Normalize and scale node sizes (much smaller than before)
        node_sizes = []
        for deg in degree_values:
            if max_degree == min_degree:
                normalized = 0.5
            else:
                normalized = (deg - min_degree) / (max_degree - min_degree)
            # Scale: 200-600 (much smaller than previous 150-800)
            size = 200 + normalized * 400
            node_sizes.append(size)
        
        # Create edge traces with subtle styling
        edge_traces = []
        edge_x, edge_y = [], []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        edge_trace = go.Scatter(
            x=edge_x,
            y=edge_y,
            mode='lines',
            line=dict(width=0.8, color='#d1d5db'),  # Light gray, thin lines
            hoverinfo='none',
            showlegend=False
        )
        
        # Create node trace with professional styling
        node_trace = go.Scatter(
            x=node_x,
            y=node_y,
            mode='markers+text',
            hoverinfo='text',
            text=node_labels,
            textposition="middle center",
            textfont=dict(size=8, color='#374151', family="Arial, sans-serif"),  # Smaller, darker font
            marker=dict(
                showscale=True,
                colorscale='Blues',  # Professional blue color scheme
                reversescale=False,
                color=degree_values,
                size=node_sizes,
                opacity=0.85,
                colorbar=dict(
                    thickness=10,  # Thinner colorbar
                    title=dict(text='Connections', side='right', font=dict(size=10)),
                    xanchor='left',
                    x=1.02,
                    len=0.5,
                    tickfont=dict(size=8)
                ),
                line=dict(width=1.5, color='#ffffff')  # White border for separation
            ),
            name='Keywords',
            hovertext=[f"{label}<br>Connections: {deg}" for label, deg in zip(node_labels, degree_values)]
        )
        
        # Create figure with professional layout
        fig = go.Figure(
            data=[edge_trace, node_trace],
            layout=go.Layout(
                title=dict(
                    text=title,
                    x=0.5,
                    y=0.95,
                    font=dict(size=16, color='#1f2937')
                ),
                showlegend=False,
                hovermode='closest',
                margin=dict(b=20, l=20, r=40, t=60),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[min(node_x)*1.1, max(node_x)*1.1]),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[min(node_y)*1.1, max(node_y)*1.1]),
                plot_bgcolor='#ffffff',
                paper_bgcolor='#ffffff',
                width=1200,  # Wider
                height=900,  # Taller for better spacing
            )
        )
        
        # Save or show
        if save:
            output_path = self.output_dir / f"network_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            plotly_plot(fig, filename=str(output_path), auto_open=show)
            logger.info(f"✅ Network plot saved: {output_path}")
            return str(output_path)
        
        return fig
    
    def plot_trend_evolution(
        self,
        trends: List[Dict],
        metric: str = 'growth_rate',
        top_n: int = 20,
        save: bool = True,
        show: bool = False
    ) -> str:
        """
        Plot trend evolution over time with professional styling
        
        Args:
            trends: List of trend data from TrendAnalyzer
            metric: Metric to plot ('growth_rate', 'momentum', 'pagerank', etc.)
            top_n: Show top N keywords
            save: Save to file
            show: Show in browser
        
        Returns:
            Path to saved HTML file
        """
        # Sort by metric
        sorted_trends = sorted(trends, key=lambda x: x.get(metric, 0), reverse=True)[:top_n]
        
        # Create bar chart
        keywords = [t['keyword'] for t in sorted_trends]
        values = [t.get(metric, 0) for t in sorted_trends]
        
        # Create color scale based on values
        colors = ['#1e40af' if v > np.percentile(values, 75) else '#3b82f6' if v > np.percentile(values, 50) else '#60a5fa' for v in values]
        
        fig = go.Figure(data=[
            go.Bar(
                x=keywords,
                y=values,
                marker_color=colors,
                hovertemplate='<b>%{x}</b><br>' + metric.replace('_', ' ').title() + ': %{y:.3f}<extra></extra>'
            )
        ])
        
        fig.update_layout(
            title=dict(
                text=f"Top Keywords by {metric.replace('_', ' ').title()}",
                x=0.5,
                font=dict(size=14, color='#1f2937')
            ),
            xaxis_title="Keyword",
            yaxis_title=metric.replace('_', ' ').title(),
            showlegend=False,
            hovermode='x unified',
            xaxis=dict(
                tickangle=-45,
                tickfont=dict(size=9),
                showgrid=False
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='#e5e7eb',
                zeroline=False
            ),
            height=500,
            width=1100,
            plot_bgcolor='#ffffff',
            paper_bgcolor='#ffffff',
            margin=dict(b=100, l=60, r=20, t=60)
        )
        
        if save:
            output_path = self.output_dir / f"trends_{metric}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            plotly_plot(fig, filename=str(output_path), auto_open=show)
            logger.info(f"✅ Trend plot saved: {output_path}")
            return str(output_path)
        
        return fig


class TrendDashboard:
    """
    Interactive Plotly Dash dashboard for trend exploration
    
    Features:
    - Real-time trend charts
    - Keyword network visualization
    - Filter by time window and metric
    - Data table with export
    """
    
    def __init__(self, db_path: str = "data/papers.db", base_dir: str = None):
        from pathlib import Path
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        db_path_obj = Path(db_path)
        if not db_path_obj.is_absolute():
            db_path_obj = self.base_dir / db_path_obj
        
        self.db = DatabaseManager(f"sqlite:///{db_path_obj}")
        self.network_builder = NetworkBuilder(self.db)
        self.trend_analyzer = TrendAnalyzer(self.db)
        self.visualizer = NetworkVisualizer()
    
    def create_dashboard(self, port: int = 8050, debug: bool = False):
        """Create and run Dash dashboard"""
        try:
            import dash
            from dash import Dash, dcc, html, Input, Output, callback_context, State
            from dash.exceptions import PreventUpdate
            import dash_bootstrap_components as dbc
            has_bootstrap = True
        except ImportError:
            try:
                from dash import Dash, dcc, html, Input, Output, callback_context, State
                has_bootstrap = False
            except ImportError:
                logger.error("Dash not installed. Run: pip install dash")
                print("\n💡 Install Dash: pip install dash plotly")
                return
        
        # Get initial data
        session = self.db.get_session()
        try:
            from sqlalchemy import inspect
            inspector = inspect(session.bind)
            tables = inspector.get_table_names()
            
            if 'keyword_network_snapshots' in tables:
                snapshots = session.query(KeywordNetworkSnapshot).order_by(
                    KeywordNetworkSnapshot.snapshot_date.desc()
                ).limit(10).all()
                time_window_options = [{'label': 'Day', 'value': 'day'},
                                       {'label': 'Week', 'value': 'week'},
                                       {'label': 'Month', 'value': 'month'},
                                       {'label': 'Quarter', 'value': 'quarter'}]
                default_window = 'month'
                if snapshots:
                    from collections import Counter
                    windows = [s.time_window for s in snapshots]
                    default_window = Counter(windows).most_common(1)[0][0]
            else:
                snapshots = []
                default_window = 'month'
                time_window_options = [{'label': 'Month', 'value': 'month'}]
        except Exception as e:
            logger.error(f"Error loading dashboard data: {e}")
            snapshots = []
            default_window = 'month'
            time_window_options = [{'label': 'Month', 'value': 'month'}]
        finally:
            session.close()
        
        # Initialize Dash app
        if has_bootstrap:
            app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
        else:
            app = Dash(__name__)
        
        # App layout
        app.layout = html.Div([
            html.H1("📊 AIVC Paper Trend Dashboard", 
                    style={'textAlign': 'center', 'marginBottom': 10, 'color': '#1f2937'}),
            html.P("Track AI Virtual Cell research trends through keyword analysis",
                   style={'textAlign': 'center', 'color': '#6b7280', 'marginBottom': 30}),
            
            # Controls
            html.Div([
                html.Div([
                    html.Label("Time Window:", style={'fontWeight': 'bold'}),
                    dcc.Dropdown(
                        id='time-window-dropdown',
                        options=time_window_options,
                        value=default_window,
                        clearable=False,
                        style={'marginTop': 5}
                    )
                ], style={'width': '30%', 'display': 'inline-block'}),
                
                html.Div([
                    html.Label("Metric:", style={'fontWeight': 'bold'}),
                    dcc.Dropdown(
                        id='metric-dropdown',
                        options=[
                            {'label': 'Growth Rate', 'value': 'growth_rate'},
                            {'label': 'Momentum', 'value': 'momentum'},
                            {'label': 'PageRank', 'value': 'pagerank'},
                            {'label': 'Degree', 'value': 'degree'},
                            {'label': 'Betweenness', 'value': 'betweenness'}
                        ],
                        value='growth_rate',
                        clearable=False,
                        style={'marginTop': 5}
                    )
                ], style={'width': '30%', 'display': 'inline-block', 'marginLeft': '5%'})
            ], style={'marginBottom': 30, 'padding': '20px', 'backgroundColor': '#f9fafb', 'borderRadius': '8px'}),
            
            # Trend chart
            html.H3("🔥 Trending Keywords", style={'color': '#1f2937'}),
            dcc.Graph(id='trend-chart', style={'height': '500px', 'backgroundColor': '#ffffff', 'borderRadius': '8px'}),
            
            # Network graph
            html.H3("🕸️ Keyword Network", style={'marginTop': 30, 'color': '#1f2937'}),
            dcc.Graph(id='network-graph', style={'height': '700px', 'backgroundColor': '#ffffff', 'borderRadius': '8px'}),
            
            # Data table
            html.H3("📋 Trending Keywords Table", style={'marginTop': 30, 'color': '#1f2937'}),
            html.Div(id='data-table', style={'backgroundColor': '#ffffff', 'borderRadius': '8px', 'padding': '20px'})
        ], style={'fontFamily': 'Arial, sans-serif', 'margin': '0 auto', 'maxWidth': '1400px', 'padding': '30px', 'backgroundColor': '#f3f4f6'})
        
        # Callbacks
        @app.callback(
            Output('trend-chart', 'figure'),
            Input('metric-dropdown', 'value')
        )
        def update_trend_chart(metric):
            try:
                trends = self.trend_analyzer.get_trending_keywords(limit=30)
                if not trends:
                    return go.Figure(layout=go.Layout(
                        title="No trend data available",
                        annotations=[{'text': 'Run: python run_virtualcell.py', 'showarrow': False, 'font': {'size': 14}}]
                    ))
                return self.visualizer.plot_trend_evolution(trends, metric=metric, save=False)
            except Exception as e:
                logger.error(f"Error updating trend chart: {e}")
                return go.Figure(layout=go.Layout(title=f"Error: {e}"))
        
        @app.callback(
            Output('network-graph', 'figure'),
            Input('time-window-dropdown', 'value')
        )
        def update_network(time_window):
            session = self.db.get_session()
            try:
                latest = session.query(KeywordNetworkSnapshot).order_by(
                    KeywordNetworkSnapshot.snapshot_date.desc()
                ).first()
                
                if not latest:
                    return go.Figure(layout=go.Layout(
                        title="No network data available",
                        annotations=[{'text': 'Run pipeline first', 'showarrow': False, 'font': {'size': 14}}]
                    ))
                
                snapshot = self.network_builder._load_snapshot(latest)
                
                if snapshot and snapshot.num_nodes > 0:
                    logger.info(f"Displaying network: {snapshot.num_nodes} nodes, {snapshot.num_edges} edges")
                    return self.visualizer.plot_network(snapshot.graph, save=False, top_n=min(40, snapshot.num_nodes))
                else:
                    return go.Figure(layout=go.Layout(title="Network has no nodes"))
                    
            except Exception as e:
                logger.error(f"Error updating network: {e}")
                import traceback
                traceback.print_exc()
                return go.Figure(layout=go.Layout(title=f"Error: {str(e)}"))
            finally:
                session.close()
        
        @app.callback(
            Output('data-table', 'children'),
            Input('metric-dropdown', 'value')
        )
        def update_table(metric):
            try:
                trends = self.trend_analyzer.get_trending_keywords(limit=50)
                
                if not trends:
                    return html.P("No trend data available. Run the pipeline first.", style={'color': '#6b7280', 'padding': '20px'})
                
                table = html.Table([
                    html.Thead([
                        html.Tr([
                            html.Th("Rank", style={'padding': '12px', 'textAlign': 'left', 'backgroundColor': '#f3f4f6'}),
                            html.Th("Keyword", style={'padding': '12px', 'textAlign': 'left', 'backgroundColor': '#f3f4f6'}),
                            html.Th("Growth Rate", style={'padding': '12px', 'textAlign': 'left', 'backgroundColor': '#f3f4f6'}),
                            html.Th("Momentum", style={'padding': '12px', 'textAlign': 'left', 'backgroundColor': '#f3f4f6'}),
                            html.Th("Occurrences", style={'padding': '12px', 'textAlign': 'left', 'backgroundColor': '#f3f4f6'})
                        ])
                    ]),
                    html.Tbody([
                        html.Tr([
                            html.Td(i + 1, style={'padding': '10px', 'border': '1px solid #e5e7eb'}),
                            html.Td(trend['keyword'], style={'padding': '10px', 'border': '1px solid #e5e7eb', 'fontWeight': '500'}),
                            html.Td(f"{trend.get('growth_rate', 0):.3f}", style={'padding': '10px', 'border': '1px solid #e5e7eb'}),
                            html.Td(f"{trend.get('momentum', 0):.3f}", style={'padding': '10px', 'border': '1px solid #e5e7eb'}),
                            html.Td(trend.get('occurrence_count', 0), style={'padding': '10px', 'border': '1px solid #e5e7eb'})
                        ])
                        for i, trend in enumerate(trends)
                    ])
                ], style={'width': '100%', 'borderCollapse': 'collapse', 'backgroundColor': '#ffffff'})
                
                return table
                
            except Exception as e:
                logger.error(f"Error updating table: {e}")
                return html.P(f"Error: {e}", style={'color': '#ef4444', 'padding': '20px'})
        
        # Run server
        logger.info(f"Starting dashboard on http://localhost:{port}")
        print(f"\n✅ Dashboard ready at: http://localhost:{port}")
        
        try:
            app.run(host='0.0.0.0', port=port, debug=debug, use_reloader=False)
        except AttributeError:
            app.run_server(host='0.0.0.0', port=port, debug=debug, use_reloader=False)


def create_visualizations(db_path: str = "data/papers.db"):
    """Create all visualizations from database"""
    db = DatabaseManager(f"sqlite:///{db_path}")
    visualizer = NetworkVisualizer()
    trend_analyzer = TrendAnalyzer(db)
    
    logger.info("Creating visualizations...")
    
    # Get trends
    trends = trend_analyzer.get_trending_keywords(limit=50)
    
    # Create trend plots
    for metric in ['growth_rate', 'momentum', 'pagerank', 'degree']:
        visualizer.plot_trend_evolution(trends, metric=metric)
    
    # Get latest network
    session = db.get_session()
    try:
        latest = session.query(KeywordNetworkSnapshot).order_by(
            KeywordNetworkSnapshot.snapshot_date.desc()
        ).first()
        
        if latest:
            builder = NetworkBuilder(db)
            snapshot = builder._load_snapshot(latest)
            visualizer.plot_network(snapshot.graph)
    finally:
        session.close()
    
    logger.info("✅ Visualizations complete! Check output/visualizations/")


if __name__ == "__main__":
    create_visualizations()
