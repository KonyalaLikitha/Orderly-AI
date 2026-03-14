"""
Tests for the Order Manager Module
"""

import sys
sys.path.insert(0, '/workspace/project/Orderly-AI')

from datetime import datetime, timedelta
from backend.order_manager import OrderManager


def test_add_item():
    """Test adding items to order."""
    manager = OrderManager()
    result = manager.add_item("bread", 2)
    assert result["success"] == True
    assert result["order"]["items"][0]["name"] == "Bread"
    assert result["order"]["items"][0]["qty"] == 2
    print("✓ Add item test passed")


def test_add_increments():
    """Test that adding same item increments quantity."""
    manager = OrderManager()
    manager.add_item("bread", 2)
    result = manager.add_item("bread", 1)
    assert result["order"]["items"][0]["qty"] == 3
    print("✓ Add increments test passed")


def test_remove_item():
    """Test removing items from order."""
    manager = OrderManager()
    manager.add_item("bread", 2)
    result = manager.remove_item("bread")
    assert result["success"] == True
    assert len(result["order"]["items"]) == 0
    print("✓ Remove item test passed")


def test_update_item():
    """Test updating item quantity."""
    manager = OrderManager()
    manager.add_item("bread", 2)
    result = manager.update_item("bread", 5)
    assert result["success"] == True
    assert result["order"]["items"][0]["qty"] == 5
    print("✓ Update item test passed")


def test_get_order_total():
    """Test order total calculation."""
    manager = OrderManager()
    manager.add_item("bread", 2)  # 2 * 80 = 160
    manager.add_item("milk", 1)   # 1 * 60 = 60
    order = manager.get_order()
    assert order["total"] == 220
    print("✓ Get order total test passed")


def test_clear_order():
    """Test clearing order."""
    manager = OrderManager()
    manager.add_item("bread", 2)
    result = manager.clear_order()
    assert result["success"] == True
    assert len(result["order"]["items"]) == 0
    assert result["order"]["total"] == 0
    print("✓ Clear order test passed")


def test_schedule_order():
    """Test scheduling an order."""
    manager = OrderManager()
    
    # Schedule for tomorrow
    schedule_time = datetime.now() + timedelta(days=1)
    schedule_time = schedule_time.replace(hour=10, minute=0, second=0, microsecond=0)
    
    result = manager.schedule_order(schedule_time, [
        {"name": "Bread", "qty": 2, "price": 80}
    ])
    
    assert result["success"] == True
    assert "SCH-" in result["scheduled_order"]["id"]
    print("✓ Schedule order test passed")


def test_schedule_order_validate_5_days():
    """Test that orders cannot be scheduled beyond 5 days."""
    manager = OrderManager()
    
    # Schedule for 6 days from now
    schedule_time = datetime.now() + timedelta(days=6)
    schedule_time = schedule_time.replace(hour=10, minute=0, second=0, microsecond=0)
    
    result = manager.schedule_order(schedule_time)
    assert result["success"] == False
    assert "5 days" in result["message"]
    print("✓ Schedule validation (5 days) test passed")


def test_schedule_order_validate_past():
    """Test that orders cannot be scheduled in the past."""
    manager = OrderManager()
    
    # Schedule for yesterday
    schedule_time = datetime.now() - timedelta(days=1)
    
    result = manager.schedule_order(schedule_time)
    assert result["success"] == False
    assert "past" in result["message"]
    print("✓ Schedule validation (past) test passed")


def test_get_scheduled_orders():
    """Test getting scheduled orders."""
    manager = OrderManager()
    
    # Schedule two orders
    time1 = datetime.now() + timedelta(days=1)
    time2 = datetime.now() + timedelta(days=2)
    
    manager.schedule_order(time1.replace(hour=10), [{"name": "Bread", "qty": 1, "price": 80}])
    manager.schedule_order(time2.replace(hour=14), [{"name": "Milk", "qty": 1, "price": 60}])
    
    orders = manager.get_scheduled_orders()
    assert len(orders) == 2
    print("✓ Get scheduled orders test passed")


def test_cancel_scheduled_order():
    """Test cancelling a scheduled order."""
    manager = OrderManager()
    
    schedule_time = datetime.now() + timedelta(days=1)
    result = manager.schedule_order(schedule_time, [{"name": "Bread", "qty": 1, "price": 80}])
    order_id = result["scheduled_order"]["id"]
    
    cancel_result = manager.cancel_scheduled_order(order_id)
    assert cancel_result["success"] == True
    
    orders = manager.get_scheduled_orders()
    assert len(orders) == 0
    print("✓ Cancel scheduled order test passed")


if __name__ == "__main__":
    test_add_item()
    test_add_increments()
    test_remove_item()
    test_update_item()
    test_get_order_total()
    test_clear_order()
    test_schedule_order()
    test_schedule_order_validate_5_days()
    test_schedule_order_validate_past()
    test_get_scheduled_orders()
    test_cancel_scheduled_order()
    print("\n✅ All order manager tests passed!")
