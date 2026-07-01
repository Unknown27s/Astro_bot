#!/usr/bin/env python3
"""Test the observability feature by simulating a query trace."""

import sys
import sqlite3
from pathlib import Path
import uuid
from datetime import datetime, timezone

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

def _now():
    """UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()

def test_observability():
    """Test observability by creating a sample trace with spans."""

    db_path = Path(__file__).parent / "data" / "astrobot.db"

    if not db_path.exists():
        print("❌ Database not found!")
        return False

    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row

        # Check if tables exist
        tables = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name IN ('obs_traces', 'obs_spans')
        """).fetchall()

        table_names = [t['name'] for t in tables]

        if 'obs_traces' not in table_names or 'obs_spans' not in table_names:
            print("❌ Observability tables not found!")
            print(f"   Found tables: {table_names}")
            return False

        print("✅ Observability tables exist")

        # Create a test trace
        trace_id = str(uuid.uuid4())
        print(f"\n📝 Creating test trace: {trace_id[:8]}...")

        conn.execute("""
            INSERT INTO obs_traces
            (trace_id, service, operation, user_id, start_time, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (trace_id, "test-service", "test.operation", "test-user", _now(), "pending", _now()))

        # Create a test span
        span_id = str(uuid.uuid4())
        print(f"📍 Creating test span: {span_id[:8]}...")

        conn.execute("""
            INSERT INTO obs_spans
            (span_id, trace_id, service, operation, start_time, status, input_data, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (span_id, trace_id, "test-service", "test.sub_operation", _now(), "success",
              '{"query": "test"}', _now()))

        # Update trace with end time
        import time
        time.sleep(0.1)  # Simulate some work

        conn.execute("""
            UPDATE obs_traces
            SET status = 'success', end_time = ?,
                duration_ms = CAST((julianday(?) - julianday(start_time)) * 86400000 AS REAL)
            WHERE trace_id = ?
        """, (_now(), _now(), trace_id))

        # Update span with end time
        conn.execute("""
            UPDATE obs_spans
            SET status = 'success', end_time = ?,
                duration_ms = CAST((julianday(?) - julianday(start_time)) * 86400000 AS REAL),
                output_data = ?
            WHERE span_id = ?
        """, (_now(), _now(), '{"result": "ok"}', span_id))

        conn.commit()
        print("✅ Test data inserted successfully")

        # Verify data was inserted
        trace_count = conn.execute("SELECT COUNT(*) as cnt FROM obs_traces").fetchone()['cnt']
        span_count = conn.execute("SELECT COUNT(*) as cnt FROM obs_spans").fetchone()['cnt']

        print(f"\n📊 Database Statistics:")
        print(f"  - Total Traces: {trace_count}")
        print(f"  - Total Spans: {span_count}")

        # Fetch and display the test trace
        test_trace = conn.execute(
            "SELECT * FROM obs_traces WHERE trace_id = ? LIMIT 1", (trace_id,)
        ).fetchone()

        if test_trace:
            print(f"\n✅ Test Trace Retrieved:")
            print(f"  - Trace ID: {test_trace['trace_id'][:8]}...")
            print(f"  - Service: {test_trace['service']}")
            print(f"  - Operation: {test_trace['operation']}")
            print(f"  - Duration: {test_trace['duration_ms']:.2f}ms")
            print(f"  - Status: {test_trace['status']}")

        test_spans = conn.execute(
            "SELECT * FROM obs_spans WHERE trace_id = ? LIMIT 5", (trace_id,)
        ).fetchall()

        if test_spans:
            print(f"\n✅ Test Spans Retrieved: {len(test_spans)} span(s)")
            for span in test_spans:
                print(f"  - {span['operation']}: {span['duration_ms']:.2f}ms")

        # Get aggregate metrics
        metrics = conn.execute("""
            SELECT
                COUNT(*) as total_traces,
                AVG(duration_ms) as avg_latency,
                COUNT(CASE WHEN status='error' THEN 1 END) as error_count
            FROM obs_traces
        """).fetchone()

        print(f"\n📈 Aggregate Metrics:")
        print(f"  - Total Traces: {metrics['total_traces']}")
        print(f"  - Avg Latency: {metrics['avg_latency']:.2f}ms")
        print(f"  - Error Count: {metrics['error_count']}")

        conn.close()

        print("\n" + "="*50)
        print("✅ OBSERVABILITY FEATURE TEST PASSED!")
        print("="*50)
        print("\nNext steps:")
        print("1. Start Streamlit: streamlit run app.py")
        print("2. Go to 💬 Test Chat and send a query")
        print("3. Go to 📈 Observability Dashboard")
        print("4. Click 🔄 Refresh Data to see your trace!")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_observability()
    sys.exit(0 if success else 1)
