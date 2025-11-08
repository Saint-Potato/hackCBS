import matplotlib

matplotlib.use("Agg")  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import io
import base64
import json
from typing import Dict, Any, List, Optional
import numpy as np
import logging

logger = logging.getLogger(__name__)


class VisualizationService:
    def __init__(self):
        # Set style for dark theme
        plt.style.use("dark_background")
        sns.set_palette("husl")

    def detect_visualization_intent(self, query: str) -> Dict[str, Any]:
        """Detect if query needs visualization"""
        viz_keywords = {
            "chart",
            "plot",
            "graph",
            "visualize",
            "show",
            "display",
            "bar chart",
            "line chart",
            "pie chart",
            "histogram",
            "scatter",
            "trends",
            "distribution",
            "comparison",
            "visualization",
        }

        query_lower = query.lower()
        needs_viz = any(keyword in query_lower for keyword in viz_keywords)

        # Determine chart type
        chart_type = "bar"  # default
        if any(
            word in query_lower for word in ["line", "trend", "over time", "timeline"]
        ):
            chart_type = "line"
        elif any(
            word in query_lower for word in ["pie", "proportion", "percentage", "share"]
        ):
            chart_type = "pie"
        elif any(
            word in query_lower for word in ["scatter", "correlation", "relationship"]
        ):
            chart_type = "scatter"
        elif any(word in query_lower for word in ["histogram", "distribution"]):
            chart_type = "histogram"

        return {
            "needs_visualization": needs_viz,
            "chart_type": chart_type,
            "confidence": 0.8 if needs_viz else 0.2,
        }

    def generate_chart(
        self, data: List[Dict], chart_type: str, title: str = "Data Visualization"
    ) -> str:
        """Generate chart and return base64 encoded image"""
        try:
            if not data or len(data) == 0:
                return self._create_empty_chart("No data available for visualization")

            df = pd.DataFrame(data)

            if df.empty:
                return self._create_empty_chart("Empty dataset")

            # Create figure with dark theme
            plt.figure(figsize=(12, 8))
            plt.style.use("dark_background")

            if chart_type == "bar":
                self._create_bar_chart(df, title)
            elif chart_type == "line":
                self._create_line_chart(df, title)
            elif chart_type == "pie":
                self._create_pie_chart(df, title)
            elif chart_type == "scatter":
                self._create_scatter_chart(df, title)
            elif chart_type == "histogram":
                self._create_histogram(df, title)
            else:
                self._create_bar_chart(df, title)  # fallback

            return self._save_to_base64()

        except Exception as e:
            logger.error(f"Chart generation error: {e}")
            return self._create_empty_chart(f"Error generating chart: {str(e)}")

    def _create_bar_chart(self, df: pd.DataFrame, title: str):
        """Create bar chart"""
        if len(df.columns) >= 2:
            x_col, y_col = df.columns[0], df.columns[1]
            # Convert x values to strings for better display
            x_values = df[x_col].astype(str)
            y_values = pd.to_numeric(df[y_col], errors="coerce")

            plt.bar(x_values, y_values, color="#64b5f6", alpha=0.8)
            plt.xlabel(str(x_col))
            plt.ylabel(str(y_col))
        else:
            # Single column - value counts
            value_counts = df.iloc[:, 0].value_counts().head(20)
            plt.bar(
                range(len(value_counts)),
                value_counts.values,
                color="#64b5f6",
                alpha=0.8,
            )
            plt.xticks(
                range(len(value_counts)), value_counts.index.astype(str), rotation=45
            )
            plt.ylabel("Count")

        plt.title(title, fontsize=16, pad=20, color="white")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()

    def _create_line_chart(self, df: pd.DataFrame, title: str):
        """Create line chart"""
        if len(df.columns) >= 2:
            x_col, y_col = df.columns[0], df.columns[1]
            x_values = df[x_col]
            y_values = pd.to_numeric(df[y_col], errors="coerce")

            plt.plot(x_values, y_values, marker="o", linewidth=2, color="#81c784")
            plt.xlabel(str(x_col))
            plt.ylabel(str(y_col))

        plt.title(title, fontsize=16, pad=20, color="white")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

    def _create_pie_chart(self, df: pd.DataFrame, title: str):
        """Create pie chart"""
        if len(df.columns) >= 2:
            labels = df.iloc[:, 0].astype(str)
            values = pd.to_numeric(df.iloc[:, 1], errors="coerce")
        else:
            value_counts = df.iloc[:, 0].value_counts().head(10)
            labels = value_counts.index.astype(str)
            values = value_counts.values

        colors = plt.cm.Set3(np.linspace(0, 1, len(labels)))
        plt.pie(values, labels=labels, autopct="%1.1f%%", colors=colors, startangle=90)
        plt.title(title, fontsize=16, pad=20, color="white")
        plt.axis("equal")

    def _create_scatter_chart(self, df: pd.DataFrame, title: str):
        """Create scatter plot"""
        if len(df.columns) >= 2:
            x_col, y_col = df.columns[0], df.columns[1]
            x_values = pd.to_numeric(df[x_col], errors="coerce")
            y_values = pd.to_numeric(df[y_col], errors="coerce")

            plt.scatter(x_values, y_values, alpha=0.7, color="#f06292", s=60)
            plt.xlabel(str(x_col))
            plt.ylabel(str(y_col))

        plt.title(title, fontsize=16, pad=20, color="white")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

    def _create_histogram(self, df: pd.DataFrame, title: str):
        """Create histogram"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            data = df[numeric_cols[0]].dropna()
            plt.hist(data, bins=20, color="#ffb74d", alpha=0.8, edgecolor="black")
            plt.xlabel(str(numeric_cols[0]))
            plt.ylabel("Frequency")

        plt.title(title, fontsize=16, pad=20, color="white")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

    def _create_empty_chart(self, message: str) -> str:
        """Create empty chart with message"""
        plt.figure(figsize=(10, 6))
        plt.text(
            0.5,
            0.5,
            message,
            ha="center",
            va="center",
            fontsize=16,
            color="white",
            wrap=True,
        )
        plt.xlim(0, 1)
        plt.ylim(0, 1)
        plt.axis("off")
        plt.tight_layout()
        return self._save_to_base64()

    def _save_to_base64(self) -> str:
        """Convert plot to base64 string"""
        buffer = io.BytesIO()
        plt.savefig(
            buffer,
            format="png",
            dpi=150,
            bbox_inches="tight",
            facecolor="#1e1e1e",
            edgecolor="none",
            pad_inches=0.2,
        )
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        plt.close()
        return image_base64
