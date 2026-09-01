from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import render,get_object_or_404
import json ,time ,queue
from orders.models import Order
from support.claude_agents import claude_run_support_agent
from support.gemini_agents import gemini_run_support_agent
from support.models import Conversation, Message
from django.contrib.admin.views.decorators import staff_member_required
from .event_queue import publish, subscribe,unsubscribe
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
        #for chat transcript
        event = {"type":"user_message","message":user_message}
        publish(conversation.id,event)

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

@staff_member_required
def dashboard(request):
    print("hii")
    conversations = Conversation.objects.all().order_by("-created_at")
    context = {
        'conversations':conversations
    }
    return render(request,"support/dashboard.html",context)


@staff_member_required
def conversation_detail(request,conversation_id):
    conversation = get_object_or_404(Conversation,id=conversation_id)
    messages = conversation.messages.order_by("created_at")
    agentlogs = conversation.agentlogs.order_by("created_at")
    print("conversation====> ",conversation)
    print("messages====> ",messages)
    print("agentlogs====> ",agentlogs)

    context = {
        "conversation": conversation,
        "messages": messages,
        "agentlogs":agentlogs
    }
    return render(request,"support/conversation_detail.html",context)

@staff_member_required
def conversation_stream(request, conversation_id):

    def event_stream(conversation_id):
        q = subscribe(conversation_id)
        try:
            while True:
                try:
                    event = q.get(timeout=15)

                    yield f"data: {json.dumps(event)}\n\n"

                except queue.Empty:
                    # SSE heartbeat
                    yield ": heartbeat\n\n"
        finally:
            unsubscribe(conversation_id, q)

    response = StreamingHttpResponse(event_stream(conversation_id),content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response

