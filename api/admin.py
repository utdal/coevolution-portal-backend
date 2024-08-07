from django.contrib import admin

from .models import APITaskMeta, MultipleSequenceAlignment, DirectCouplingAnalysis, ContactMap

admin.site.register(APITaskMeta)
admin.site.register(MultipleSequenceAlignment)
admin.site.register(DirectCouplingAnalysis)
admin.site.register(ContactMap)
