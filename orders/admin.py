from django.contrib import admin

# Register your models here.
from .models import Product,Order,RefundRequest

admin.site.register(Product)
admin.site.register(Order)
admin.site.register(RefundRequest)

