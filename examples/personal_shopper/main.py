import datetime
import random

import database
from anthill import Agent
from anthill.types import AgentFunction
from anthill.repl import run_demo_loop

class RefundItem(AgentFunction):
    user_id: int
    item_id: int

    def run(self, **kwargs):
        """Initiate a refund based on the user ID and item ID.
        Takes as input arguments in the format '{"user_id":"1","item_id":"3"}'
        """
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT amount FROM PurchaseHistory
            WHERE user_id = ? AND item_id = ?
        """,
            (self.user_id, self.item_id),
        )
        result = cursor.fetchone()
        if result:
            amount = result[0]
            output = f"Refunding ${amount} to user ID {self.user_id} for item ID {self.item_id}."
        else:
            output = f"No purchase found for user ID {self.user_id} and item ID {self.item_id}."
        print(output)
        return output

class NotifyCustomer(AgentFunction):
    user_id: int
    method: str

    def run(self, **kwargs):
        """Notify a customer by their preferred method of either phone or email.
        Takes as input arguments in the format '{"user_id":"1","method":"email"}'"""

        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT email, phone FROM Users
            WHERE user_id = ?
        """,
            (self.user_id,),
        )
        user = cursor.fetchone()
        if user:
            email, phone = user
            if self.method == "email" and email:
                output = f"Emailed customer {email} a notification."
            elif self.method == "phone" and phone:
                output = f"Texted customer {phone} a notification."
            else:
                output = f"No {self.method} contact available for user ID {self.user_id}."
        else:
            output = f"User ID {self.user_id} not found."
        print(output)
        return output

class OrderItem(AgentFunction):
    user_id: int
    product_id: int

    def run(self, **kwargs):
        """Place an order for a product based on the user ID and product ID.
        Takes as input arguments in the format '{"user_id":"1","product_id":"2"}'"""
        date_of_purchase = datetime.datetime.now()
        item_id = random.randint(1, 300)

        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT product_id, product_name, price FROM Products
            WHERE product_id = ?
        """,
            (self.product_id,),
        )
        result = cursor.fetchone()
        if result:
            product_id, product_name, price = result
            output = f"Ordering product {product_name} for user ID {self.user_id}. The price is {price}."
            
            # Add the purchase to the database
            database.add_purchase(self.user_id, date_of_purchase, item_id, price)
        else:
            output = f"Product {self.product_id} not found."
        print(output)
        return output


# Initialize the database
database.initialize_database()

# Preview tables
database.preview_table("Users")
database.preview_table("PurchaseHistory")
database.preview_table("Products")

# Define the agents

refunds_agent = Agent(
    name="Refunds Agent",
    model="groq/llama-3.1-70b-versatile",
    instructions=f"""You are a refund agent that handles all actions related to refunds after a return has been processed.
    You must ask for both the user ID and item ID to initiate a refund. Ask for both user_id and item_id in one message.
    If the user asks you to notify them, you must ask them what their preferred method of notification is. For notifications, you must
    ask them for user_id and method in one message.""",
    functions=[RefundItem, NotifyCustomer],
)

sales_agent = Agent(
    name="Sales Agent",
    model="groq/llama-3.1-70b-versatile",
    instructions=f"""You are a sales agent that handles all actions related to placing an order to purchase an item.
    Regardless of what the user wants to purchase, must ask for BOTH the user ID and product ID to place an order.
    An order cannot be placed without these two pieces of information. Ask for both user_id and product_id in one message.
    If the user asks you to notify them, you must ask them what their preferred method is. For notifications, you must
    ask them for user_id and method in one message.
    """,
    functions=[OrderItem, NotifyCustomer],
)

triage_agent = Agent(
    name="Triage Agent",
    model="groq/llama-3.1-70b-versatile",
    instructions=f"""You are to triage a users request, and call a tool to transfer to the right intent.
    Once you are ready to transfer to the right intent, call the tool to transfer to the right intent.
    You dont need to know specifics, just the topic of the request.
    If the user request is about making an order or purchasing an item, transfer to the Sales Agent.
    If the user request is about getting a refund on an item or returning a product, transfer to the Refunds Agent.
    When you need more information to triage the request to an agent, ask a direct question without explaining why you're asking it.
    Do not share your thought process with the user! Do not make unreasonable assumptions on behalf of user.""",
)

triage_agent.transfers = [sales_agent, refunds_agent]
sales_agent.transfers = [triage_agent]
refunds_agent.transfers = [triage_agent]

for f in triage_agent.functions:
    print(f.__name__)

if __name__ == "__main__":
    # Run the demo loop
    run_demo_loop(starting_agent=triage_agent, debug=False)
