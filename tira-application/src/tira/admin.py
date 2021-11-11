from django.contrib import admin
from .transitions import TransactionLog, TransitionLog, EvaluationLog

# Register your models here.

admin.site.register(TransactionLog)
admin.site.register(TransitionLog)
admin.site.register(EvaluationLog)