from django.contrib import admin
from django.contrib.auth.models import User
from .models import SystemMessage, Message, Note, BlockedUser
from .models import Profile

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
        # Надсилаємо всім користувачам, окрім автора (опціонально)
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


# -------------------------
# Реєстрація моделей
# -------------------------
admin.site.register(SystemMessage, SystemMessageAdmin)
admin.site.register(Note)
admin.site.register(BlockedUser)





@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'horseshoes', 'silver_wings')
    list_editable = ('horseshoes', 'silver_wings')


