import pytest
import os
import sqlite3
from server import init_db, get_user_stats, start_session, complete_session

TEST_DB = "test_focus_flow.db"

@pytest.fixture(autouse=True)
def run_around_tests():
    # Setup: Create fresh test database
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    init_db(TEST_DB)
    
    yield # Run the test
    
    # Teardown: Clean up
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def test_initial_stats():
    stats = get_user_stats(TEST_DB)
    assert stats["level"] == 1
    assert stats["xp"] == 0
    assert stats["total_focus_time"] == 0
    assert stats["xp_required_for_next_level"] == 100 # 100 * (1 ^ 1.5)
    assert stats["progress_percentage"] == 0.0

def simulate_session(duration, db_path):
    session_id, _ = start_session(duration, db_path)
    
    # Fast forward time to bypass anti-cheat
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("UPDATE active_sessions SET start_time_ts = start_time_ts - ? WHERE id = ?", (duration * 60 + 10, session_id))
    conn.commit()
    conn.close()
    
    stats, title = complete_session(session_id, db_path)
    return stats

def test_anti_cheat_blocks_early_completion():
    session_id, _ = start_session(25, TEST_DB)
    # Try to complete immediately (0 minutes elapsed)
    with pytest.raises(ValueError, match="Anti-Cheat"):
        complete_session(session_id, TEST_DB)

def test_add_session_xp_math():
    # Add a 5 minute session -> Should yield 50 XP
    stats = simulate_session(5, TEST_DB)
    assert stats["total_focus_time"] == 5
    assert stats["xp"] == 50
    assert stats["level"] == 1
    assert stats["progress_percentage"] == 50.0

def test_level_up():
    # Add 10 minutes -> 100 XP -> Exact amount needed for Level 2
    stats = simulate_session(10, TEST_DB)
    assert stats["level"] == 2
    assert stats["xp"] == 100
    
    # XP required for level 3 is 100 * (2 ^ 1.5) = 282
    assert stats["xp_required_for_next_level"] == 282
    assert stats["progress_percentage"] == 0.0 # Just hit level 2, so 0% towards level 3

def test_multiple_level_ups():
    # Add 100 minutes -> 1000 XP
    stats = simulate_session(100, TEST_DB)
    assert stats["level"] == 5
    assert stats["xp"] == 1000
    assert stats["xp_required_for_next_level"] == 1118
    assert stats["xp_base_for_current_level"] == 800
    
    # Progress towards level 6: (1000 - 800) / (1118 - 800) * 100 = 62.89%
    assert 60 < stats["progress_percentage"] < 65

def test_session_history_logging():
    simulate_session(25, TEST_DB)
    simulate_session(15, TEST_DB)
    
    conn = sqlite3.connect(TEST_DB)
    c = conn.cursor()
    c.execute("SELECT duration, title FROM sessions ORDER BY id ASC")
    rows = c.fetchall()
    conn.close()
    
    assert len(rows) == 2
    assert rows[0][0] == 25
    assert "25m" in rows[0][1] # Verify RPG quest title injected duration
    assert rows[1][0] == 15
    assert "15m" in rows[1][1]
