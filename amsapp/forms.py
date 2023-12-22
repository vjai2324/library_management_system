from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import *



class LoginForm(forms.Form):
    username = forms.CharField(max_length=65)
    password = forms.CharField(max_length=65, widget=forms.PasswordInput)


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['first_name','last_name','username', 'email', 'password1', 'password2']

class ProfileRegisterForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["mobile_number",
            "gender",
            "Address",'pincode', 'district', 'state','postName']
        


class UserUpdateForm(UserChangeForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['mobile_number', 'gender', 'Address']


class BookSearchForm(forms.Form):
    query = forms.CharField(label="Search Query", required=False)
    category = forms.ChoiceField(
        label="Category",
        required=False,
        choices=[("programming", "Programming"), ("fiction", "Fiction")],
    )
    author = forms.CharField(label="Author", required=False)
    publication_year = forms.IntegerField(label="Publication Year", required=False)


class Dealers2Form(forms.ModelForm):
    class Meta:
        model = dealers2
        fields = "__all__"


class Book2Form(forms.ModelForm):
    class Meta:
        model = book2
        fields = "__all__"
        widgets = {
            "pub_date": forms.DateInput(attrs={"type": "date"}),
        }


class Purchase2Form(forms.ModelForm):
    class Meta:
        model = purchase2
        fields = "__all__"
        widgets = {
            "orderdate": forms.DateInput(attrs={"type": "date"}),
            "get_book_pub_date": forms.DateInput(attrs={"type": "date"}),
        }


class RPurchaseForm(forms.ModelForm):
    class Meta:
        model = R_Purchase
        fields = "__all__"


class BookTransactionForm(forms.ModelForm):
    class Meta:
        model = Book_transaction
        fields = '__all__'  # Include all fields from the Book_transaction model
        widgets = {
            'checkout': forms.DateInput(attrs={'type': 'date'}),
            'checkin_date': forms.DateInput(attrs={'type': 'date'}),
        }


class WishlistItemForm(forms.Form):
    book_id = forms.CharField(max_length=255)
    book_isbn = forms.CharField(max_length=255, widget=forms.HiddenInput())
