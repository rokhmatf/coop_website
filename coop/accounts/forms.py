from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate
from .models import User

class CustomLoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control form-custom',
            'placeholder': 'Email',
            'required': True
        }),
        label="Email"
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-custom',
            'placeholder': 'Password',
            'required': True
        }),
        label="Password"
    )
    
    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)
    
    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')
        
        if email and password:
            try:
                user_obj = User.objects.get(email=email)
                user = authenticate(request=self.request, username=user_obj.username, password=password)
                if user is None:
                    raise forms.ValidationError("Invalid email or password")
                if not user.is_active:
                    raise forms.ValidationError("This account is inactive")
                cleaned_data['user'] = user
            except User.DoesNotExist:
                raise forms.ValidationError("Invalid email or password")
        
        return cleaned_data


class SupervisorRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password untuk supervisor'
        }),
        label="Password",
        help_text="Password minimal 8 karakter"
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Konfirmasi password'
        }),
        label="Konfirmasi Password"
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Username untuk supervisor'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email supervisor'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nama depan'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nama belakang'
            }),
        }
        labels = {
            'username': 'Username',
            'email': 'Email',
            'first_name': 'Nama Depan',
            'last_name': 'Nama Belakang',
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email sudah terdaftar.")
        return email
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Username sudah terdaftar.")
        return username
    
    def clean_password_confirm(self):
        password = self.cleaned_data.get('password')
        password_confirm = self.cleaned_data.get('password_confirm')
        
        if password and password_confirm:
            if password != password_confirm:
                raise forms.ValidationError("Password tidak cocok.")
        return password_confirm
    
    def clean_password(self):
        password = self.cleaned_data.get('password')
        if len(password) < 8:
            raise forms.ValidationError("Password minimal 8 karakter.")
        return password
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.role = 'supervisor'  # Set role sebagai supervisor
        user.is_active = True
        if commit:
            user.save()
        return user
