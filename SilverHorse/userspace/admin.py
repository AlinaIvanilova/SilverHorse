from django.contrib import admin
from django.contrib.auth.models import User
from django.utils import timezone  # додано
from .models import SystemMessage, Message, Note, BlockedUser
from .models import Profile
from .models import Horse
from .models import Competition, CompetitionRegistration


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
# Реєстрація моделі Horse
# -------------------------
class CompetitionRegistrationInline(admin.TabularInline):
    model = CompetitionRegistration
    extra = 0
    fields = ('competition', 'status', 'result_place', 'score', 'reward_horseshoes')
    readonly_fields = ('registered_at',)
    can_delete = True


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
    inlines = [CompetitionRegistrationInline]


# -------------------------
# Дія для примусового завершення змагань
# -------------------------
@admin.action(description="Завершити обрані змагання прямо зараз")
def force_finish_competition(modeladmin, request, queryset):
    for comp in queryset:
        if not comp.is_active:
            modeladmin.message_user(request, f"Змагання {comp} вже неактивне.", level='warning')
            continue
        # Якщо час початку ще не настав, зсуваємо в минуле
        if comp.start_time > timezone.now():
            comp.start_time = timezone.now() - timezone.timedelta(hours=1)
            comp.end_time = timezone.now() + timezone.timedelta(minutes=1)
            comp.save()
        try:
            comp.process_results()
            modeladmin.message_user(request, f"Змагання {comp} завершено, результати оброблено.")
        except Exception as e:
            modeladmin.message_user(request, f"Помилка при обробці {comp}: {e}", level='error')


# -------------------------
# Реєстрація моделі Competition
# -------------------------
@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'competition_type', 'start_time', 'end_time',
        'is_active', 'max_participants', 'energy_cost'
    )
    list_filter = ('competition_type', 'is_active', 'start_time')
    search_fields = ('name', 'description')
    ordering = ('-start_time',)
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Основна інформація', {
            'fields': ('name', 'competition_type', 'description', 'is_active', 'created_at')
        }),
        ('Дата та час', {
            'fields': ('start_time', 'end_time')
        }),
        ('Вимоги та навички', {
            'fields': ('primary_skill', 'secondary_skill')
        }),
        ('Умови участі', {
            'fields': ('max_participants', 'energy_cost')
        }),
    )
    actions = [force_finish_competition]  # <-- додано дію


# -------------------------
# Окрема реєстрація для CompetitionRegistration
# -------------------------
@admin.register(CompetitionRegistration)
class CompetitionRegistrationAdmin(admin.ModelAdmin):
    list_display = (
        'horse', 'competition', 'status', 'registered_at',
        'result_place', 'score', 'reward_horseshoes'
    )
    list_filter = ('status', 'competition__competition_type', 'registered_at')
    search_fields = ('horse__name', 'competition__name')
    autocomplete_fields = ('horse', 'competition')
    readonly_fields = ('registered_at',)