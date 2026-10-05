from django.contrib import admin

from .models import (
    APITaskMeta,
    DirectCouplingAnalysis,
    MappedDi,
    MultipleSequenceAlignment,
    SeedSequence,
    StructureContacts,
)

admin.site.register(APITaskMeta)
admin.site.register(SeedSequence)
admin.site.register(MultipleSequenceAlignment)
admin.site.register(DirectCouplingAnalysis)
admin.site.register(MappedDi)
admin.site.register(StructureContacts)
