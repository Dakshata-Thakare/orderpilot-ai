
from google import genai
from google.genai import types
from django.conf import settings
from .tools import get_order_details,get_refund_history,check_delivery_status
from .models import Conversation, Message, AgentLog

#Initialize Gemini client
client = genai.Client(api_key=settings.GEMINI_API_KEY)
gemini_model = settings.GEMINI_MODEL


#SUPPORT SYSTEM PROMPT ---> Maya's job description
SUPPORT_SYSTEM_PROMPT = """
You are Maya, a customer support agent at CoolBreeze AC.
You help customers with issues related to their AC orders.

Your responsibilities:
- Always use your tools to gather facts before responding
- Check order details when customer mentions their order
- Check refund history before making any refund decisions
- Be empathetic but honest

Your personality:
- Friendly and Professional
- Patient even when customer is angry
- Clear and consise in your replies

Important rules:
- Always check order details first before responding
- Never approve or deny a refund yourself
- If refund decision is needed - tell customer you are checking with your team
"""


MANAGER_SYSTEM_PROMPT = """
You are a senior support manager at CoolBreeze AC.
A support agent has escalated a customer case to you for a refund decision.

Your responsibilities:
- Review the case summary carefully
- Consider the customer's refund history
- Make a fair and final refund decision
- Give a clear reason for your decision

Your decision options:
- Approve refund — if the case is genuine and within policy
- Deny refund — if the case is suspicious or outside policy
- Escalate to risk team — if you suspect fraud

Important rules:
- Be fair but firm
- Base decision on facts — not emotions
- Always give a specific reason for your decision
- Keep your response concise and professional
"""


#SUPPORT TOOLS ----> Tool schemas,that ai agents will read
SUPPORT_TOOLS = [
    {
        "name": "get_order_details",
        "description": "Fetch complete order details including status, carrier, tracking number and days since order was placed. Use this when customer mentions their order or complains about delivery.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "integer",
                    "description": "The order ID to look up"
                }
            },
            "required": ["order_id"]
        }
    },

    {
        "name": "get_refund_history",
        "description": "Get complete refund history for a user. Use this before making any refund related decisions.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "integer",
                    "description": "The user ID to check refund history for"
                }
            },
            "required": ["user_id"]
        }
    },

    {
        "name": "check_delivery_status",
        "description": "Check current delivery status using tracking number and carrier. Use this when customer complains about delayed or missing delivery.",
        "parameters": {
            "type": "object",
            "properties": {
                "tracking_number": {
                    "type": "string",
                    "description": "The shipment tracking number"
                },
                "carrier": {
                    "type": "string",
                    "description": "The carrier name for example BlueDart or Delhivery"
                }
            },
            "required": ["tracking_number", "carrier"]
        }
    },

    {
        "name": "escalate_to_manager",
        "description": "Escalate the case to manager for refund decision. Always include customer's user_id in the case summary so manager can assess fraud risk accurately.",
        "parameters": {
            "type": "object",
            "properties": {
                "case_summary": {
                    "type": "string",
                    "description": "Complete case summary. Must include: customer user_id, order details, refund history and complaint. Format: Start with 'Customer User ID: X' on the first line."
                }
            },
            "required": ["case_summary"]
        }
    },

    # {
    #     "name": "search_knowledge_base",
    #     "description": "Search CoolBreeze AC company documents including refund policy, warranty policy, and product FAQs. Use this when customer asks about company policies, warranty coverage, warranty claims, refund eligibility, or any general product information that requires accurate company documentation.",
    #     "parameters": {
    #         "type": "object",
    #         "properties": {
    #             "query": {
    #                 "type": "string",
    #                 "description": "The search query to find relevant information from company documents. Be specific — for example 'refund eligibility within 30 days' instead of just 'refund'."
    #             }
    #         },
    #         "required": ["query"]
    #     }
    # }


]


# MANAGER_TOOLS = [
#     {
#         "name": "assess_fraud_risk",
#         "description": "Consult the risk agent to assess fraud risk for a customer. Use this when refund request looks suspicious or customer has multiple refund requests. Pass the user_id to get a risk verdict.",
#         "parameters": {
#             "type": "object",
#             "properties": {
#                 "user_id": {
#                     "type": "integer",
#                     "description": "The user ID to assess fraud risk for"
#                 }
#             },
#             "required": ["user_id"]
#         }
#     }
# ]


