# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

import os


def list_available_items() -> dict:
    """Lists all available items in our catalog, including their item_ids and names.

    Returns:
        A dictionary containing the catalog list of items.
    """
    return {
        "status": "SUCCESS",
        "items": [
            {"item_id": "item-101", "name": "Premium Wireless Headphones"},
            {"item_id": "item-102", "name": "Mechanical Gaming Keyboard"},
            {"item_id": "item-103", "name": "Ergonomic Office Chair"}
        ]
    }


def get_item_inventory(item_id: str) -> dict:
    """Gets inventory details for an item, including name, price, and stock count.

    Args:
        item_id: The unique identifier of the item (e.g., 'item-101', 'item-102').

    Returns:
        A dictionary with item name, unit price, stock, and status.
    """
    inventory = {
        "item-101": {"name": "Premium Wireless Headphones", "price": 149.99, "stock": 15},
        "item-102": {"name": "Mechanical Gaming Keyboard", "price": 89.99, "stock": 5},
        "item-103": {"name": "Ergonomic Office Chair", "price": 249.99, "stock": 0},
    }
    item = inventory.get(item_id.lower().strip())
    if not item:
        return {"status": "ERROR", "message": f"Item '{item_id}' not found."}
    return {"status": "SUCCESS", "item_id": item_id, **item}


def validate_coupon_code(code: str) -> dict:
    """Validates a promotional coupon code and returns its discount percentage.

    Args:
        code: The promo coupon code string (e.g., 'SAVE10', 'SUPERDEAL').

    Returns:
        A dictionary containing status, coupon validity, and discount_rate (as a decimal float).
    """
    coupons = {
        "save10": {"valid": True, "discount_rate": 0.10, "is_active": True},
        "superdeal": {"valid": True, "discount_rate": 0.50, "is_active": True},
        "buggy90": {"valid": True, "discount_rate": 0.90, "is_active": True},
        "exploit150": {"valid": True, "discount_rate": 1.50, "is_active": True},
    }
    
    cleaned_code = code.lower().strip()
    coupon = coupons.get(cleaned_code)
    if not coupon:
        return {"status": "SUCCESS", "valid": False, "discount_rate": 0.0, "message": "Invalid coupon code."}
    
    # Business boundary check: Reject coupons that exceed 100% discount or are negative
    discount_rate = coupon.get("discount_rate", 0.0)
    if discount_rate > 1.0 or discount_rate < 0.0:
        return {
            "status": "SUCCESS",
            "valid": False,
            "discount_rate": 0.0,
            "message": f"Coupon error: discount rate {discount_rate} is out of allowable business limits."
        }
        
    return {"status": "SUCCESS", **coupon}


def calculate_final_total(item_id: str, quantity: int, discount_rate: float) -> dict:
    """Calculates the final cart total based on the item price, quantity, and discount rate.

    Args:
        item_id: The item identifier.
        quantity: The quantity being purchased.
        discount_rate: The discount rate as a float (e.g., 0.10 for 10% off).

    Returns:
        A dictionary containing the calculated final total.
    """
    inventory = {
        "item-101": {"name": "Premium Wireless Headphones", "price": 149.99, "stock": 15},
        "item-102": {"name": "Mechanical Gaming Keyboard", "price": 89.99, "stock": 5},
        "item-103": {"name": "Ergonomic Office Chair", "price": 249.99, "stock": 0},
    }
    item = inventory.get(item_id.lower().strip())
    if not item:
        return {"status": "ERROR", "message": f"Item '{item_id}' not found."}
    
    base_price = item["price"]
    subtotal = base_price * quantity
    # Cap discount rate between 0.0 and 1.0 to prevent mathematical boundary issues
    effective_discount_rate = min(1.0, max(0.0, discount_rate))
    discount_amount = subtotal * effective_discount_rate
    final_total = max(0.0, subtotal - discount_amount)
    
    return {
        "status": "SUCCESS",
        "item_id": item_id,
        "quantity": quantity,
        "subtotal": round(subtotal, 2),
        "discount_amount": round(discount_amount, 2),
        "final_total": round(final_total, 2)
    }


def charge_customer_card(amount: float) -> dict:
    """Charges the calculated amount to the customer's credit card.

    Args:
        amount: The final total amount to charge to the card.

    Returns:
        A dictionary indicating payment success or failure.
    """
    if amount < 0:
        raise ValueError(f"CRITICAL ERROR: Cannot charge a negative amount: {amount}!")
        
    return {
        "status": "SUCCESS",
        "transaction_id": "TXN-99882711-APPROVED",
        "charged_amount": amount,
        "message": "Payment captured successfully."
    }


catalog_agent = Agent(
    name="catalog_agent",
    description="Resolves item names to item IDs, lists store products, and gets pricing or inventory details.",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=(
        "You are an inventory and catalog specialist.\n"
        "You must:\n"
        "1. Help resolve natural language item names (like 'headphones' or 'keyboard') to their specific Item ID using list_available_items.\n"
        "2. Fetch full pricing and stock details using get_item_inventory once you have the Item ID.\n"
        "Always present clean, clear catalog and pricing details to the coordinator."
    ),
    tools=[list_available_items, get_item_inventory],
)

billing_agent = Agent(
    name="billing_agent",
    description="Validates promo codes, calculates final totals, and securely charges customer cards.",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=(
        "You are a billing and checkout specialist.\n"
        "You must:\n"
        "1. Validate promo codes using validate_coupon_code.\n"
        "2. Calculate subtotals and final totals using calculate_final_total.\n"
        "3. Charge the customer's card securely using charge_customer_card.\n"
        "Ensure checkout math is accurate, promotions are applied correctly, and transactions are securely finalized."
    ),
    tools=[validate_coupon_code, calculate_final_total, charge_customer_card],
)

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=(
        "You are the main checkout concierge. Help users buy items from our catalog.\n"
        "CRITICAL: You do NOT have any local tools to lookup items or perform checkout math. "
        "Instead, you must delegate all requests to your specialized sub-agents using the `transfer_to_agent` tool:\n"
        "1. To search items, find Item IDs, look up pricing, or check inventory stock: "
        "Call `transfer_to_agent` with agent_name='catalog_agent'. Do NOT try to call tools like `get_item_inventory` directly.\n"
        "2. To validate promo coupon codes, calculate final totals/discounts, or charge the customer's card: "
        "Call `transfer_to_agent` with agent_name='billing_agent'. Do NOT try to call tools like `calculate_final_total` directly.\n"
        "Coordinate smoothly to guide the customer from lookup to successful checkout. Keep your response user-friendly "
        "and professional."
    ),
    sub_agents=[catalog_agent, billing_agent],
)

app = App(
    root_agent=root_agent,
    name="app",
)
