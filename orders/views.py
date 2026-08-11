from django.shortcuts import get_object_or_404, render
from . models import Order,RefundRequest
from django.contrib.auth.decorators import login_required
from support.models import Conversation

# Create your views here.
@login_required
def orders_list(request):
    orders = Order.objects.filter(user=request.user)
    context = {
        'orders':orders,
    }
    return render(request,'orders_list.html',context)

@login_required
def order_detail(request,order_id):
    order = get_object_or_404(Order,id=order_id,user=request.user)
    refunds = RefundRequest.objects.filter(order=order)

    try:
        conversation = Conversation.objects.get(user=request.user,order=order)
        previous_messages = conversation.messages.order_by("created_at")
    except Conversation.DoesNotExist:
        conversation = None
        previous_messages = []

    context = {
        'order':order,
        'refunds':refunds,
        'conversation':conversation,
        'previous_messages':previous_messages,
    }
    # print("order:::::::::::::::: ", context['order'])
    return render(request,"order_detail.html",context)