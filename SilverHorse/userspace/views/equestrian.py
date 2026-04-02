from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Q
from ..models import EquestrianComplex, ComplexRating, Horse, Resource, ComplexResource
from ..forms import EquestrianComplexForm, RatingForm

@login_required
def equestrian_page(request):
    return render(request, 'userspace/equestrian/equestrian.html')

@login_required
def manage_complex(request):
    complex_obj, created = EquestrianComplex.objects.get_or_create(owner=request.user)

    if request.method == 'POST':
        form = EquestrianComplexForm(request.POST, instance=complex_obj)
        if form.is_valid():
            form.save()
            return redirect('manage_complex')
    else:
        form = EquestrianComplexForm(instance=complex_obj)

    return render(request, 'userspace/equestrian/equestrian.html', {'form': form, 'complex': complex_obj})


@login_required
def equestrian_page(request):
    user = request.user
    search_query = request.GET.get('search', '')

    # Отримати власний комплекс або None
    complex_obj = EquestrianComplex.objects.filter(owner=user).first()
    has_complex = complex_obj is not None

    # Форми
    complex_form = EquestrianComplexForm(instance=complex_obj)
    rating_form = RatingForm()

    # Отримати ВСІ комплекси для відображення в останньому розділі
    all_complexes = EquestrianComplex.objects.all()

    # Пошук по всіх комплексах (не тільки інших)
    if search_query:
        all_complexes = all_complexes.filter(
            Q(name__icontains=search_query) |
            Q(owner__username__icontains=search_query)
        )

    # POST обробка
    if request.method == 'POST':
        # 🎯 СТВОРЕННЯ КОМПЛЕКСУ
        if 'create_complex' in request.POST and not has_complex:
            try:
                # Створюємо комплекс з default значеннями
                EquestrianComplex.objects.create(
                    owner=user,
                    name=f"Комплекс {user.username}",
                    location='forest',
                    prestige=0
                )
                messages.success(request, "Комплекс успішно створено!")
                return redirect('equestrian_page')
            except Exception as e:
                messages.error(request, f"Помилка при створенні комплексу: {str(e)}")
                return redirect('equestrian_page')

        # 📝 РЕДАГУВАННЯ існуючого комплексу
        elif 'create_complex' in request.POST and has_complex:
            complex_form = EquestrianComplexForm(request.POST, instance=complex_obj)
            if complex_form.is_valid():
                complex_form.save()
                messages.success(request, "Комплекс оновлено!")
                return redirect('equestrian_page')

        # ⭐ ОЦІНКА іншого комплексу
        elif 'rating_submit' in request.POST:
            rating_form = RatingForm(request.POST)
            complex_id = request.POST.get('complex_id')
            target_complex = get_object_or_404(EquestrianComplex, id=complex_id)

            if rating_form.is_valid():
                rating_value = rating_form.cleaned_data['rating']
                if target_complex.owner != user:
                    ComplexRating.objects.update_or_create(
                        complex=target_complex,
                        user=user,
                        defaults={'rating': rating_value}
                    )
                    messages.success(request, f"Ви оцінили комплекс {target_complex.name}!")
                else:
                    messages.error(request, "Власник не може оцінювати свій комплекс.")
            return redirect('equestrian_page')

    # Середній рейтинг власного комплексу
    average_rating = None
    if has_complex and complex_obj.ratings.exists():
        average_rating = round(complex_obj.ratings.aggregate(Avg('rating'))['rating__avg'], 2)

    # Обчислити середній рейтинг для всіх комплексів
    for c in all_complexes:
        if c.ratings.exists():
            c.avg_rating = round(c.ratings.aggregate(Avg('rating'))['rating__avg'], 2)
        else:
            c.avg_rating = None

    # Отримати інші комплекси для пошукового розділу
    other_complexes = all_complexes.exclude(owner=user) if search_query else []

    context = {
        'complex_obj': complex_obj,
        'has_complex': has_complex,
        'complex_form': complex_form,
        'rating_form': rating_form,
        'average_rating': average_rating,
        'all_complexes': all_complexes,  # Всі комплекси для останнього розділу
        'other_complexes': other_complexes,  # Результати пошуку
        'search_query': search_query,
        'user': user,
    }

    return render(request, 'userspace/equestrian/equestrian.html', context)


@login_required
def storage_view(request):
    # Отримуємо комплекс поточного користувача
    complex_obj = EquestrianComplex.objects.filter(owner=request.user).first()
    if not complex_obj:
        messages.error(request, "У вас немає власного комплексу.")
        return redirect('equestrian_page')

    # Отримуємо всі ресурси, які є в системі
    all_resources = Resource.objects.all()

    # Для кожного ресурсу отримуємо його кількість у комплексі
    resources_data = []
    for res in all_resources:
        try:
            complex_res = ComplexResource.objects.get(complex=complex_obj, resource=res)
            quantity = complex_res.quantity
        except ComplexResource.DoesNotExist:
            quantity = 0
        resources_data.append({
            'resource': res,
            'quantity': quantity,
        })

    return render(request, 'userspace/shop/storage.html', {
        'complex': complex_obj,
        'resources': resources_data,
    })