# RISK_TOOLS = [
#     {
#         "name": "get_customer_risk_profile",
#         "description": "Get complete risk profile for a customer including order history, refund patterns and ratio. Use this to assess fraud risk.",
#         "parameters": {
#             "type": "object",
#             "properties": {
#                 "user_id": {
#                     "type": "integer",
#                     "description": "The user ID to assess risk for"
#                 }
#             },
#             "required": ["user_id"]
#         }
#     }
# ]

tools = types.Tool(
    function_declarations=SUPPORT_TOOLS
)

#execute_tool() ----> bridge between claude and python functions (tools)
def execute_tool(tool_name,tool_input):
    if tool_name == "get_order_details":
        return get_order_details(tool_input["order_id"])

    if tool_name == "get_refund_history":
        return get_refund_history(tool_input["user_id"])

    if tool_name == "check_delivery_status":
        return check_delivery_status(tool_input["tracking_number"],tool_input["carrier"])

    if tool_name == "escalate_to_manager":
        case_summary = tool_input["case_summary"]
        print("escalating to manager ====> ",case_summary)
        decision = gemini_run_manager_agent(case_summary)
        print("decision===> ",decision)
        return decision



#Agent Loop ----> while loop that loops until the task is done
def gemini_run_support_agent(user_message,conversation_id,order_id,user_id):
    conv = Conversation.objects.get(id=conversation_id)

    conversation_messages = []

    for msg in conv.messages.order_by("created_at"):

        # Gemini user "user" and "model"
        role = "model" if msg.role == "assistant" else "user"

        # conversation_messages.append({
        #     "role": role,
        #     "parts": [
        #         {
        #             "text" : msg.content
        #         }
        #     ]
        # })
        conversation_messages.append(
            types.Content(
                role=role,
                parts=[
                    types.Part.from_text(text=msg.content)
                ]
            )
        )


    while True:
        #send this conversation to LLM
        response = client.models.generate_content(
            model = gemini_model,
            contents = conversation_messages,
            config=types.GenerateContentConfig(
                system_instruction=(SUPPORT_SYSTEM_PROMPT + f"\n\nContext: This conversation is about Order: #{order_id}, user: {user_id}"
            ),
            tools=[tools]
            )
        )
        print("response===> ",response)

        # Check if Gemini wants a tool
        function_calls = response.function_calls

        if function_calls:
            #add gemini's response containing the function call to conversation
            conversation_messages.append(
                response.candidates[0].content
            )

            tool_responses = []
            #execute each requested tool
            for function_call in function_calls:
                print("tool call ====> ",function_call.name)
                print("tool input ===> ",function_call.args)

                result = execute_tool(function_call.name,function_call.args)
                print("tool result ====> ",result)

                tool_responses.append(
                    types.Part.from_function_response(
                        name=function_call.name,
                        response={
                            "result":result
                        }
                    )
                )

            #adding tool result to conversation
            conversation_messages.append(
                types.Content(
                    role="user",
                    parts=tool_responses
                )
            )
            continue

        # print("llm response  ===> ",response)
        # print("FULL RESPONSE:", response)
        # print("TEXT:", repr(response.text))
        # print("CANDIDATES:", response.candidates)
        # print("PROMPT FEEDBACK:", response.prompt_feedback)
        return response.text

def gemini_run_manager_agent(case_summary):
    # Whenever we send a message to our agent, we always use the "user" role, not the "assistant" role, because the message is an input to the agent.
    print("case_summary--===> ",case_summary)
    manager_messages = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=case_summary)
            ]
        )
    ]

    while True:
        response = client.models.generate_content(
            model = gemini_model,
            contents=manager_messages,
            config = types.GenerateContentConfig(
                system_instruction=(MANAGER_SYSTEM_PROMPT)
            )
        )

        function_calls = response.function_calls
        if not function_calls:
            return response.text

        tool_results = []
        for block in function_calls:
            if block.type == 'tool_use':
                result = execute_tool(block.name,block.args)
                tool_results.append(
                    types.Part.from_function_response(
                        name = block.name, 
                        response = {
                            "result":result
                        }
                    )
                )

            manager_messages.append(response.candidates[0].content)

            manager_messages.append(
                types.Content(
                    role = "user",
                    parts = tool_results
                )
            )
