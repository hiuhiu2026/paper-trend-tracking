"""
Visualization Module for Paper Trend Tracking

Creates:
- Keyword network graphs
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
    """Visualize keyword co-occurrence networks"""
    
    def __init__(self, output_dir: str = "output/visualizations"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def plot_network(
        self,
        graph: nx.Graph,
        title: str = "Keyword Co-occurrence Network",
        top_n: int = 50,
        save: bool = True,
        show: bool = False
    ) -> str:
        """
        Create network visualization
        
        Args:
            graph: NetworkX graph
            title: Plot title
            top_n: Show only top N nodes by degree
            save: Save to file
            show: Show in browser
        
        Returns:
            Path to saved HTML file
        """
        # Get top nodes by degree
        degrees = dict(graph.degree())
        top_nodes = sorted(degrees.keys(), key=lambda x: degrees[x], reverse=True)[:top_n]
        
        # Create subgraph
        G = graph.subgraph(top_nodes)
        
        # Compute layout using spring layout
        pos = nx.spring_layout(G, k=2, iterations=50, seed=42)
        
        # Extract node positions
        node_x = [pos[node][0] for node in G.nodes()]
        node_y = [pos[node][1] for node in G.nodes()]
        node_labels = list(G.nodes())
        node_sizes = [degrees[node] * 100 for node in G.nodes()]
        
        # Create node trace
        node_trace = go.Scatter(
            x=node_x,
            y=node_y,
            mode='markers+text',
            hoverinfo='text',
            text=node_labels,
            textposition="middle center",
            textfont=dict(size=10, color='white'),
            marker=dict(
                showscale=True,
                colorscale='Viridis',
                reversescale=True,
                color=node_sizes,
                size=node_sizes,
                colorbar=dict(
                    thickness=15,
                    title=dict(text='Degree', side='right'),
                    xanchor='left',
                ),
                line_width=2
            ),
            name='Keywords'
        )
        
        # Create edge traces
        edge_traces = []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            
            edge_trace = go.Scatter(
                x=[x0, x1, None],
                y=[y0, y1, None],
                mode='lines',
                line=dict(width=1, color='#888'),
                hoverinfo='none',
                showlegend=False
            )
            edge_traces.append(edge_trace)
        
        # Create figure
        fig = go.Figure(
            data=edge_traces + [node_trace],
            layout=go.Layout(
                title=dict(text=title, x=0.5, y=0.95),
                showlegend=False,
                hovermode='closest',
                margin=dict(b=20, l=5, r=5, t=40),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                plot_bgcolor='white',
                width=1000,
                height=800
            )
        )
        
        # Save or show
        if save:
            output_path = self.output_dir / f"network_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            plotly_plot(fig, filename=str(output_path), auto_open=show)
            logger.info(f"Network plot saved: {output_path}")
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
        Plot trend evolution over time
        
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
        
        fig = go.Figure(data=[
            go.Bar(
                x=keywords,
                y=values,
                marker_color='rgb(55, 83, 109)',
                hovertemplate='<b>%{x}</b><br>' + metric + ': %{y:.3f}<extra></extra>'
            )
        ])
        
        fig.update_layout(
            title=f"Top Keywords by {metric.replace('_', ' ').title()}",
            xaxis_title="Keyword",
            yaxis_title=metric.replace('_', ' ').title(),
            showlegend=False,
            hovermode='x unified',
            xaxis=dict(tickangle=-45),
            height=500,
            width=1000
        )
        
        if save:
            output_path = self.output_dir / f"trends_{metric}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            plotly_plot(fig, filename=str(output_path), auto_open=show)
            logger.info(f"Trend plot saved: {output_path}")
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
        # Ensure db_path is absolute
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
                print("💡 Optional (better UI): pip install dash-bootstrap-components")
                return
        
        # Initialize Dash app
        app = dash.Dash(__name__)
        
        # Get initial data
        session = self.db.get_session()
        try:
            # Get latest trends
            trends = self.trend_analyzer.get_trending_keywords(limit=50)
            
            # Get snapshot dates
            snapshots = session.query(KeywordNetworkSnapshot).order_by(
                KeywordNetworkSnapshot.snapshot_date.desc()
            ).all()
            snapshot_dates = [s.snapshot_date.strftime('%Y-%m-%d') for s in snapshots]
        finally:
            session.close()
        
        # Initialize Dash app
        if has_bootstrap:
            app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
        else:
            app = Dash(__name__)
        
        # Get initial data for layout
        session = self.db.get_session()
        try:
            # Check if tables exist and have data
            from sqlalchemy import inspect
            inspector = inspect(session.bind)
            tables = inspector.get_table_names()
            
            logger.info(f"Dashboard database tables: {tables}")
            
            if 'keyword_network_snapshots' in tables:
                snapshots = session.query(KeywordNetworkSnapshot).order_by(
                    KeywordNetworkSnapshot.snapshot_date.desc()
                ).limit(10).all()
                
                logger.info(f"Found {len(snapshots)} snapshots")
                
                time_window_options = [{'label': 'Day', 'value': 'day'},
                                       {'label': 'Week', 'value': 'week'},
                                       {'label': 'Month', 'value': 'month'},
                                       {'label': 'Quarter', 'value': 'quarter'}]
                
                default_window = 'month'
                if snapshots:
                    from collections import Counter
                    windows = [s.time_window for s in snapshots]
                    default_window = Counter(windows).most_common(1)[0][0]
                    logger.info(f"Default time window: {default_window}")
            else:
                logger.warning("No keyword_network_snapshots table found")
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
        
        # App layout - simple version without tabs (more compatible)
        app.layout = html.Div([
            html.H1("📊 Paper Trend Tracking Dashboard", 
                    style={'textAlign': 'center', 'marginBottom': 10}),
            html.P("Track research trends through keyword network evolution",
                   style={'textAlign': 'center', 'color': '#666', 'marginBottom': 30}),
            
            # Controls
            html.Div([
                html.Div([
                    html.Label("Time Window:"),
                    dcc.Dropdown(
                        id='time-window-dropdown',
                        options=time_window_options,
                        value=default_window,
                        clearable=False
                    )
                ], style={'width': '30%', 'display': 'inline-block'}),
                
                html.Div([
                    html.Label("Metric: "),
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
                        clearable=False
                    )
                ], style={'width': '30%', 'display': 'inline-block', 'marginLeft': '5%'})
            ], style={'marginBottom': 30}),
            
            # Trend chart
            html.H3("Trending Keywords"),
            dcc.Graph(id='trend-chart', style={'height': '500px'}),
            
            # Network graph
            html.H3("Keyword Network (Latest Snapshot)", style={'marginTop': 30}),
            dcc.Graph(id='network-graph', style={'height': '600px'}),
            
            # Data table
            html.H3("Trending Keywords Table", style={'marginTop': 30}),
            html.Div(id='data-table')
        ], style={'fontFamily': 'Arial, sans-serif', 'margin': '0 auto', 'maxWidth': '1200px', 'padding': '20px'})
        
        # Callbacks
        @app.callback(
            Output('trend-chart', 'figure'),
            Input('metric-dropdown', 'value')
        )
        def update_trend_chart(metric):
            try:
                trends = self.trend_analyzer.get_trending_keywords(limit=30)
                if not trends:
                    # Try to get any data
                    logger.debug("No trends found, showing empty chart")
                    return go.Figure(layout=go.Layout(
                        title="No trend data available - Run pipeline first",
                        xaxis={'visible': False},
                        yaxis={'visible': False},
                        annotations=[{
                            'text': "Run: python run_virtualcell.py",
                            'xref': 'paper', 'yref': 'paper',
                            'showarrow': False, 'font': {'size': 14}
                        }]
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
            # Get latest snapshot
            session = self.db.get_session()
            try:
                # Try to get any snapshot first
                latest = session.query(KeywordNetworkSnapshot).order_by(
                    KeywordNetworkSnapshot.snapshot_date.desc()
                ).first()
                
                if not latest:
                    logger.debug("No network snapshots found")
                    return go.Figure(layout=go.Layout(
                        title="No network data available - Run pipeline first",
                        xaxis={'visible': False},
                        yaxis={'visible': False},
                        annotations=[{
                            'text': "Run: python run_virtualcell.py --network",
                            'xref': 'paper', 'yref': 'paper',
                            'showarrow': False, 'font': {'size': 14}
                        }]
                    ))
                
                # Try to get snapshot with selected time window
                snapshot_data = session.query(KeywordNetworkSnapshot).filter(
                    KeywordNetworkSnapshot.time_window == time_window
                ).order_by(KeywordNetworkSnapshot.snapshot_date.desc()).first()
                
                # Fallback to any snapshot if time window not found
                if not snapshot_data:
                    logger.debug(f"No snapshots for {time_window}, using latest")
                    snapshot_data = latest
                
                snapshot = self.network_builder._load_snapshot(snapshot_data)
                
                if snapshot and snapshot.num_nodes > 0:
                    return self.visualizer.plot_network(snapshot.graph, save=False)
                else:
                    return go.Figure(layout=go.Layout(title="Empty network"))
                    
            except Exception as e:
                logger.error(f"Error updating network: {e}")
                return go.Figure(layout=go.Layout(title=f"Error: {e}"))
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
                    return html.Div([
                        html.P("No trend data available", style={'color': '#666'}),
                        html.P("Run the pipeline first:", style={'color': '#999', 'fontSize': '12px'}),
                        html.Code("python run_virtualcell.py", style={'backgroundColor': '#f4f4f4', 'padding': '5px'})
                    ], style={'padding': '20px', 'textAlign': 'center'})
                
                table = html.Table([
                    html.Thead([
                        html.Tr([
                            html.Th("Rank"),
                            html.Th("Keyword"),
                            html.Th("Growth Rate"),
                            html.Th("Momentum"),
                            html.Th("Occurrences")
                        ])
                    ]),
                    html.Tbody([
                        html.Tr([
                            html.Td(i + 1),
                            html.Td(trend['keyword']),
                            html.Td(f"{trend.get('growth_rate', 0):.3f}"),
                            html.Td(f"{trend.get('momentum', 0):.3f}"),
                            html.Td(trend.get('occurrence_count', 0))
                        ])
                        for i, trend in enumerate(trends)
                    ])
                ], style={'width': '100%', 'borderCollapse': 'collapse'})
                
                # Add styling
                for row in table.children[1].children:
                    for cell in row.children:
                        cell.style['padding'] = '8px'
                        cell.style['border'] = '1px solid #ddd'
                
                return table
                
            except Exception as e:
                logger.error(f"Error updating table: {e}")
                return html.P(f"Error: {e}")
        
        # Run server (Dash 3.x uses app.run, Dash 2.x uses app.run_server)
        logger.info(f"Starting dashboard on http://localhost:{port}")
        print(f"\n✅ Dashboard ready at: http://localhost:{port}")
        print(f"   Press Ctrl+C to stop\n")
        
        # Try Dash 3.x API first, fallback to 2.x
        try:
            app.run(host='0.0.0.0', port=port, debug=debug)
        except AttributeError:
            # Dash 2.x
            app.run_server(host='0.0.0.0', port=port, debug=debug)


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
    
    logger.info("Visualizations complete! Check output/visualizations/")


if __name__ == "__main__":
    # Create static visualizations
    create_visualizations()
    
    # Or run interactive dashboard
    # dashboard = TrendDashboard()
    # dashboard.create_dashboard(port=8050)
