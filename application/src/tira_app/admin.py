from django.contrib import admin

from . import model as modeldb

# Register your models here.

admin.site.register(modeldb.TransactionLog)
admin.site.register(modeldb.TransitionLog)
admin.site.register(modeldb.EvaluationLog)
admin.site.register(modeldb.Organizer)
admin.site.register(modeldb.VirtualMachine)
