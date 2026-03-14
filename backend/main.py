"""
Voice POS Backend API
FastAPI backend for voice-enabled Point of Sale system.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import uvicorn

from .order_parser import parse_transcript, find_product, get_product_price
from .order_manager import order_manager
from .scheduler_service import scheduler, start_scheduler, stop_scheduler

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    start_scheduler()
    yield
    # Shutdown
    stop_scheduler()

app = FastAPI(title="Voice POS API", version="2.0.0", lifespan=lifespan)


# Request models
class OrderItem(BaseModel):
    name: str
    qty: int = 1


class AddOrderRequest(BaseModel):
    product: str
    quantity: int = 1


class RemoveOrderRequest(BaseModel):
    product: str


class UpdateOrderRequest(BaseModel):
    product: str
    quantity: int


class ScheduleOrderRequest(BaseModel):
    scheduled_datetime: str  # ISO format: "2024-03-20T10:00:00"
    items: Optional[List[OrderItem]] = None


class VoiceScheduleRequest(BaseModel):
    transcript: str


# Health check
@app.get("/")
async def root():
    return {"status": "running", "service": "Voice POS API"}


# Order endpoints
@app.post("/order/add")
async def add_item(request: AddOrderRequest):
    """Add item to current order."""
    result = order_manager.add_item(request.product, request.quantity)
    return result


@app.post("/order/remove")
async def remove_item(request: RemoveOrderRequest):
    """Remove item from current order."""
    result = order_manager.remove_item(request.product)
    return result


@app.put("/order/update")
async def update_item(request: UpdateOrderRequest):
    """Update item quantity in current order."""
    result = order_manager.update_item(request.product, request.quantity)
    return result


@app.get("/order")
async def get_order():
    """Get current order."""
    return order_manager.get_order()


@app.delete("/order/clear")
async def clear_order():
    """Clear current order."""
    return order_manager.clear_order()


# Schedule endpoints
@app.post("/order/schedule")
async def schedule_order(request: ScheduleOrderRequest):
    """
    Schedule an order for a specific date and time.
    Date must be within the next 5 days.
    """
    try:
        # Parse the scheduled datetime
        scheduled_dt = datetime.fromisoformat(request.scheduled_datetime)
        
        # Validate the scheduled time
        now = datetime.now()
        max_scheduled = now + timedelta(days=5)
        
        if scheduled_dt > max_scheduled:
            return {
                "success": False,
                "message": "Orders can only be scheduled within the next 5 days"
            }
        
        if scheduled_dt < now:
            return {
                "success": False,
                "message": "Cannot schedule orders in the past"
            }
        
        # Use provided items or current order
        items = request.items if request.items else None
        if items:
            items_list = [{"name": item.name, "qty": item.qty, "price": get_product_price(item.name) or 0} for item in items]
        else:
            items_list = order_manager.get_order()['items']
        
        if not items_list:
            return {
                "success": False,
                "message": "Cannot schedule an empty order"
            }
        
        result = order_manager.schedule_order(scheduled_dt, items_list)
        return result
        
    except ValueError as e:
        return {
            "success": False,
            "message": f"Invalid date format. Use ISO format: {e}"
        }


@app.get("/order/scheduled")
async def get_scheduled_orders():
    """Get all scheduled orders."""
    return {
        "scheduled_orders": order_manager.get_scheduled_orders()
    }


@app.delete("/order/scheduled/{order_id}")
async def cancel_scheduled_order(order_id: str):
    """Cancel a scheduled order."""
    return order_manager.cancel_scheduled_order(order_id)


@app.get("/order/scheduled/validate")
async def validate_schedule_date(date: str, time: str):
    """
    Validate if a date and time is valid for scheduling.
    Returns: {"valid": bool, "message": str, "datetime": str or None}
    """
    try:
        # Parse date and time
        date_str = date.strip()
        time_str = time.strip()
        
        scheduled_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        
        now = datetime.now()
        max_scheduled = now + timedelta(days=5)
        
        if scheduled_dt < now:
            return {
                "valid": False,
                "message": "Cannot schedule orders in the past",
                "datetime": None
            }
        
        if scheduled_dt > max_scheduled:
            return {
                "valid": False,
                "message": "Orders can only be scheduled within the next 5 days",
                "datetime": None
            }
        
        return {
            "valid": True,
            "message": "Valid schedule time",
            "datetime": scheduled_dt.isoformat()
        }
        
    except ValueError:
        return {
            "valid": False,
            "message": "Invalid date or time format. Use YYYY-MM-DD for date and HH:MM for time",
            "datetime": None
        }


# Parse voice transcript endpoint
@app.post("/parse")
async def parse_voice(transcript: str):
    """Parse a voice transcript."""
    result = parse_transcript(transcript)
    return {"transcript": transcript, "parsed": result}


# Scheduler status
@app.get("/scheduler/status")
async def get_scheduler_status():
    """Get scheduler status."""
    return scheduler.get_status()


# Voice scheduling endpoint - parse natural language
@app.post("/order/schedule/voice")
async def schedule_order_voice(request: VoiceScheduleRequest):
    """
    Schedule an order from a voice transcript.
    Example: "Schedule two milk packets on March 20 at 10 AM"
    """
    transcript = request.transcript.lower()
    
    # Parse quantity
    quantity = 1
    product_name = ""
    
    # Extract quantity words
    quantity_map = {
        'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
        'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
    }
    
    words = transcript.split()
    for i, word in enumerate(words):
        if word in quantity_map:
            quantity = quantity_map[word]
            # Product is likely after this
            if i + 1 < len(words):
                # Find product in remaining text
                remaining = ' '.join(words[i+1:])
                product_match = find_product(remaining)
                if product_match:
                    product_name = product_match['name']
                    break
        elif word.isdigit():
            quantity = int(word)
            remaining = ' '.join(words[i+1:])
            product_match = find_product(remaining)
            if product_match:
                product_name = product_match['name']
                break
    
    # If no product found, try full transcript
    if not product_name:
        product_match = find_product(transcript)
        if product_match:
            product_name = product_match['name']
    
    if not product_name:
        return {
            "success": False,
            "message": "Could not understand the product. Please try again."
        }
    
    # Extract date and time
    # Look for common patterns
    scheduled_dt = None
    now = datetime.now()
    
    # Simple month parsing
    months = {
        'january': 1, 'february': 2, 'march': 3, 'april': 4,
        'may': 5, 'june': 6, 'july': 7, 'august': 8,
        'september': 9, 'october': 10, 'november': 11, 'december': 12
    }
    
    # Try to find month in transcript
    found_month = None
    for month_name, month_num in months.items():
        if month_name in transcript:
            found_month = month_num
            break
    
    # Try to find day number
    import re
    day_match = re.search(r'(\d{1,2})(?:st|nd|rd|th)?', transcript)
    
    # Try to find time
    hour = None
    minute = 0
    is_pm = 'pm' in transcript
    is_am = 'am' in transcript
    
    time_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', transcript)
    if time_match:
        hour = int(time_match.group(1))
        if time_match.group(2):
            minute = int(time_match.group(2))
        if is_pm and hour != 12:
            hour += 12
        elif is_am and hour == 12:
            hour = 0
    
    if found_month and day_match:
        day = int(day_match.group(1))
        year = now.year
        
        # If the date is in the past this year, use next year
        try:
            scheduled_dt = datetime(year, found_month, day, hour or 10, minute)
        except ValueError:
            # Invalid date
            pass
    
    if not scheduled_dt:
        # Default to tomorrow at 10 AM
        scheduled_dt = now + timedelta(days=1)
        scheduled_dt = scheduled_dt.replace(hour=10, minute=0, second=0, microsecond=0)
    
    # Validate
    max_scheduled = now + timedelta(days=5)
    if scheduled_dt > max_scheduled:
        return {
            "success": False,
            "message": "Orders can only be scheduled within the next 5 days"
        }
    
    if scheduled_dt < now:
        return {
            "success": False,
            "message": "Cannot schedule orders in the past"
        }
    
    # Create order items
    items = [{
        "name": product_name,
        "qty": quantity,
        "price": get_product_price(product_name) or 0
    }]
    
    result = order_manager.schedule_order(scheduled_dt, items)
    return result


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
