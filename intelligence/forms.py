from django import forms
from .models import PublisherProfile


class ReviewForm(forms.Form):
    decision = forms.ChoiceField(
        choices=[("approved", "Approve"), ("rejected", "Reject")]
    )
    rights = forms.ChoiceField(
        choices=[
            ("unknown", "Link only / unknown"),
            ("owned", "Owned"),
            ("licensed", "Licensed"),
            ("permission", "Permission granted"),
        ]
    )
    evidence = forms.CharField(widget=forms.Textarea, required=False)
    notes = forms.CharField(widget=forms.Textarea, required=False)


class AssignForm(forms.Form):
    publishers = forms.ModelMultipleChoiceField(
        queryset=PublisherProfile.objects.filter(active=True),
        widget=forms.CheckboxSelectMultiple,
    )


class PublicationForm(forms.Form):
    url = forms.URLField(max_length=1000)
    published_at = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"})
    )


class PerformanceForm(forms.Form):
    observed_at = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"})
    )
    views = forms.IntegerField(min_value=0, required=False)
    likes = forms.IntegerField(min_value=0, required=False)
    comments = forms.IntegerField(min_value=0, required=False)
    shares = forms.IntegerField(min_value=0, required=False)
    followers_gained = forms.IntegerField(min_value=0, required=False)
