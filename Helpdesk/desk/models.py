from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils.functional import lazy

technician_group = 'Техник'

User = get_user_model()

@lazy
def get_default_technician():
    return User.objects.filter(groups__name=technician_group).all()[1].id


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    verbose_name = models.CharField(max_length=255, verbose_name='Имя пользователя')

    def __str__(self):
        return self.verbose_name

class Ticket(models.Model):

    class Kinds(models.TextChoices):
        LOW = "Низкая", "Низкая"
        MEDIUM = 'Средняя', 'Средняя'
        HIGH = 'Высокая', 'Высокая'
        CRITICAL = "Критичная", "Критичная"

    class Progres(models.TextChoices):
        IMPOSSIBLE = 'Невозможно выполнить', 'Невозможно выполнить'
        ACCEPTED = 'Принято к рассмотрению', 'Принято к рассмотрению'
        INPROGRESS = 'В стадии решения', 'В стадии решения'
        DECIDED = 'Успешно решено', 'Успешно решено'

    class Status(models.TextChoices):
        OPENED = 'открыта', 'Открыта'
        CLOSED = 'закрыта', 'Закрыта'

    title = models.CharField(max_length=100, verbose_name='Тема')
    content = models.TextField(verbose_name='Текст')
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name='Автор', blank=True, null=True, related_name='created_tickets')
    criticalness = models.CharField(max_length=25, choices=Kinds.choices, default=Kinds.MEDIUM, verbose_name='Критичность')
    technician = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name='Исполнитель', blank=True, null=True, limit_choices_to={'groups__name': technician_group}, default=get_default_technician, related_name='assigned_tickets')
    progress = models.CharField(max_length=25, choices=Progres.choices, default=Progres.ACCEPTED, verbose_name='Статус заявки')
    status = models.CharField(max_length=10, choices=Status.choices,default=Status.OPENED, verbose_name='Открытость заявки')
    published = models.DateTimeField(auto_now=True, db_index=True, verbose_name='Дата и время создания')
    chat = models.JSONField(default=list, blank=True, verbose_name='Чат')
    documents = models.ManyToManyField('Document', blank=True, related_name='related_tickets', verbose_name='Документ')
    
    def get_absolute_url(self):
        return "%s/" % self.pk

    class Meta:
        verbose_name_plural = 'Заявки'
        verbose_name = "Заявка"
        ordering = ["-published"]
        permissions = [('view_all_tickets', 'Can view all tickets'),]
    
class Document(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='related_documents', verbose_name='Заявка')
    file = models.FileField(upload_to='files/', blank=True, null=True, verbose_name='Документ')

    def __str__(self):
        return self.file.name if self.file else ''
    
    class Meta:
        verbose_name_plural = 'Документы'
        verbose_name = "Документ"

@receiver(pre_save, sender=Ticket)
def set_created_by(sender, instance, **kwargs):
    if not instance.created_by:
        instance.created_by = get_user_model().get_current_user()
