from django.contrib import admin

from django.contrib import admin
from .models import Conversation,Message,AgentLog

# Register your models here.
admin.site.register(Conversation)
admin.site.register(Message)
admin.site.register(AgentLog)