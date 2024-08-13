from django.shortcuts import render, redirect
from .models import Ticket, Document, get_default_technician, technician_group
from django.views.generic.edit import CreateView
from .forms import TicketForm, LoginForm
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.contrib.auth.views import LogoutView
from django.views.decorators.cache import never_cache
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.core.mail import send_mail
from django.contrib.auth import login
import pytz
import datetime

email_host_user = 'email_host_user'

class TicketCreateView(LoginRequiredMixin, CreateView):
    template_name = 'desk/create.html'
    form_class = TicketForm
    success_url = reverse_lazy('index')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        documents = self.request.FILES.getlist('documents')
        document_names = self.request.POST.getlist('document_names')
        for document, name in zip(documents, document_names):
            if document:
                doc = Document(ticket=form.instance, file=document)
                doc.file.name = name
                doc.save()
        try:
            technician_email = get_default_technician().email
            subject = 'Поступила новая заявка по Административно-хозяйственной службе'
            message = 'Поступила заявка с темой "{}"'.format(form.cleaned_data['title'])
            from_email = email_host_user
            send_mail(subject, message, from_email, [technician_email])
        except:
            pass
        return response
        

class MyLogoutView(LogoutView):
    next_page = reverse_lazy('login')

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)

        previous_page = request.session.pop('previous_page', None)

        return response if previous_page is None else redirect(previous_page)

def Login_View(request):
    error_message = None
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username'].verbose_name
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('index')
            else:
                error_message = "Неверный логин или пароль"
    else:
        form = LoginForm()
    return render(request, 'desk/login.html', {'form': form, 'error_message': error_message})


@never_cache
@login_required
def index(request):
    if request.user.groups.filter(name=technician_group).exists():
        tickets = Ticket.objects.all()  # отображаем все заявки для пользователей с соответствующими правами
    else:
        tickets = Ticket.objects.filter(created_by=request.user)  # отображаем только заявки, созданные текущим пользователем

    #print(request.user.has_perm('app.view_all_tickets'))
    #не работает данный фильтр - request.user.has_perm('app.view_all_tickets'), так что все техники должны иметь группу technician_group

    title = request.GET.get('title')
    created_by = request.GET.get('created_by')
    criticalness = request.GET.get('criticalness')
    technician = request.GET.get('technician')
    status = request.GET.get('status')
    progress = request.GET.get('progress')
    published_start = request.GET.get('published_start')
    published_end = request.GET.get('published_end')

    if title:
        tickets = tickets.filter(title__icontains=title)
    if created_by:
        tickets = tickets.filter(created_by__profile__verbose_name__icontains=created_by)
    if criticalness:
        try:
            tickets = tickets.filter(criticalness=Ticket.Kinds[criticalness])
        except ObjectDoesNotExist:
            pass
    if technician:
        tickets = tickets.filter(technician__profile__verbose_name__icontains=technician)
    if status:
        if status == "any":
            tickets = tickets.filter(status__in=[status[0] for status in Ticket.Status.choices])  # показываем все заявки
        else:
            tickets = tickets.filter(status=Ticket.Status[status])
    if progress:
        tickets = tickets.filter(progress=Ticket.Progres[progress])
    if published_start:
        tickets = tickets.filter(published__gte=published_start)
    if published_end:
        tickets = tickets.filter(published__lte=published_end)
    if status:
        if status == "any":
            tickets = tickets.all()
        else:
            tickets = tickets.filter(status=Ticket.Status[status])
    else:
        tickets = tickets.filter(status=Ticket.Status.OPENED)

    return render(request, 'desk/index.html', {
        'tickets': tickets,
        'status_choices': [
            ('CLOSED', 'Закрыта'),
            ('any', 'Любой')
        ],
        'progress_choices': [
            ('IMPOSSIBLE', 'Невозможно выполнить'),
            ('ACCEPTED', 'Принято к рассмотрению'),
            ('INPROGRESS', 'В стадии решения'),
            ('DECIDED', 'Успешно решено')
        ],
        'title': title,
        'created_by': created_by,
        'criticalness': criticalness,
        'technician': technician,
        'status': status,
        'progress': progress,
        'published_start': published_start,
        'published_end': published_end,
    })


@login_required
@user_passes_test(lambda user, **kwargs: user.has_perm('app.view_all_tickets') or user.groups.filter(name=technician_group).exists() or user.is_staff or user.is_superuser or Ticket.objects.filter(created_by=user, pk=kwargs.get('ticket_id')).exists() or Ticket.objects.filter(created_by=user).exists())
def ticket(request, **kwargs):
    current_ticket = get_object_or_404(Ticket, pk=kwargs.get('ticket_id'))
    users = User.objects.filter(groups__name=technician_group)
    if not (request.user.has_perm('app.view_all_tickets') or request.user.groups.filter(name=technician_group).exists() or request.user.is_staff or request.user.is_superuser or current_ticket.created_by == request.user):
        raise Http404("Страница не найдена")
    context = {'current_ticket': current_ticket, 'has_view_all_tickets_permission': request.user.groups.filter(name=technician_group).exists(), 'users': users}

    return render(request, 'desk/ticket.html', context)

