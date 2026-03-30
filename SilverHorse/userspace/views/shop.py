from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction  # <-- додайте імпорт
from ..models import Resource, ComplexResource, EquestrianComplex, Profile


@login_required
def shop_view(request):
    # Перевірка наявності комплексу
    complex_obj = EquestrianComplex.objects.filter(owner=request.user).first()
    if not complex_obj:
        messages.error(request, "Спочатку створіть кінний комплекс!")
        return redirect('equestrian_page')

    # Фільтр за типом ресурсу
    resource_type = request.GET.get('type', '')
    if resource_type in dict(Resource.TYPE_CHOICES):
        resources = Resource.objects.filter(type=resource_type)
    else:
        resources = Resource.objects.all()

    # Підготовка даних для шаблону
    resources_data = []
    for res in resources:
        try:
            complex_res = ComplexResource.objects.get(complex=complex_obj, resource=res)
            quantity = complex_res.quantity
        except ComplexResource.DoesNotExist:
            quantity = 0
        resources_data.append({
            'resource': res,
            'quantity': quantity,
        })

    # Обробка покупки
    if request.method == 'POST':
        resource_id = request.POST.get('resource_id')
        quantity = int(request.POST.get('quantity', 1))
        if quantity <= 0:
            messages.error(request, "Кількість має бути більше 0.")
            return redirect('shop')

        resource = get_object_or_404(Resource, id=resource_id)
        total_price = resource.price * quantity

        # 🔒 Вся операція в одній транзакції з блокуванням рядків
        with transaction.atomic():
            # Отримуємо профіль з блокуванням
            profile = Profile.objects.select_for_update().get(user=request.user)
            if profile.horseshoes >= total_price:
                # Знімаємо кошти
                profile.horseshoes -= total_price
                profile.save()

                # Отримуємо або створюємо запис ресурсу в комплексі з блокуванням
                complex_res, created = ComplexResource.objects.select_for_update().get_or_create(
                    complex=complex_obj, resource=resource,
                    defaults={'quantity': 0}
                )
                complex_res.quantity += quantity
                complex_res.save()

                messages.success(request, f"Ви купили {quantity} x {resource.name} за {total_price} підков!")
            else:
                messages.error(request, f"Недостатньо коштів. Потрібно {total_price}, у вас {profile.horseshoes}.")

        # Після транзакції перенаправляємо назад
        return redirect(request.path + (f"?type={resource_type}" if resource_type else ""))

    context = {
        'resources_data': resources_data,
        'complex': complex_obj,
        'resource_type': resource_type,
        'resource_types': Resource.TYPE_CHOICES,
    }
    return render(request, 'userspace/shop.html', context)