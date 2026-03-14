"""
Order Manager Module
Handles order CRUD operations including scheduled orders.
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional


class OrderManager:
    """Manages both immediate and scheduled orders."""
    
    def __init__(self):
        # Current immediate order session
        self.current_order = {"items": []}
        # Store scheduled orders
        self.scheduled_orders = []
        # Order ID counter
        self.order_counter = 1
    
    def add_item(self, product: str, quantity: int = 1) -> Dict[str, Any]:
        """Add item to current order or increment if exists."""
        from .order_parser import get_product_price, find_product
        
        product_info = find_product(product)
        if not product_info:
            return {"success": False, "message": f"Product '{product}' not found"}
        
        price = product_info['price']
        name = product_info['name']
        
        # Check if item already exists
        for item in self.current_order['items']:
            if item['name'] == name:
                item['qty'] += quantity
                return {
                    "success": True,
                    "message": f"Added {quantity} {name} to your order (now {item['qty']})",
                    "order": self.get_order()
                }
        
        # Add new item
        self.current_order['items'].append({
            "name": name,
            "qty": quantity,
            "price": price
        })
        
        return {
            "success": True,
            "message": f"Added {quantity} {name} to your order",
            "order": self.get_order()
        }
    
    def remove_item(self, product: str) -> Dict[str, Any]:
        """Remove item from current order."""
        from .order_parser import find_product
        
        product_info = find_product(product)
        if not product_info:
            return {"success": False, "message": f"Product '{product}' not found"}
        
        name = product_info['name']
        
        # Find and remove item
        for i, item in enumerate(self.current_order['items']):
            if item['name'] == name:
                self.current_order['items'].pop(i)
                return {
                    "success": True,
                    "message": f"Removed {name} from your order",
                    "order": self.get_order()
                }
        
        return {
            "success": False,
            "message": f"{name} not in your order"
        }
    
    def update_item(self, product: str, quantity: int) -> Dict[str, Any]:
        """Update quantity for an item in current order."""
        from .order_parser import find_product
        
        product_info = find_product(product)
        if not product_info:
            return {"success": False, "message": f"Product '{product}' not found"}
        
        name = product_info['name']
        
        # Find and update item
        for item in self.current_order['items']:
            if item['name'] == name:
                if quantity <= 0:
                    self.current_order['items'].remove(item)
                    return {
                        "success": True,
                        "message": f"Removed {name} from your order",
                        "order": self.get_order()
                    }
                item['qty'] = quantity
                return {
                    "success": True,
                    "message": f"Updated {name} quantity to {quantity}",
                    "order": self.get_order()
                }
        
        return {
            "success": False,
            "message": f"{name} not in your order"
        }
    
    def get_order(self) -> Dict[str, Any]:
        """Get current order with total."""
        total = sum(item['qty'] * item['price'] for item in self.current_order['items'])
        return {
            "items": [
                {"name": item['name'], "qty": item['qty'], "price": item['price']}
                for item in self.current_order['items']
            ],
            "total": total
        }
    
    def clear_order(self) -> Dict[str, Any]:
        """Clear all items from current order."""
        self.current_order = {"items": []}
        return {
            "success": True,
            "message": "Order cleared",
            "order": self.get_order()
        }
    
    def schedule_order(self, scheduled_datetime: datetime, items: List[Dict] = None) -> Dict[str, Any]:
        """
        Schedule an order for future execution.
        
        Args:
            scheduled_datetime: When to execute the order
            items: List of items (if None, uses current order)
        
        Returns:
            Scheduled order details
        """
        # Validate scheduled time (must be within next 5 days)
        now = datetime.now()
        max_scheduled_time = now + timedelta(days=5)
        
        if scheduled_datetime > max_scheduled_time:
            return {
                "success": False,
                "message": "Orders can only be scheduled within the next 5 days"
            }
        
        if scheduled_datetime < now:
            return {
                "success": False,
                "message": "Cannot schedule orders in the past"
            }
        
        # Generate order ID
        order_id = f"SCH-{self.order_counter:04d}"
        self.order_counter += 1
        
        # Use provided items or current order
        order_items = items if items is not None else self.get_order()['items']
        
        if not order_items:
            return {
                "success": False,
                "message": "Cannot schedule an empty order"
            }
        
        scheduled_order = {
            "id": order_id,
            "scheduled_datetime": scheduled_datetime.isoformat(),
            "items": order_items,
            "total": sum(item['qty'] * item['price'] for item in order_items),
            "status": "scheduled",
            "created_at": now.isoformat()
        }
        
        self.scheduled_orders.append(scheduled_order)
        
        return {
            "success": True,
            "message": f"Order scheduled for {scheduled_datetime.strftime('%B %d, %Y at %I:%M %p')}",
            "scheduled_order": scheduled_order
        }
    
    def get_scheduled_orders(self) -> List[Dict]:
        """Get all scheduled orders."""
        return sorted(self.scheduled_orders, key=lambda x: x['scheduled_datetime'])
    
    def cancel_scheduled_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel a scheduled order."""
        for i, order in enumerate(self.scheduled_orders):
            if order['id'] == order_id:
                self.scheduled_orders.pop(i)
                return {
                    "success": True,
                    "message": f"Scheduled order {order_id} cancelled"
                }
        
        return {
            "success": False,
            "message": f"Scheduled order {order_id} not found"
        }
    
    def execute_scheduled_order(self, order_id: str) -> Dict[str, Any]:
        """Execute a scheduled order immediately (for scheduler)."""
        for order in self.scheduled_orders:
            if order['id'] == order_id:
                # Add items to current order
                for item in order['items']:
                    self.add_item(item['name'], item['qty'])
                
                # Remove from scheduled
                self.scheduled_orders.remove(order)
                
                return {
                    "success": True,
                    "message": f"Scheduled order {order_id} executed",
                    "order": self.get_order()
                }
        
        return {
            "success": False,
            "message": f"Scheduled order {order_id} not found"
        }


# Singleton instance
order_manager = OrderManager()
