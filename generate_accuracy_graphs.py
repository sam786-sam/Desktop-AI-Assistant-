"""
Jarvis Accuracy Graph Generator
Creates beautiful visualizations using matplotlib and generates HTML reports
"""

import os
import json
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Circle, Rectangle, Polygon
import numpy as np
from pathlib import Path

class AccuracyGraphGenerator:
    """Generate various types of graphs for accuracy visualization"""
    
    def __init__(self, results=None):
        self.results = results or {}
        self.save_dir = os.path.join(os.path.dirname(__file__), "Data", "Graphs")
        os.makedirs(self.save_dir, exist_ok=True)
        
        # Set style
        plt.style.use('dark_background')
        self.colors = {
            'green': '#00ff88',
            'yellow': '#ffcc00',
            'red': '#ff4444',
            'blue': '#00ccff',
            'purple': '#cc66ff',
            'orange': '#ff9933'
        }
    
    def load_results(self, filepath):
        """Load results from JSON file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.results = json.load(f)
            print(f"✅ Loaded results from {filepath}")
            return True
        except Exception as e:
            print(f"❌ Error loading results: {e}")
            return False
    
    def create_bar_chart(self, save=True):
        """Create horizontal bar chart for category accuracy"""
        if not self.results.get('categories'):
            print("❌ No category data available")
            return None
        
        fig, ax = plt.subplots(figsize=(8, 5))  # Reduced further
        
        categories = list(self.results['categories'].keys())
        accuracies = [self.results['categories'][cat].get('accuracy', 0) * 100 
                     for cat in categories]
        
        # Color based on accuracy
        colors = []
        for acc in accuracies:
            if acc >= 90:
                colors.append(self.colors['green'])
            elif acc >= 70:
                colors.append(self.colors['yellow'])
            else:
                colors.append(self.colors['red'])
        
        # Create horizontal bars
        y_pos = np.arange(len(categories))
        bars = ax.barh(y_pos, accuracies, color=colors, alpha=0.8)
        
        # Add value labels
        for i, (bar, acc) in enumerate(zip(bars, accuracies)):
            width = bar.get_width()
            label_x = width + 2
            ax.text(label_x, bar.get_y() + bar.get_height()/2, 
                   f'{acc:.1f}%', ha='left', va='center', 
                   fontsize=11, fontweight='bold', color='white')
        
        ax.set_xlabel('Accuracy (%)', fontsize=12, color='white')
        ax.set_ylabel('Category', fontsize=12, color='white')
        ax.set_title('Jarvis AI - Category-wise Accuracy Analysis', 
                    fontsize=14, fontweight='bold', color=self.colors['blue'])
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels([cat.replace('_', ' ').title() for cat in categories])
        ax.set_xlim(0, 105)
        
        # Add grid
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # Add threshold lines
        ax.axvline(x=90, color=self.colors['green'], linestyle='--', 
                  alpha=0.5, label='Excellent (90%)')
        ax.axvline(x=70, color=self.colors['yellow'], linestyle='--', 
                  alpha=0.5, label='Good (70%)')
        
        plt.tight_layout()
        
        return fig
    
    def create_pie_chart(self, save=True):
        """Create pie chart showing accuracy distribution"""
        if not self.results.get('categories'):
            print("❌ No category data available")
            return None
        
        fig, ax = plt.subplots(figsize=(7, 7))  # Reduced further
        
        categories = list(self.results['categories'].keys())
        accuracies = [self.results['categories'][cat].get('accuracy', 0) * 100 
                     for cat in categories]
        
        # Weights for weighted pie chart
        weights = {
            "microphone_system": 0.20,
            "assistant_status": 0.20,
            "response_times": 0.15,
            "module_imports": 0.25,
            "file_operations": 0.20
        }
        
        # Calculate weighted contributions
        weighted_acc = []
        for cat, acc in zip(categories, accuracies):
            weight = weights.get(cat, 0.2)
            weighted_acc.append(acc * weight)
        
        # Colors
        colors_list = []
        for acc in accuracies:
            if acc >= 90:
                colors_list.append(self.colors['green'])
            elif acc >= 70:
                colors_list.append(self.colors['yellow'])
            else:
                colors_list.append(self.colors['red'])
        
        # Create pie chart
        wedges, texts, autotexts = ax.pie(
            weighted_acc, 
            labels=[cat.replace('_', ' ').title() for cat in categories],
            colors=colors_list,
            autopct=lambda pct: f'{pct:.1f}%',
            startangle=90,
            pctdistance=0.75,
            textprops={'fontsize': 10, 'color': 'white'}
        )
        
        # Make percentage text bold
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        ax.set_title('Weighted Accuracy Distribution', 
                    fontsize=14, fontweight='bold', color='white', pad=20)
        
        # Add center circle for donut effect
        centre_circle = plt.Circle((0, 0), 0.50, fc='#1a1a1a')
        ax.add_artist(centre_circle)
        
        # Add overall accuracy in center
        overall = self.results.get('overall_accuracy', 0) * 100
        ax.text(0, 0, f'{overall:.1f}%', ha='center', va='center',
               fontsize=20, fontweight='bold', color=self.colors['blue'])
        ax.text(0, -0.3, 'Overall', ha='center', va='center',
               fontsize=12, color='white')
        
        plt.tight_layout()
        
        return fig
    
    def create_gauge_chart(self, save=True):
        """Create gauge/meter chart for overall accuracy"""
        overall = self.results.get('overall_accuracy', 0) * 100
        
        fig, ax = plt.subplots(figsize=(7, 5), subplot_kw={'projection': 'polar'})
        
        # Gauge parameters
        max_angle = 180  # Semi-circle
        start_angle = 90  # Start from top
        
        # Determine color based on accuracy
        if overall >= 90:
            gauge_color = self.colors['green']
            rating = 'EXCELLENT'
        elif overall >= 80:
            gauge_color = self.colors['green']
            rating = 'GOOD'
        elif overall >= 70:
            gauge_color = self.colors['yellow']
            rating = 'FAIR'
        elif overall >= 60:
            gauge_color = self.colors['orange']
            rating = 'NEEDS IMPROVEMENT'
        else:
            gauge_color = self.colors['red']
            rating = 'CRITICAL'
        
        # Draw background arc (full scale)
        ax.bar(x=np.deg2rad(start_angle), height=0.3, width=np.deg2rad(max_angle),
              bottom=0.7, color='#333333', alpha=0.5)
        
        # Draw filled portion (actual accuracy)
        filled_angle = (overall / 100) * max_angle
        ax.bar(x=np.deg2rad(start_angle), height=0.3, width=np.deg2rad(filled_angle),
              bottom=0.7, color=gauge_color, alpha=0.8)
        
        # Remove radial grid and labels
        ax.set_yticks([])
        ax.set_xticks(np.deg2rad(range(start_angle, start_angle + max_angle + 1, 10)))
        ax.set_xticklabels([])
        
        # Add percentage labels
        angle_positions = [start_angle, start_angle + max_angle/2, start_angle + max_angle]
        percentage_labels = ['0%', '50%', '100%']
        for angle, label in zip(angle_positions, percentage_labels):
            ax.text(np.deg2rad(angle), 0.5, label, ha='center', va='center',
                   fontsize=12, color='white', fontweight='bold')
        
        # Add needle
        needle_angle = np.deg2rad(start_angle + filled_angle)
        ax.plot([needle_angle, needle_angle], [0.7, 1.0], 'r-', linewidth=3)
        
        # Add center circle
        circle = Circle((0, 0), 0.15, transform=ax.transData._b, 
                       fc='#1a1a1a', ec='white', linewidth=2)
        ax.add_patch(circle)
        
        # Add title and value
        ax.set_title(f'Overall System Accuracy\n{overall:.1f}% - {rating}',
                    fontsize=16, fontweight='bold', color='white', pad=20)
        
        plt.tight_layout()
        
        return fig
    
    def create_radar_chart(self, save=True):
        """Create radar/spider chart for multi-dimensional comparison"""
        if not self.results.get('categories'):
            print("❌ No category data available")
            return None
        
        fig, ax = plt.subplots(figsize=(7, 7), subplot_kw={'projection': 'polar'})
        
        categories = list(self.results['categories'].keys())
        accuracies = [self.results['categories'][cat].get('accuracy', 0) * 100 
                     for cat in categories]
        
        # Number of variables
        num_vars = len(categories)
        
        # Compute angle for each category
        angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
        angles += angles[:1]  # Complete the loop
        
        # Make data circular
        accuracies += accuracies[:1]
        
        # Draw the accuracy polygon
        ax.plot(angles, accuracies, 'o-', linewidth=2, color=self.colors['blue'])
        ax.fill(angles, accuracies, alpha=0.25, color=self.colors['blue'])
        
        # Add category labels
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels([cat.replace('_', ' ').title() for cat in categories],
                          fontsize=10, color='white')
        
        # Add grid and limits
        ax.set_ylim(0, 100)
        ax.set_thetagrids(np.degrees(angles[:-1]), 
                         labels=[cat.replace('_', ' ').title() for cat in categories])
        
        # Customize grid
        ax.grid(True, linestyle='--', alpha=0.5)
        
        # Add title
        plt.title('Jarvis AI - Multi-Dimensional Accuracy Analysis',
                 fontsize=14, fontweight='bold', color='white', pad=20)
        
        plt.tight_layout()
        
        return fig
    
    def create_comparison_chart(self, save=True):
        """Create comparison chart: Expected vs Actual"""
        if not self.results.get('categories'):
            print("❌ No category data available")
            return None
        
        expectations = {
            "microphone_system": 95,
            "assistant_status": 95,
            "response_times": 85,
            "module_imports": 100,
            "file_operations": 98
        }
        
        fig, ax = plt.subplots(figsize=(8, 5))
        
        categories = list(self.results['categories'].keys())
        actual = [self.results['categories'][cat].get('accuracy', 0) * 100 
                 for cat in categories]
        expected = [expectations.get(cat, 90) for cat in categories]
        
        x = np.arange(len(categories))
        width = 0.35
        
        # Create bars
        rects1 = ax.bar(x - width/2, expected, width, label='Expected',
                       color=self.colors['orange'], alpha=0.7)
        rects2 = ax.bar(x + width/2, actual, width, label='Actual',
                       color=self.colors['green'], alpha=0.7)
        
        # Add labels
        ax.set_ylabel('Accuracy (%)', fontsize=12, color='white')
        ax.set_xlabel('Category', fontsize=12, color='white')
        ax.set_title('Expected vs Actual Performance Comparison',
                    fontsize=14, fontweight='bold', color='white')
        ax.set_xticks(x)
        ax.set_xticklabels([cat.replace('_', ' ').title() for cat in categories],
                          rotation=15)
        ax.legend(fontsize=11)
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # Add value labels on bars
        for rect in rects1 + rects2:
            height = rect.get_height()
            ax.annotate(f'{height:.0f}%',
                       xy=(rect.get_x() + rect.get_width() / 2, height),
                       xytext=(0, 3),
                       textcoords="offset points",
                       ha='center', va='bottom', fontsize=9,
                       color='white', fontweight='bold')
        
        plt.tight_layout()
        
        return fig
    
    def create_all_graphs(self):
        """Generate all types of graphs"""
        print("\n🎨 Generating all accuracy graphs...\n")
        
        graphs = []
        
        # Generate each type
        print("1️⃣ Creating Bar Chart...")
        fig1 = self.create_bar_chart()
        if fig1:
            filename = f"category_accuracy_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            filepath = os.path.join(self.save_dir, filename)
            fig1.savefig(filepath, dpi=80, facecolor='#1a1a1a', bbox_inches='tight')  # Reduced to 80 DPI
            graphs.append(("Category Bar Chart", filepath))
        
        print("2️⃣ Creating Pie Chart...")
        fig2 = self.create_pie_chart()
        if fig2:
            filename = f"pie_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            filepath = os.path.join(self.save_dir, filename)
            fig2.savefig(filepath, dpi=80, facecolor='#1a1a1a', bbox_inches='tight')  # Reduced to 80 DPI
            graphs.append(("Accuracy Distribution Pie Chart", filepath))
        
        print("3️⃣ Creating Gauge Chart...")
        fig3 = self.create_gauge_chart()
        if fig3:
            filename = f"gauge_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            filepath = os.path.join(self.save_dir, filename)
            fig3.savefig(filepath, dpi=80, facecolor='#1a1a1a', bbox_inches='tight')  # Reduced to 80 DPI
            graphs.append(("Overall Accuracy Gauge", filepath))
        
        print("4️⃣ Creating Radar Chart...")
        fig4 = self.create_radar_chart()
        if fig4:
            filename = f"radar_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            filepath = os.path.join(self.save_dir, filename)
            fig4.savefig(filepath, dpi=80, facecolor='#1a1a1a', bbox_inches='tight')  # Reduced to 80 DPI
            graphs.append(("Multi-Dimensional Radar Chart", filepath))
        
        print("5️⃣ Creating Comparison Chart...")
        fig5 = self.create_comparison_chart()
        if fig5:
            filename = f"comparison_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            filepath = os.path.join(self.save_dir, filename)
            fig5.savefig(filepath, dpi=80, facecolor='#1a1a1a', bbox_inches='tight')  # Reduced to 80 DPI
            graphs.append(("Expected vs Actual Comparison", filepath))
        
        print(f"\n✅ Generated {len(graphs)} graphs successfully!")
        print(f"📁 Saved to: {self.save_dir}")
        
        return graphs
    
    def create_html_report(self, graphs=None):
        """Create an interactive HTML report with all graphs"""
        if graphs is None:
            # Find latest graphs
            graph_files = []
            for root, dirs, files in os.walk(self.save_dir):
                for file in files:
                    if file.endswith('.png') and datetime.now().strftime('%Y%m%d') in file:
                        graph_files.append(os.path.join(root, file))
            graph_files.sort(reverse=True)
            graphs = [(f"Graph {i+1}", f) for i, f in enumerate(graph_files[:5])]
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jarvis AI - Accuracy Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: white;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        h1 {{
            text-align: center;
            color: #00ff88;
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 0 0 20px rgba(0, 255, 136, 0.5);
        }}
        .subtitle {{
            text-align: center;
            color: #00ccff;
            font-size: 1.2em;
            margin-bottom: 40px;
        }}
        .summary-box {{
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 20px;
            margin: 20px 0;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }}
        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .metric-card {{
            background: rgba(0, 255, 136, 0.1);
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            border: 2px solid rgba(0, 255, 136, 0.3);
            transition: transform 0.3s ease;
        }}
        .metric-card:hover {{
            transform: translateY(-5px);
        }}
        .metric-value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #00ff88;
        }}
        .metric-label {{
            font-size: 1.1em;
            color: #cccccc;
            margin-top: 10px;
        }}
        .graph-container {{
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 20px;
            margin: 30px 0;
            text-align: center;
        }}
        .graph-container img {{
            max-width: 100%;
            height: auto;
            border-radius: 10px;
            box-shadow: 0 5px 20px rgba(0, 0, 0, 0.5);
        }}
        .footer {{
            text-align: center;
            margin-top: 50px;
            padding: 20px;
            color: #888;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Jarvis AI Accuracy Report</h1>
        <div class="subtitle">Comprehensive Performance Analysis</div>
        
        <div class="summary-box">
            <h2 style="color: #00ff88;">📊 Executive Summary</h2>
            <p><strong>Report Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Overall System Accuracy:</strong> <span style="color: #00ff88; font-size: 1.5em; font-weight: bold;">{self.results.get('overall_accuracy', 0) * 100:.2f}%</span></p>
            <p><strong>Categories Tested:</strong> {len(self.results.get('categories', {}))}</p>
        </div>
        
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-value">{self.results.get('overall_accuracy', 0) * 100:.1f}%</div>
                <div class="metric-label">Overall Accuracy</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{len(self.results.get('categories', {}))}</div>
                <div class="metric-label">Categories</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{len(graphs)}</div>
                <div class="metric-label">Visualizations</div>
            </div>
        </div>
        
        <h2 style="color: #00ccff; margin-top: 40px;">📈 Visual Analytics</h2>
"""
        
        # Add each graph
        for name, filepath in graphs:
            if os.path.exists(filepath):
                # Convert to relative path
                rel_path = os.path.basename(filepath)
                html_content += f"""
        <div class="graph-container">
            <h3 style="color: #ff9933;">{name}</h3>
            <img src="{rel_path}" alt="{name}">
        </div>
"""
        
        html_content += """
        <div class="footer">
            <p>Jarvis AI Accuracy Calculator | Generated with Python & Matplotlib</p>
            <p>Advanced Performance Monitoring System</p>
        </div>
    </div>
</body>
</html>
"""
        
        # Save HTML
        html_filename = os.path.join(self.save_dir, f"accuracy_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
        with open(html_filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"\n✅ HTML report saved to: {html_filename}")
        print(f"🌐 Opening in browser...")
        
        # Open in browser
        import webbrowser
        webbrowser.open(f"file:///{os.path.abspath(html_filename)}")
        
        return html_filename


def main():
    """Main function to generate graphs"""
    print("="*80)
    print("🎨 JARVIS ACCURACY GRAPH GENERATOR")
    print("="*80)
    
    generator = AccuracyGraphGenerator()
    
    # Try to load latest results
    data_dir = os.path.join(os.path.dirname(__file__), "Data")
    json_files = [f for f in os.listdir(data_dir) if f.startswith('detailed_accuracy_') and f.endswith('.json')]
    
    if json_files:
        latest_json = sorted(json_files)[-1]
        json_path = os.path.join(data_dir, latest_json)
        
        if generator.load_results(json_path):
            print("\n✅ Using latest accuracy results\n")
            
            # Generate all graphs
            graphs = generator.create_all_graphs()
            
            # Create HTML report
            html_file = generator.create_html_report(graphs)
            
            print("\n" + "="*80)
            print("✨ All graphs generated successfully!")
            print(f"📁 Graphs location: {generator.save_dir}")
            print(f"🌐 HTML Report: {html_file}")
            print("="*80)
        else:
            print("\n❌ Could not load results. Please run accuracy calculator first.")
    else:
        print("\n⚠️ No accuracy results found. Please run advanced_accuracy_calculator.py first.")


if __name__ == "__main__":
    main()
