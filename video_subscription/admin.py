from django.contrib import admin
from django.apps import apps


def register_all_app_models():  
   models_to_ignore = [  
       'admin.LogEntry',  
       'contenttypes.ContentType',  
       'sessions.Session',  
       'authtoken.TokenProxy',  
       'authtoken.Token',  # We automatically register the authtoken app models.  
   ]  
   for model in apps.get_models():
       try:
            if model._meta.label in models_to_ignore:
                continue
            else:
                @admin.register(model)
                class TraderAdmin(admin.ModelAdmin):
                    list_display = [f.name for f in model._meta.fields]

       except admin.sites.AlreadyRegistered:
            pass

register_all_app_models()