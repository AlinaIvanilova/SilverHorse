from django.contrib import admin
from django.contrib.auth.models import User
from .models import SystemMessage, Message, Note, BlockedUser
from .models import Profile
from .models import Horse

# -------------------------
# Повідомлення між користувачами
# -------------------------
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'text', 'created_at')
    search_fields = ('sender__username', 'receiver__username', 'text')


# -------------------------
# Дія для надсилання системного повідомлення всім користувачам
# -------------------------
@admin.action(description="Надіслати обране повідомлення всім користувачам")
def send_to_all_users(modeladmin, request, queryset):
    for msg in queryset:
        for user in User.objects.all():
            SystemMessage.objects.create(
                user=user,
                title=msg.title,
                content=msg.content
            )
    modeladmin.message_user(request, "Системне повідомлення надіслано всім користувачам!")


# -------------------------
# Системні повідомлення
# -------------------------
class SystemMessageAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'created_at', 'is_read')
    search_fields = ('title', 'content', 'user__username')
    actions = [send_to_all_users]


admin.site.register(SystemMessage, SystemMessageAdmin)
admin.site.register(Note)
admin.site.register(BlockedUser)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'horseshoes', 'silver_wings')
    list_editable = ('horseshoes', 'silver_wings')


# -------------------------
# Реєстрація моделі Horse (проста, без зайвих налаштувань)
# -------------------------
@admin.register(Horse)
class HorseAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'age', 'status', 'last_sleep', 'last_sleep_processed')
    list_filter = ('status', 'gender')
    search_fields = ('name', 'owner__username')
    fieldsets = (
        (None, {'fields': ('name', 'owner', 'breed', 'gender', 'coat_color', 'age', 'status', 'price')}),
        ('Характеристики', {'fields': ('speed', 'endurance', 'strength', 'health', 'energy', 'mood')}),
        ('Сон', {'fields': ('last_sleep', 'last_sleep_processed', 'energy_at_sleep')}),
    )