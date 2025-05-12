from django import forms
from .models import FundRequest, UserFundRequest
from django.contrib.auth.models import User


class FundRequestForm(forms.ModelForm):
    class Meta:
        model = FundRequest
        fields = ['amount_requested', 'reason']
    def __init__(self, *args, **kwargs):
        super(FundRequestForm, self).__init__(*args, **kwargs)
        self.fields['amount_requested'].widget.attrs.update({'class': 'form-control'})
        self.fields['reason'].widget.attrs.update({'class': 'form-control', 'rows': 3})

    def clean_amount_requested(self):
        amount = self.cleaned_data.get('amount_requested')
        if amount <= 0:
            raise forms.ValidationError("amount should be above 0.")
        return amount

class FundApprovalForm(forms.ModelForm):
    class Meta:
        model = FundRequest
        fields = ['status', 'rejection_reason']

    def __init__(self, *args, **kwargs):
        super(FundApprovalForm, self).__init__(*args, **kwargs)
        self.fields['status'].widget.attrs.update({'class': 'form-select'})
        self.fields['rejection_reason'].widget.attrs.update({'class': 'form-control', 'rows': 3})

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get("status")
        rejection_reason = cleaned_data.get("rejection_reason")

        if status == "REJECTED" and not rejection_reason:
            raise forms.ValidationError("Please provide a rejection reason.")


class UserSignupForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']


class UserLoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)


class UserFundRequestForm(forms.ModelForm):
    class Meta:
        model = UserFundRequest
        fields = ['organization', 'amount', 'reason']
        widgets = {
            'reason': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'amount': 'Amount (INR)',
        }
