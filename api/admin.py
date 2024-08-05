from django.contrib import admin

from .models import APITaskMeta, MultipleSequenceAlignment, DirectCouplingResults, ContactMap

admin.site.register(APITaskMeta)
admin.site.register(MultipleSequenceAlignment)
admin.site.register(DirectCouplingResults)
admin.site.register(ContactMap)
