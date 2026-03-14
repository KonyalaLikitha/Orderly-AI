"""
Voice POS Frontend with Scheduled Order Booking
Features:
- Vapi voice assistant integration
- Real-time order display
- Scheduled order booking with date-time picker
- Manual order management
"""

import gradio as gr
import requests
import json
from datetime import datetime, timedelta

# API base URL
API_BASE = "http://localhost:8001"

# Global state
current_order = {"items": [], "total": 0}
scheduled_orders = []


def get_order():
    """Fetch current order from API."""
    global current_order
    try:
        response = requests.get(f"{API_BASE}/order")
        if response.status_code == 200:
            current_order = response.json()
            return current_order
    except:
        pass
    return {"items": [], "total": 0}


def add_item(product, quantity):
    """Add item to order."""
    if not product:
        return "Please enter a product name", get_order_display()
    
    try:
        response = requests.post(
            f"{API_BASE}/order/add",
            json={"product": product, "quantity": int(quantity) if quantity else 1}
        )
        if response.status_code == 200:
            result = response.json()
            get_order()  # Refresh
            return result.get("message", "Added"), get_order_display()
    except Exception as e:
        return f"Error: {str(e)}", get_order_display()


def remove_item(product):
    """Remove item from order."""
    if not product:
        return "Please enter a product name", get_order_display()
    
    try:
        response = requests.post(
            f"{API_BASE}/order/remove",
            json={"product": product}
        )
        if response.status_code == 200:
            result = response.json()
            get_order()  # Refresh
            return result.get("message", "Removed"), get_order_display()
    except Exception as e:
        return f"Error: {str(e)}", get_order_display()


def update_item(product, quantity):
    """Update item quantity."""
    if not product:
        return "Please enter a product name", get_order_display()
    
    try:
        response = requests.put(
            f"{API_BASE}/order/update",
            json={"product": product, "quantity": int(quantity)}
        )
        if response.status_code == 200:
            result = response.json()
            get_order()  # Refresh
            return result.get("message", "Updated"), get_order_display()
    except Exception as e:
        return f"Error: {str(e)}", get_order_display()


def clear_order():
    """Clear current order."""
    try:
        response = requests.delete(f"{API_BASE}/order/clear")
        if response.status_code == 200:
            get_order()  # Refresh
            return "Order cleared", get_order_display()
    except Exception as e:
        return f"Error: {str(e)}", get_order_display()


def get_order_display():
    """Format order for display."""
    order = get_order()
    if not order.get("items"):
        return "🛒 Empty Order\n\nAdd items using voice or manual input."
    
    display = "🛒 **Current Order**\n\n"
    for item in order["items"]:
        display += f"- {item['name']}: {item['qty']} × ₹{item['price']} = ₹{item['qty'] * item['price']}\n"
    
    display += f"\n**Total: ₹{order['total']}**"
    return display


def refresh_orders():
    """Refresh both current and scheduled orders."""
    get_order()
    refresh_scheduled()
    return get_order_display(), get_scheduled_display()


def get_scheduled_display():
    """Format scheduled orders for display."""
    try:
        response = requests.get(f"{API_BASE}/order/scheduled")
        if response.status_code == 200:
            data = response.json()
            scheduled = data.get("scheduled_orders", [])
            
            if not scheduled:
                return "📅 No Scheduled Orders\n\nSchedule an order for later delivery."
            
            display = "📅 **Scheduled Orders**\n\n"
            for order in scheduled:
                dt = datetime.fromisoformat(order["scheduled_datetime"])
                display += f"**{order['id']}**\n"
                display += f"📆 {dt.strftime('%B %d, %Y at %I:%M %p')}\n"
                for item in order["items"]:
                    display += f"- {item['name']}: {item['qty']} × ₹{item['price']}\n"
                display += f"**Total: ₹{order['total']}**\n"
                display += f"Status: {order['status']}\n\n"
            
            return display
    except Exception as e:
        return f"Error loading scheduled orders: {str(e)}"
    
    return "📅 No Scheduled Orders"


def refresh_scheduled():
    """Refresh scheduled orders list."""
    global scheduled_orders
    try:
        response = requests.get(f"{API_BASE}/order/scheduled")
        if response.status_code == 200:
            scheduled_orders = response.json().get("scheduled_orders", [])
    except:
        pass


