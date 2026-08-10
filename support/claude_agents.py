
from anthropic import Anthropic
from django.conf import settings
from .tools import get_order_details,get_refund_history,check_delivery_status
from .models import Conversation, Message, AgentLog

#Initialize Anthropic client

client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
anthropic_model = settings.ANTHROPIC_MODEL



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






#SUPPORT TOOLS ----> Tool schemas,that ai agents will read
SUPPORT_TOOLS = [
    {
        "name": "get_order_details",
        "description": "Fetch complete order details including status, carrier, tracking number and days since order was placed. Use this when customer mentions their order or complains about delivery.",
        "input_schema": {
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
        "input_schema": {
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
        "input_schema": {
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
    }
    # ,

    # {
    #     "name": "escalate_to_manager",
    #     "description": "Escalate the case to manager for refund decision. Always include customer's user_id in the case summary so manager can assess fraud risk accurately.",
    #     "input_schema": {
    #         "type": "object",
    #         "properties": {
    #             "case_summary": {
    #                 "type": "string",
    #                 "description": "Complete case summary. Must include: customer user_id, order details, refund history and complaint. Format: Start with 'Customer User ID: X' on the first line."
    #             }
    #         },
    #         "required": ["case_summary"]
    #     }
    # },

    # {
    #     "name": "search_knowledge_base",
    #     "description": "Search CoolBreeze AC company documents including refund policy, warranty policy, and product FAQs. Use this when customer asks about company policies, warranty coverage, warranty claims, refund eligibility, or any general product information that requires accurate company documentation.",
    #     "input_schema": {
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
#         "input_schema": {
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
#         "input_schema": {
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



#execute_tool() ----> bridge between claude and python functions (tools)
def execute_tool(tool_name,tool_input):
    if tool_name == "get_order_details":
        return get_order_details(tool_input["order_id"])

    if tool_name == "get_refund_history":
        return get_refund_history(tool_input["user_id"])

    if tool_name == "check_delivery_status":
        return check_delivery_status(tool_input["tracking_number"],tool_input["carrier"])



#Agent Loop ----> while loop that loops until the task is done
def claude_run_support_agent(user_message,conversation_id,order_id,user_id):
    conv = Conversation.objects.get(id=conversation_id)

    conversation_messages = []
    for msg in conv.messages.order_by("created_at"):
        conversation_messages.append({
            "role": msg.role,
            "content":msg.content
        })

    while True:
        #send this conversation to LLM
        response = client.messages.create(
            model=anthropic_model,
            max_tokens=1024,
            system=SUPPORT_SYSTEM_PROMPT + f"\n\nContext: This conversation is about Order: #{order_id}, user: {user_id}",
            tools=SUPPORT_TOOLS,
            messages=conversation_messages
        )

        '''
        response==> Message(id='msg_01XjHybzdVsX9L8izYAeXMbU', container=None, content=[TextBlock(citations=None, text='Let me check your details right away.', type='text'), ToolUseBlock(id='toolu_015XvP6G9MmnWkR68cre2sUCf', caller=DirectCaller(type='direct'), input={'order_id': 2}, name='get_order_details', type='tool_use')], model='claude-sonnet-4-6', role='assistant', stop_details=None, stop_reason='tool_use', type='message', usage=Usage(cache_creation_input_tokens=0, cache_creation_ephemeral_input_tokens=0, cache_read_input_tokens=0, inference_geo='global', input_tokens=1859, output_tokens=67, server=None, service_tier='standard')
        if the stop_reason is tool_use ==> Claude wants your application to execute a tool/function before it can continue.
        if the stop_reason is end_user ==>Claude has finished its response and is waiting for the user/application to continue.
        '''
        print("response===> ",response)
        print("stop_reason===> ",response.stop_reason)
        print("content====>",response.content)

        if response.stop_reason == 'tool_use':
            tool_result = []
            for block in response.content:
                if block.type == 'tool_use':
                    '''
                        tool call==> get_order_details
                        tool input ==> {'order_id': 3}
                        tool result {'order_id': 3, 'product_name': 'CoolBreeze AC Voltage Stabilizer 5KVA', 'amount': '4999.00', 'status': 'delivered', 'carrier': 'Delhivery', 'tracking_number': 'DL88103742', 'delivery_address': '14, Residency Road, Shivajinagar, Bangalore - 560025', 'ordered_on': '16 Feb 2025', 'days_since_order': 465}

                        tool call==> get_refund_history
                        tool input ==> {'user_id': 2}
                        tool result {'total_refund_requests': 3, 'history': [
                            {'order_id': 1, 'product': 'CoolBreeze 1.5 Ton 5 Star Inverter Split AC', 'reason': 'AC dispatched 5 days ago but not delivered yet. Want refund.', 'status': 'pending', 'requested_on': '30 Apr 2025'},
                            {'order_id': 2, 'product': 'CoolBreeze 1.5 Ton 3 Star Split AC', 'reason': 'AC is making loud noise during operation. Not acceptable.', 'status': 'denied', 'requested_on': '20 Mar 2025'},
                            {'order_id': 3, 'product': 'CoolBreeze AC Voltage Stabilizer 5KVA', 'reason': 'Stabilizer stopped working after 3 days. AC not turning on.', 'status': 'approved', 'requested_on': '20 Feb 2025'}
                        ]}
                    '''
                    print("tool call ====> ",block.name)   #Gives you the name of the tool Claude wants to call
                    print("tool input ====> ",block.input) #Gives you the arguments Claude wants to pass to your tool

                    #execute the tool
                    result = execute_tool(block.name,block.input)
                    print("tool result ",result)
                    tool_result.append({
                        "type":"tool_result",
                        "tool_use_id": block.id,
                        "content":str(result)
                    })
            conversation_messages.append({
                "role":"assistant",
                "content": response.content
            })
            
            conversation_messages.append({
                "role":"user",
                "content": tool_result
            })
        else:
            return response.content[0].text

                    
        # final_text = response.content[0].text
        # return final_text
