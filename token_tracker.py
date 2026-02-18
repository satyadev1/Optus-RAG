"""
Token Usage Tracking System for Claude API
Tracks all API calls with detailed metrics for auditing and cost analysis
"""

import sqlite3
from datetime import datetime
import json
import os

class TokenTracker:
    def __init__(self, db_path="token_usage.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize SQLite database for token tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS token_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                model TEXT NOT NULL,
                question TEXT NOT NULL,
                collection TEXT NOT NULL,
                input_tokens INTEGER NOT NULL,
                output_tokens INTEGER NOT NULL,
                total_tokens INTEGER NOT NULL,
                cost_usd REAL NOT NULL,
                documents_retrieved INTEGER NOT NULL,
                response_time_ms INTEGER NOT NULL,
                user_id TEXT DEFAULT 'default',
                session_id TEXT,
                success BOOLEAN DEFAULT 1
            )
        ''')

        conn.commit()
        conn.close()
        print(f"[TokenTracker] Database initialized: {self.db_path}")

    def track_usage(self, model, question, collection, input_tokens, output_tokens,
                   documents_retrieved, response_time_ms, session_id=None, success=True):
        """
        Track a single API call

        Args:
            model: Claude model used (e.g., "claude-sonnet-4-5")
            question: User's question
            collection: Collection(s) searched
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            documents_retrieved: Number of documents retrieved from Milvus
            response_time_ms: Response time in milliseconds
            session_id: Optional session identifier
            success: Whether the request was successful
        """
        total_tokens = input_tokens + output_tokens
        cost = self.calculate_cost(model, input_tokens, output_tokens)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO token_usage
            (timestamp, model, question, collection, input_tokens, output_tokens,
             total_tokens, cost_usd, documents_retrieved, response_time_ms, session_id, success)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            model,
            question[:500],  # Truncate long questions
            collection,
            input_tokens,
            output_tokens,
            total_tokens,
            cost,
            documents_retrieved,
            response_time_ms,
            session_id,
            success
        ))

        conn.commit()
        conn.close()

        print(f"[TokenTracker] Tracked: {total_tokens} tokens, ${cost:.4f}")
        return {
            'total_tokens': total_tokens,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'cost': cost
        }

    def calculate_cost(self, model, input_tokens, output_tokens):
        """
        Calculate cost based on Claude pricing

        Pricing (as of 2024):
        - Claude Sonnet 4.5: $3 per MTok input, $15 per MTok output
        - Claude Opus: $15 per MTok input, $75 per MTok output
        - Claude Haiku: $0.25 per MTok input, $1.25 per MTok output
        """
        pricing = {
            'claude-sonnet-4-5': {'input': 3.0, 'output': 15.0},
            'claude-opus-4': {'input': 15.0, 'output': 75.0},
            'claude-haiku-4': {'input': 0.25, 'output': 1.25},
        }

        # Default to Sonnet pricing if model not found
        rates = pricing.get(model, pricing['claude-sonnet-4-5'])

        input_cost = (input_tokens / 1_000_000) * rates['input']
        output_cost = (output_tokens / 1_000_000) * rates['output']

        return input_cost + output_cost

    def get_usage_stats(self, period='all', limit=100):
        """
        Get usage statistics

        Args:
            period: 'today', 'week', 'month', 'all'
            limit: Maximum number of records to return

        Returns:
            dict with statistics and recent queries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Build time filter
        time_filter = ""
        if period == 'today':
            time_filter = "WHERE date(timestamp) = date('now')"
        elif period == 'week':
            time_filter = "WHERE timestamp >= datetime('now', '-7 days')"
        elif period == 'month':
            time_filter = "WHERE timestamp >= datetime('now', '-30 days')"

        # Get summary stats
        cursor.execute(f'''
            SELECT
                COUNT(*) as total_requests,
                SUM(input_tokens) as total_input_tokens,
                SUM(output_tokens) as total_output_tokens,
                SUM(total_tokens) as total_tokens,
                SUM(cost_usd) as total_cost,
                SUM(documents_retrieved) as total_documents,
                AVG(response_time_ms) as avg_response_time,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_requests,
                SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed_requests
            FROM token_usage
            {time_filter}
        ''')
        stats = dict(cursor.fetchone())

        # Get recent queries
        cursor.execute(f'''
            SELECT *
            FROM token_usage
            {time_filter}
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        recent_queries = [dict(row) for row in cursor.fetchall()]

        # Get breakdown by model
        cursor.execute(f'''
            SELECT
                model,
                COUNT(*) as requests,
                SUM(total_tokens) as tokens,
                SUM(cost_usd) as cost
            FROM token_usage
            {time_filter}
            GROUP BY model
        ''')
        model_breakdown = [dict(row) for row in cursor.fetchall()]

        # Get breakdown by collection
        cursor.execute(f'''
            SELECT
                collection,
                COUNT(*) as requests,
                SUM(total_tokens) as tokens,
                SUM(cost_usd) as cost
            FROM token_usage
            {time_filter}
            GROUP BY collection
        ''')
        collection_breakdown = [dict(row) for row in cursor.fetchall()]

        conn.close()

        return {
            'period': period,
            'summary': stats,
            'recent_queries': recent_queries,
            'model_breakdown': model_breakdown,
            'collection_breakdown': collection_breakdown
        }

    def get_cost_breakdown(self, period='month'):
        """Get detailed cost breakdown"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Daily costs for the period
        time_filter = ""
        if period == 'week':
            time_filter = "WHERE timestamp >= datetime('now', '-7 days')"
        elif period == 'month':
            time_filter = "WHERE timestamp >= datetime('now', '-30 days')"

        cursor.execute(f'''
            SELECT
                date(timestamp) as date,
                COUNT(*) as requests,
                SUM(total_tokens) as tokens,
                SUM(cost_usd) as cost
            FROM token_usage
            {time_filter}
            GROUP BY date(timestamp)
            ORDER BY date DESC
        ''')

        daily_costs = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return daily_costs

    def export_to_csv(self, output_path="token_usage_export.csv", period='all'):
        """Export usage data to CSV for external analysis"""
        import csv

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        time_filter = ""
        if period == 'today':
            time_filter = "WHERE date(timestamp) = date('now')"
        elif period == 'week':
            time_filter = "WHERE timestamp >= datetime('now', '-7 days')"
        elif period == 'month':
            time_filter = "WHERE timestamp >= datetime('now', '-30 days')"

        cursor.execute(f'''
            SELECT * FROM token_usage
            {time_filter}
            ORDER BY timestamp DESC
        ''')

        rows = cursor.fetchall()

        if rows:
            with open(output_path, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=rows[0].keys())
                writer.writeheader()
                for row in rows:
                    writer.writerow(dict(row))

        conn.close()
        print(f"[TokenTracker] Exported {len(rows)} records to {output_path}")
        return output_path

    def clear_old_data(self, days=90):
        """Clear data older than specified days"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            DELETE FROM token_usage
            WHERE timestamp < datetime('now', '-' || ? || ' days')
        ''', (days,))

        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        print(f"[TokenTracker] Deleted {deleted} records older than {days} days")
        return deleted


# Singleton instance
_tracker_instance = None

def get_tracker():
    """Get or create the global token tracker instance"""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = TokenTracker()
    return _tracker_instance