@login_required  
def send_message(request, ticket_id):
    current_ticket = Ticket.objects.get(pk=ticket_id)
    if request.method == 'POST':
        if 'close-ticket' in request.POST:
            current_ticket.status = Ticket.Status.CLOSED
            
            # уведомление на эл.почту
            try:
                technician_email = current_ticket.technician.email
                subject = 'Заявка №{} закрыта'.format(current_ticket.id)
                message = 'Заявка №{} с темой "{}" закрыта.'.format(current_ticket.id, current_ticket.title)
                from_email = email_host_user
                send_mail(subject, message, from_email, [technician_email])
            except:             
                pass
            
            try:
                creator_email = current_ticket.created_by.email
                subject = 'Заявка №{} закрыта'.format(current_ticket.id)
                message = 'Заявка №{} с темой "{}" закрыта.'.format(current_ticket.id, current_ticket.title)
                from_email = email_host_user
                send_mail(subject, message, from_email, [creator_email])
            except:             
                pass
            
            try:
                superuseremail = get_default_technician().email
                subject = 'Заявка №{} закрыта'.format(current_ticket.id)
                message = 'Заявка №{} с темой "{}" закрыта.'.format(current_ticket.id, current_ticket.title)
                from_email = email_host_user
                send_mail(subject, message, from_email, [superuseremail])
            except:             
                pass
            

            # добавление уведомления в чат
            current_ticket.chat.append({ 
                'author': 'Уведомление системы',
                'message': f'Заявка закрыта пользователем {request.user.profile}',
                'datetime': datetime.datetime.now(pytz.timezone('Asia/Yekaterinburg')).strftime("%Y-%m-%d %H:%M:%S")
            })
            current_ticket.save()
            return redirect('index')
        elif 'open-ticket' in request.POST:
            current_ticket.status = Ticket.Status.OPENED

            # уведомление на эл.почту
            try:
                superuseremail = get_default_technician().email
                subject = 'Заявка №{} открыта повторно'.format(current_ticket.id)
                message = 'Заявка №{} с темой "{}" открыта повторно.'.format(current_ticket.id, current_ticket.title)
                from_email = email_host_user
                send_mail(subject, message, from_email, [superuseremail])
            except:             
                pass

            # добавление уведомления в чат
            current_ticket.chat.append({
                'author': 'Уведомление системы',
                'message': f'Заявка открыта пользователем {request.user.profile}',
                'datetime': datetime.datetime.now(pytz.timezone('Asia/Yekaterinburg')).strftime("%Y-%m-%d %H:%M:%S")
            })
            current_ticket.save()
            return redirect('index')
        elif 'progress' in request.POST:
            current_ticket.progress = request.POST.get('progress')
            
            # уведомление на эл.почту
            try:
                superuseremail = get_default_technician().email
                subject = 'Статус заявки №{} изменен'.format(current_ticket.id)
                message = 'Статус заявки №{} с темой "{}" изменен на "{}"'.format(current_ticket.id, current_ticket.title, current_ticket.progress)
                from_email = email_host_user
                send_mail(subject, message, from_email, [superuseremail])
            except:             
                pass
            
            try:
                creator_email = current_ticket.created_by.email
                subject = 'Статус заявки №{} изменен'.format(current_ticket.id)
                message = 'Статус заявки №{} с темой "{}" изменен на "{}"'.format(current_ticket.id, current_ticket.title, current_ticket.progress)
                from_email = email_host_user
                send_mail(subject, message, from_email, [creator_email])
            except:             
                pass
            
            # добавление уведомления в чат
            current_ticket.chat.append({
                'author': 'Уведомление системы',
                'message': f'Статус заявки изменен на "{current_ticket.progress}" пользователем {request.user.profile}',
                'datetime': datetime.datetime.now(pytz.timezone('Asia/Yekaterinburg')).strftime("%Y-%m-%d %H:%M:%S")
            })
            current_ticket.save()
            return redirect('ticket', ticket_id=ticket_id)
        elif 'assign-technician' in request.POST and request.user.is_superuser:
            technician_id = request.POST.get('technician')
            technician = User.objects.get(id=technician_id)
            current_ticket.technician = technician

            # уведомление на эл.почту
            try:
                technician_email = current_ticket.technician.email
                subject = 'Вам назначена заявка №{} по Административно-хозяйственной службе'.format(current_ticket.id)
                message = 'Вам назначена заявка №{} с темой "{}"'.format(current_ticket.id, current_ticket.title)
                from_email = email_host_user
                send_mail(subject, message, from_email, [technician_email])
            except:
                pass

            # добавление уведомления в чат
            current_ticket.chat.append({
                'author': 'Уведомление системы',
                'message': f'Исполнитель заявки изменен на {technician.profile} пользователем {request.user.profile}',
                'datetime': datetime.datetime.now(pytz.timezone('Asia/Yekaterinburg')).strftime("%Y-%m-%d %H:%M:%S")
            })
            current_ticket.save()
            return redirect('ticket', ticket_id=ticket_id)        
        else:
            message_text = request.POST.get('message_text')
            if message_text:
                current_ticket.chat.append({
                    'author': request.user.profile.verbose_name,
                    'message': message_text,
                    'datetime': datetime.datetime.now(pytz.timezone('Asia/Yekaterinburg')).strftime("%Y-%m-%d %H:%M:%S")
                })
                current_ticket.save()
            return redirect('ticket', ticket_id=ticket_id)
  
