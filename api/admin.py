from django.contrib import admin

from .models import APITaskMeta, SeedSequence, MultipleSequenceAlignment, DirectCouplingAnalysis, MappedDi, StructureContacts

admin.site.register(APITaskMeta)
admin.site.register(SeedSequence)
admin.site.register(MultipleSequenceAlignment)
admin.site.register(DirectCouplingAnalysis)
admin.site.register(MappedDi)
admin.site.register(StructureContacts)
