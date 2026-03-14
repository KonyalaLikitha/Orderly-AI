"""
Vapi Voice Integration for Voice POS
This module handles Vapi API calls for voice commands.
"""

import os
import requests
from typing import Dict, Any, Optional

VAPI_BASE_URL = "https://api.vapi.ai"


class VapiClient:
    """Client for Vapi.ai voice assistant API."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("VAPI_PUBLIC_KEY")
        self.base_url = VAPI_BASE_URL
    
    def add_tool_calls(self, tool_calls: list) -> Dict[str, Any]:
        """
        Execute tool calls from Vapi assistant.
        
        Tool calls include:
        - addToOrder
        - removeFromOrder
        - updateOrderItem
        - getCurrentOrder
        - clearOrder
        - scheduleOrder
        - getScheduledOrders
        - cancelScheduledOrder
        """
        if not self.api_key:
            return {"error": "VAPI_PUBLIC_KEY not set"}
        
        results = []
        
        for tool_call in tool_calls:
            function_name = tool_call.get("name")
            arguments = tool_call.get("arguments", {})
            
            result = self._execute_function(function_name, arguments)
            results.append({
                "tool_call_id": tool_call.get("id"),
                "function": function_name,
                "result": result
            })
        
        return {"results": results}
    
    def _execute_function(self, function_name: str, arguments: Dict) -> Any:
        """Execute a specific function."""
        from backend.order_parser import parse_transcript, find_product
        from backend.order_manager import order_manager
        
        API_BASE = "http://localhost:8001"
        
        if function_name == "addToOrder":
            product = arguments.get("product")
            quantity = arguments.get("quantity", 1)
            result = order_manager.add_item(product, quantity)
            return result
        
        elif function_name == "removeFromOrder":
            product = arguments.get("product")
            result = order_manager.remove_item(product)
            return result
        
        elif function_name == "updateOrderItem":
            product = arguments.get("product")
            quantity = arguments.get("quantity")
            result = order_manager.update_item(product, quantity)
            return result
        
        elif function_name == "getCurrentOrder":
            return order_manager.get_order()
        
        elif function_name == "clearOrder":
            return order_manager.clear_order()
        
        elif function_name == "scheduleOrder":
            product = arguments.get("product")
            quantity = arguments.get("quantity", 1)
            date = arguments.get("date")
            time = arguments.get("time")
            
            if not date or not time:
                return {"success": False, "message": "Please provide both date and time"}
            
            from datetime import datetime, timedelta
            
            try:
                scheduled_dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
                now = datetime.now()
                
                if scheduled_dt > now + timedelta(days=5):
                    return {"success": False, "message": "Orders can only be scheduled within the next 5 days"}
                
                if scheduled_dt < now:
                    return {"success": False, "message": "Cannot schedule orders in the past"}
                
                items = [{
                    "name": product,
                    "qty": quantity,
                    "price": 0  # Will be filled by order_manager
                }]
                
                return order_manager.schedule_order(scheduled_dt, items)
            
            except ValueError as e:
                return {"success": False, "message": f"Invalid date/time format: {str(e)}"}
        
        elif function_name == "getScheduledOrders":
            return {"scheduled_orders": order_manager.get_scheduled_orders()}
        
        elif function_name == "cancelScheduledOrder":
            order_id = arguments.get("orderId")
            return order_manager.cancel_scheduled_order(order_id)
        
        return {"error": f"Unknown function: {function_name}"}


# Default client instance
vapi_client = VapiClient()
