from django.contrib import admin

from .models import APITask, MSA, DirectCouplingResults, ContactMap

admin.site.register(APITask)
admin.site.register(MSA)
admin.site.register(DirectCouplingResults)
admin.site.register(ContactMap)
