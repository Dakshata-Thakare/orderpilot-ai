from django.http import JsonResponse
from django.shortcuts import render,get_object_or_404
import json ,time
from orders.models import Order
from support.claude_agents import claude_run_support_agent
from support.gemini_agents import gemini_run_support_agent
from support.models import Conversation, Message

# Create your views here.
def chat(request,order_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_message = data.get("message")

        if not user_message:
            return JsonResponse({"error": "Empty message"},status=400)
        # print("user_message is ",user_message)

        order = get_object_or_404(Order,id=order_id,user=request.user)
        # print(request.user)
        # print(order.id)
        
        conversation,created = Conversation.objects.get_or_create(user=request.user,order=order)
        print(conversation)
        print(created)

        # 1. Save user message
        Message.objects.create(conversation=conversation,role="user",content=user_message)

        #2. send user message and conversation to LLM
        # reply = claude_run_support_agent(user_message,conversation.id,,order.id,request.user.id)
        reply = gemini_run_support_agent(user_message,conversation.id,order.id,request.user.id)

        #3. store the LLM reply
        Message.objects.create(conversation=conversation, role='assistant', content=reply)  #for claude assistant and user
        # Message.objects.create(conversation=conversation, role='model', content=reply)  #for gemini model and user ===>so instead of storing this everywhere I will simply change this in code because in future maybe i use the claude apis

        # time.sleep(2)
        return JsonResponse({"reply":reply})

    