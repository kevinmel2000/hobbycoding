from django.contrib.auth.decorators import login_required
from django.core.paginator import EmptyPage
from django.core.urlresolvers import reverse
from django.http import Http404
from django.utils import timezone
from django.views.generic import ListView

from meetup.mixins import FilterMixin
from .models import Meetup
from .forms import MeetupEditForm, CommentForm
from django.shortcuts import render, get_object_or_404, redirect
import django_filters


class MeetupFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr='contains')

    class Meta:
        model = Meetup
        fields = ['title']
        # together = ['title', 'tag']


class MeetupListView(ListView, FilterMixin):
    """
        Refer: https://github.com/carltongibson/django-filter/issues/245
    """
    model = Meetup
    template_name = 'meetup_list.html'
    paginate_by = 10
    context_object_name = 'meetup_list'

    filter_class = MeetupFilter

    def get_queryset(self, *args, **kwargs):
        qs = super(MeetupListView, self).get_queryset(*args, **kwargs)
        return self.get_filter_class()(self.request.GET, queryset=qs)

    def paginate_queryset(self, queryset, page_size):
        try:
            return super(MeetupListView, self).paginate_queryset(queryset, page_size)
        except EmptyPage:
            raise Http404


# TODO: comment 폼을 여기서 분리하고 싶은데..
def meetup_detail(request, pk):
    meetup = get_object_or_404(Meetup, pk=pk)
    if request.method == 'GET':
        form = CommentForm()
    elif request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.meetup = meetup
            comment.save()
            return redirect('meetup.views.meetup_detail', pk=pk)
    return render(request, 'meetup_detail.html', {'meetup': meetup, 'cmtForm': form})


@login_required
def meetup_new(request):
    if request.method == 'GET':
        form = MeetupEditForm()
    elif request.method == 'POST':
        form = MeetupEditForm(request.POST, request.FILES)
        if form.is_valid():
            new_meetup = form.save(commit=False)
            new_meetup.author = request.user
            new_meetup.published_date = timezone.now()
            new_meetup.save()
            return redirect('meetup.views.meetup_detail', pk=new_meetup.pk)

    return render(request, 'meetup_edit.html', {'form': form})


def meetup_edit(request, pk):
    meetup = get_object_or_404(Meetup, pk=pk)
    if request.method == 'GET':
        form = MeetupEditForm()
    elif request.method == 'POST':
        form = MeetupEditForm(request.POST, request.FILES)

        if form.is_valid():
            new_meetup = form.save(commit=False)
            new_meetup.author = request.user
            new_meetup.published_date = timezone.now()
            new_meetup.save()
            return redirect(reverse('meetup_detail', kwargs={'pk':new_meetup.pk}))

    return render(request, 'meetup_edit.html', {'form': form})


def meetup_join(request, pk):
    Meetup.objects.filter(pk=pk).update(views=F('views')+1)
    # return HttpResponseRedirect(request.GET.get('next')))
    return ''


def meetup_like(request, pk):
    meetup = get_object_or_404(Meetup, pk=pk) # TODO: 이렇게 밋업 가져오는걸 매번 메서드마다 해야하나
    if request.user in meetup.likes.all():
        meetup.likes.remove(request.user)
    else:
        meetup.likes.add(request.user)
    return redirect('meetup.views.meetup_detail', pk=pk)



