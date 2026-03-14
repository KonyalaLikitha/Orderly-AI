"""
Voice POS Frontend with Voice-First Pre-Order Scheduling
Features:
- Three tabs: Current Order, Schedule Order, Voice Assistant
- Voice-first scheduling: Calendar → Voice time → Voice order → Voice confirmation
- No manual typing for scheduling
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
current_session_id = None


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
    """Add item to order (for Current Order tab)."""
    if not product:
        return "Please enter a product name", get_order_display()
    
    try:
        response = requests.post(
            f"{API_BASE}/order/add",
            json={"product": product, "quantity": int(quantity) if quantity else 1}
        )
        if response.status_code == 200:
            result = response.json()
            get_order()
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
            get_order()
            return result.get("message", "Removed"), get_order_display()
    except Exception as e:
        return f"Error: {str(e)}", get_order_display()


def clear_order():
    """Clear current order."""
    try:
        response = requests.delete(f"{API_BASE}/order/clear")
        if response.status_code == 200:
            get_order()
            return "Order cleared", get_order_display()
    except Exception as e:
        return f"Error: {str(e)}", get_order_display()


def get_order_display():
    """Format order for display."""
    order = get_order()
    if not order.get("items"):
        return "🛒 **Current Order**\n\nEmpty. Add items using the form below or use voice commands."
    
    display = "🛒 **Current Order**\n\n"
    for item in order["items"]:
        display += f"- {item['name']}: {item['qty']} × ₹{item['price']} = ₹{item['qty'] * item['price']}\n"
    
    display += f"\n**Total: ₹{order['total']}**"
    return display


def refresh_all():
    """Refresh all displays."""
    get_order()
    refresh_scheduled()
    return get_order_display(), get_scheduled_display(), get_voice_status_display()


def get_scheduled_display():
    """Format scheduled orders for display."""
    try:
        response = requests.get(f"{API_BASE}/order/scheduled")
        if response.status_code == 200:
            data = response.json()
            scheduled = data.get("scheduled_orders", [])
            
            if not scheduled:
                return "📅 **No Scheduled Orders**\n\nYour scheduled orders will appear here."
            
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
        return f"Error loading: {str(e)}"
    
    return "📅 **No Scheduled Orders**"


def refresh_scheduled():
    """Refresh scheduled orders list."""
    global scheduled_orders
    try:
        response = requests.get(f"{API_BASE}/order/scheduled")
        if response.status_code == 200:
            scheduled_orders = response.json().get("scheduled_orders", [])
    except:
        pass


# ==================== VOICE SCHEDULING FUNCTIONS ====================

def start_voice_schedule(selected_date):
    """
    Step 1: User selects date from calendar
    This starts the voice scheduling session
    """
    if not selected_date:
        return "📅 Please select a date from the calendar to start scheduling.", "", get_voice_status_display()
    
    try:
        response = requests.post(
            f"{API_BASE}/order/schedule/session/start",
            json={"date": selected_date}
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("success"):
                # Format date for display
                try:
                    dt = datetime.strptime(selected_date, "%Y-%m-%d")
                    date_formatted = dt.strftime("%B %d, %Y")
                except:
                    date_formatted = selected_date
                
                status = f"📅 **Date Selected: {date_formatted}**\n\n"
                status += f"🎤 **Voice Assistant:** {result.get('prompt', 'Please tell me the time')}\n\n"
                status += "⏰ *Say something like: 6 PM, 18:30, or 7 AM*"
                
                return status, result.get("session_id", ""), get_voice_status_display()
            else:
                return f"❌ {result.get('message', 'Error')}", "", get_voice_status_display()
    
    except Exception as e:
        return f"❌ Error: {str(e)}", "", get_voice_status_display()
    
    return "❌ Could not start scheduling session", "", get_voice_status_display()


def process_voice_time(voice_input, session_id):
    """
    Step 2: Process voice input for time
    """
    if not voice_input:
        return "🎤 Please speak the time (e.g., 6 PM)", session_id, get_voice_status_display()
    
    if not session_id:
        return "❌ No active session. Please select a date first.", "", get_voice_status_display()
    
    try:
        response = requests.post(
            f"{API_BASE}/order/schedule/session/time",
            json={"time": voice_input}
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("success"):
                status = f"✅ **Time Set: {result.get('selected_time')}**\n\n"
                status += f"📅 Scheduled: {result.get('formatted_datetime')}\n\n"
                status += f"🎤 **Voice Assistant:** {result.get('prompt', 'What would you like to order?')}\n\n"
                status += "🛒 *Say something like: two milk packets, or one bread and three eggs*"
                
                return status, result.get("session_id", session_id), get_voice_status_display()
            else:
                return f"🎤 {result.get('prompt', result.get('message', 'Could not understand time'))}", session_id, get_voice_status_display()
    
    except Exception as e:
        return f"❌ Error: {str(e)}", session_id, get_voice_status_display()
    
    return "❌ Could not process time", session_id, get_voice_status_display()


def process_voice_order(voice_input, session_id):
    """
    Step 3: Process voice input for order
    """
    if not voice_input:
        return "🎤 Please speak your order", session_id, get_voice_status_display()
    
    if not session_id:
        return "❌ No active session. Please start over.", "", get_voice_status_display()
    
    try:
        response = requests.post(
            f"{API_BASE}/order/schedule/session/order",
            json={"transcript": voice_input}
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("success"):
                order_items = result.get("order_items", [])
                items_text = ""
                for name, qty in order_items:
                    items_text += f"- {qty} × {name}\n"
                
                status = f"📝 **Order Received:**\n{items_text}\n"
                status += f"📅 **Scheduled:** {result.get('formatted_datetime')}\n\n"
                status += f"💰 **Total:** ₹{result.get('total', 0)}\n\n"
                status += f"🎤 **Voice Assistant:** {result.get('prompt', 'Should I confirm?')}\n\n"
                status += "✅ *Say YES or CONFIRM to save, or NO to cancel*"
                
                return status, result.get("session_id", session_id), get_voice_status_display()
            else:
                return f"🎤 {result.get('prompt', result.get('message', 'Could not understand order'))}", session_id, get_voice_status_display()
    
    except Exception as e:
        return f"❌ Error: {str(e)}", session_id, get_voice_status_display()
    
    return "❌ Could not process order", session_id, get_voice_status_display()


def confirm_voice_order(voice_input, session_id):
    """
    Step 4: Confirm or cancel the order
    """
    if not session_id:
        return "❌ No active session. Please start over.", "", get_voice_status_display()
    
    voice_lower = voice_input.lower().strip()
    
    # Check for confirmation
    if any(word in voice_lower for word in ["yes", "yeah", "yep", "confirm", "ok", "okay", "sure", "do it", "save"]):
        try:
            response = requests.post(
                f"{API_BASE}/order/schedule/session/confirm",
                params={"session_id": session_id}
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success"):
                    status = f"✅ **{result.get('message', 'Order Scheduled!')}**\n\n"
                    status += f"🆔 Order ID: {result.get('scheduled_order', {}).get('id', 'N/A')}\n\n"
                    status += "✨ Your order will be automatically placed at the scheduled time."
                    
                    refresh_scheduled()
                    return status, "", get_voice_status_display()
                else:
                    return f"❌ {result.get('message', 'Error')}", session_id, get_voice_status_display()
        except Exception as e:
            return f"❌ Error: {str(e)}", session_id, get_voice_status_display()
    
    # Check for cancellation
    elif any(word in voice_lower for word in ["no", "nope", "cancel", "don't", "stop"]):
        try:
            requests.post(f"{API_BASE}/order/schedule/session/cancel")
        except:
            pass
        return "❌ Order cancelled. Select a date to start a new schedule.", "", get_voice_status_display()
    
    # Need confirmation
    return "🎤 Please say YES to confirm or NO to cancel.", session_id, get_voice_status_display()


def cancel_voice_schedule():
    """Cancel the current voice scheduling session."""
    try:
        requests.post(f"{API_BASE}/order/schedule/session/cancel")
    except:
        pass
    return "❌ Scheduling cancelled. Select a date to start a new schedule.", "", get_voice_status_display()


def get_voice_status_display():
    """Get current voice scheduling status."""
    try:
        response = requests.get(f"{API_BASE}/order/schedule/session/status")
        if response.status_code == 200:
            data = response.json()
            if data.get("has_active_session"):
                session = data.get("session", {})
                status = session.get("status", "unknown")
                date = session.get("date", "")
                time = session.get("time", "")
                items = session.get("items", [])
                
                status_text = f"🎙️ **Voice Scheduling Active**\n\n"
                status_text += f"📅 Date: {date}\n"
                if time:
                    status_text += f"⏰ Time: {time}\n"
                if items:
                    items_str = ", ".join([f"{qty} {name}" for name, qty in items])
                    status_text += f"🛒 Items: {items_str}\n"
                status_text += f"\n📊 Status: {status}"
                return status_text
    except:
        pass
    
    return "🎙️ **Voice Scheduling**\n\nSelect a date to begin scheduling your order."


def get_calendar_dates():
    """Get available dates for calendar (next 5 days)."""
    today = datetime.now()
    dates = []
    for i in range(5):
        dt = today + timedelta(days=i)
        dates.append({
            "label": dt.strftime("%B %d, %Y"),
            "value": dt.strftime("%Y-%m-%d")
        })
    return dates


# ==================== BUILD THE UI ====================

# Custom CSS for the voice-first interface
custom_css = """
.voice-flow {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 20px;
    border-radius: 15px;
    color: white;
}
.calendar-section {
    background: #f8f9fa;
    padding: 20px;
    border-radius: 15px;
    text-align: center;
}
.date-btn {
    background: #4CAF50 !important;
    color: white !important;
    border: none !important;
    padding: 15px 30px !important;
    font-size: 16px !important;
    border-radius: 10px !important;
    margin: 5px !important;
}
.date-btn:hover {
    background: #45a049 !important;
}
.date-btn:disabled {
    background: #cccccc !important;
    color: #666666 !important;
}
.voice-status {
    background: #fff3cd;
    padding: 15px;
    border-radius: 10px;
    border-left: 4px solid #ffc107;
}
.confirm-btn {
    background: #28a745 !important;
    color: white !important;
}
.cancel-btn {
    background: #dc3545 !important;
    color: white !important;
}
"""

with gr.Blocks(title="Voice POS - Voice-First Scheduling", theme=gr.themes.Soft(), css=custom_css) as app:
    gr.Markdown("# 🛒 Voice POS System")
    gr.Markdown("## Voice-First Pre-Order Scheduling")
    
    with gr.Tabs():
        # ==================== TAB 1: CURRENT ORDER ====================
        with gr.Tab("📋 Current Order"):
            gr.Markdown("### 🛒 Your Current Order")
            
            with gr.Row():
                with gr.Column(scale=1):
                    order_display = gr.Markdown(value=get_order_display())
                    refresh_btn = gr.Button("🔄 Refresh Order", variant="secondary")
                    
                    gr.Markdown("---")
                    gr.Markdown("#### Add Items Manually")
                    with gr.Group():
                        product_input = gr.Textbox(label="Product", placeholder="e.g., bread, milk")
                        quantity_input = gr.Number(label="Quantity", value=1, minimum=1)
                        
                        with gr.Row():
                            add_btn = gr.Button("➕ Add", variant="primary")
                            remove_btn = gr.Button("➖ Remove")
                            clear_btn = gr.Button("🗑️ Clear")
                    
                    status_msg = gr.Textbox(label="Status", interactive=False)
                
                with gr.Column(scale=1):
                    gr.Markdown("#### 📅 Scheduled Orders")
                    scheduled_display = gr.Markdown(value=get_scheduled_display())
                    refresh_scheduled_btn = gr.Button("🔄 Refresh")
        
        # ==================== TAB 2: SCHEDULE ORDER (VOICE-FIRST) ====================
        with gr.Tab("📅 Schedule Order"):
            gr.Markdown("## 🎤 Voice-First Pre-Order Scheduling")
            gr.Markdown("""
            **How it works:**
            1. 👆 Click a date below to select it
            2. 🎤 Speak the time when asked
            3. 🛒 Say your order
            4. ✅ Confirm by saying 'Yes'
            """)
            
            with gr.Row():
                # Left: Calendar Selection
                with gr.Column(scale=1):
                    gr.Markdown("### 📅 Select a Date")
                    gr.Markdown("*Click a date to start voice scheduling*")
                    
                    calendar_group = gr.Group()
                    with calendar_group:
                        dates = get_calendar_dates()
                        for d in dates:
                            date_btn = gr.Button(
                                f"📅 {d['label']}",
                                elem_classes=["date-btn"],
                                variant="primary"
                            )
                
                # Right: Voice Flow Status
                with gr.Column(scale=1):
                    gr.Markdown("### 🎤 Voice Scheduling")
                    
                    voice_status = gr.Markdown(
                        value="👆 **Select a date to begin**",
                        elem_classes=["voice-status"]
                    )
                    
                    # Hidden session ID storage
                    session_id_hidden = gr.Textbox(visible=False, value="")
                    
                    # Voice input field (simulated - in production would use actual voice)
                    gr.Markdown("#### 🎙️ Voice Input")
                    gr.Markdown("*Type what you would say (or use voice in production):*")
                    voice_input = gr.Textbox(
                        label="Your response",
                        placeholder="e.g., 6 PM, two milk, yes",
                        lines=2
                    )
                    
                    with gr.Row():
                        submit_voice_btn = gr.Button("🎤 Submit Voice", variant="primary")
                        cancel_schedule_btn = gr.Button("❌ Cancel", variant="stop")
                    
                    voice_result = gr.Markdown(value="")
            
            gr.Markdown("---")
            gr.Markdown("### 📅 Your Scheduled Orders")
            scheduled_tab_display = gr.Markdown(value=get_scheduled_display())
        
        # ==================== TAB 3: VOICE ASSISTANT ====================
        with gr.Tab("🎤 Voice Assistant"):
            gr.Markdown("## 🎤 Voice Assistant Commands")
            gr.Markdown("""
            **Available Commands:**
            
            **Current Order:**
            - "Add [product]" - Add item to order
            - "Remove [product]" - Remove item
            - "What's my total?" - Get order total
            - "Clear order" - Clear all items
            
            **Scheduling (via calendar + voice):**
            1. Select date from calendar in Schedule Order tab
            2. Speak time (e.g., "6 PM", "18:30")
            3. Speak order (e.g., "two milk packets")
            4. Confirm with "Yes"
            
            **Products Available:**
            Bread, Milk, Pen Pack, Phone Charger, USB Cable, Cooking Oil, Rice, Sugar, Tea, Coffee, Eggs, Butter, Cheese, Notebook, Pencil
            """)
            
            # Simple test for voice parsing
            gr.Markdown("---")
            gr.Markdown("### 🧪 Test Voice Parser")
            with gr.Row():
                test_input = gr.Textbox(label="Voice Transcript", placeholder="e.g., two milk packets and one bread")
                test_btn = gr.Button("Parse")
            test_output = gr.Textbox(label="Parsed Result", interactive=False)
    
    # ==================== CONNECT HANDLERS ====================
    
    # Current Order tab handlers
    refresh_btn.click(refresh_all, outputs=[order_display, scheduled_display, voice_status])
    refresh_scheduled_btn.click(refresh_all, outputs=[order_display, scheduled_display, voice_status])
    
    add_btn.click(add_item, inputs=[product_input, quantity_input], outputs=[status_msg, order_display])
    remove_btn.click(remove_item, inputs=[product_input], outputs=[status_msg, order_display])
    clear_btn.click(clear_order, outputs=[status_msg, order_display])
    
    # Schedule Order tab handlers - date buttons
    def make_date_handler(date_value):
        def handler():
            return start_voice_schedule(date_value)
        return handler
    
    for d in dates:
        date_btn.click(
            make_date_handler(d['value']),
            outputs=[voice_status, session_id_hidden, scheduled_tab_display]
        )
    
    # Voice input handler - determines next step based on session state
    def handle_voice_input(voice_input, session_id):
        # Get current session status
        try:
            response = requests.get(f"{API_BASE}/order/schedule/session/status")
            if response.status_code == 200:
                data = response.json()
                if data.get("has_active_session"):
                    status = data.get("session", {}).get("status", "")
                    
                    if status == "waiting_for_time":
                        return process_voice_time(voice_input, session_id)
                    elif status == "waiting_for_order":
                        return process_voice_order(voice_input, session_id)
                    elif status == "waiting_for_confirmation":
                        return confirm_voice_order(voice_input, session_id)
        except:
            pass
        
        # No active session - prompt to select date
        return "👆 Please select a date from the calendar to start.", "", get_voice_status_display()
    
    submit_voice_btn.click(
        handle_voice_input,
        inputs=[voice_input, session_id_hidden],
        outputs=[voice_result, session_id_hidden, scheduled_tab_display]
    )
    
    # Cancel scheduling
    cancel_schedule_btn.click(
        cancel_voice_schedule,
        outputs=[voice_result, session_id_hidden, scheduled_tab_display]
    )
    
    # Test parser
    def test_parse(transcript):
        try:
            response = requests.post(f"{API_BASE}/parse", json=transcript)
            if response.status_code == 200:
                return str(response.json())
        except:
            pass
        return "Error"
    
    test_btn.click(test_parse, inputs=[test_input], outputs=[test_output])


if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=7860)