def schedule_order_from_current(schedule_date, schedule_time):
    """Schedule current order for a specific date and time."""
    if not schedule_date or not schedule_time:
        return "Please select both date and time", get_order_display(), get_scheduled_display()
    
    try:
        # Validate the scheduled time
        response = requests.get(
            f"{API_BASE}/order/scheduled/validate",
            params={"date": schedule_date, "time": schedule_time}
        )
        
        if response.status_code == 200:
            data = response.json()
            if not data.get("valid"):
                return data.get("message", "Invalid time"), get_order_display(), get_scheduled_display()
            
            scheduled_dt = data.get("datetime")
            
            # Use current order items
            order = get_order()
            if not order.get("items"):
                return "Order is empty. Add items first.", get_order_display(), get_scheduled_display()
            
            items = [{"name": item["name"], "qty": item["qty"]} for item in order["items"]]
            
            response = requests.post(
                f"{API_BASE}/order/schedule",
                json={
                    "scheduled_datetime": scheduled_dt,
                    "items": items
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    # Clear current order after scheduling
                    clear_order()
                    refresh_scheduled()
                    return result.get("message", "Order scheduled!"), get_order_display(), get_scheduled_display()
                else:
                    return result.get("message", "Failed to schedule"), get_order_display(), get_scheduled_display()
    except Exception as e:
        return f"Error: {str(e)}", get_order_display(), get_scheduled_display()
    
    return "Failed to schedule order", get_order_display(), get_scheduled_display()


def cancel_scheduled(order_id):
    """Cancel a scheduled order."""
    if not order_id:
        return "Please enter an order ID", get_scheduled_display()
    
    try:
        response = requests.delete(f"{API_BASE}/order/scheduled/{order_id}")
        if response.status_code == 200:
            result = response.json()
            refresh_scheduled()
            return result.get("message", "Cancelled"), get_scheduled_display()
    except Exception as e:
        return f"Error: {str(e)}", get_scheduled_display()
    
    return "Failed to cancel", get_scheduled_display()


def get_available_dates():
    """Get list of available dates (next 5 days) for the date picker."""
    today = datetime.now()
    dates = []
    for i in range(5):
        dt = today + timedelta(days=i)
        dates.append(dt.strftime("%Y-%m-%d"))
    return dates


def get_available_times():
    """Get list of available time slots."""
    times = []
    for hour in range(6, 23):  # 6 AM to 10 PM
        times.append(f"{hour:02d}:00")
        times.append(f"{hour:02d}:30")
    return times


# Build the UI
with gr.Blocks(title="Voice POS - Scheduled Orders", theme=gr.themes.Soft()) as app:
    gr.Markdown("# 🛒 Voice POS System")
    gr.Markdown("## With Scheduled Order Booking")
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 📋 Manual Order")
            
            with gr.Group():
                product_input = gr.Textbox(label="Product", placeholder="e.g., bread, milk, pen")
                quantity_input = gr.Number(label="Quantity", value=1, minimum=1)
                
                with gr.Row():
                    add_btn = gr.Button("➕ Add", variant="primary")
                    remove_btn = gr.Button("➖ Remove")
                
                with gr.Row():
                    update_btn = gr.Button("🔄 Update")
                    clear_btn = gr.Button("🗑️ Clear")
            
            gr.Markdown("### 📅 Schedule Order")
            gr.Markdown("*Schedule your order for delivery within the next 5 days*")
            
            with gr.Group():
                gr.Markdown("**Select Date and Time:**")
                date_picker = gr.Dropdown(
                    label="Date",
                    choices=get_available_dates(),
                    value=get_available_dates()[0] if get_available_dates() else None
                )
                time_picker = gr.Dropdown(
                    label="Time",
                    choices=get_available_times(),
                    value="10:00"
                )
                
                schedule_btn = gr.Button("📅 Schedule Current Order", variant="primary")
            
            status_output = gr.Textbox(label="Status", interactive=False)
        
        with gr.Column(scale=1):
            gr.Markdown("### 🛒 Current Order")
            order_display = gr.Markdown(value=get_order_display())
            refresh_btn = gr.Button("🔄 Refresh")
            
            gr.Markdown("### 📅 Scheduled Orders")
            scheduled_display = gr.Markdown(value=get_scheduled_display())
            refresh_scheduled_btn = gr.Button("🔄 Refresh Scheduled")
            
            with gr.Group():
                cancel_id = gr.Textbox(label="Order ID to Cancel", placeholder="e.g., SCH-0001")
                cancel_btn = gr.Button("❌ Cancel Scheduled Order")
    
    # Connect buttons
    add_btn.click(add_item, inputs=[product_input, quantity_input], outputs=[status_output, order_display])
    remove_btn.click(remove_item, inputs=[product_input], outputs=[status_output, order_display])
    update_btn.click(update_item, inputs=[product_input, quantity_input], outputs=[status_output, order_display])
    clear_btn.click(clear_order, outputs=[status_output, order_display])
    
    schedule_btn.click(
        schedule_order_from_current,
        inputs=[date_picker, time_picker],
        outputs=[status_output, order_display, scheduled_display]
    )
    
    refresh_btn.click(refresh_orders, outputs=[order_display, scheduled_display])
    refresh_scheduled_btn.click(lambda: get_scheduled_display(), outputs=[scheduled_display])
    
    cancel_btn.click(cancel_scheduled, inputs=[cancel_id], outputs=[scheduled_display])
    
    # Voice command section
    gr.Markdown("---")
    gr.Markdown("### 🎤 Voice Commands")
    gr.Markdown("""
    **Current Order:**
    - "Add [product]" - Add item to order
    - "Remove [product]" - Remove item
    - "Clear order" - Clear all items
    
    **Schedule Voice Commands (via Vapi):**
    - "Schedule two milk packets on March 20 at 10 AM"
    - "Book bread for 7 PM on April 2"
    """)

if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=7860)
