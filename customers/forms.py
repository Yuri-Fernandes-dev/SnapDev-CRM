from django import forms
from .models import Customer

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            'name',
            'email',
            'phone',
            'address',
            'city',
            'state',
            'zipcode',
            'birthday',
            'notes'
        ]
        widgets = {
            'birthday': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not phone:  # Se o telefone estiver vazio, não precisa validar
            return phone
        
        # . Verificar se existe outro cliente com este telefone na mesma empresa
        # Excluir o cliente atual no caso de edição
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            exists = Customer.objects.filter(
                company=self.company, 
                phone=phone
            ).exclude(pk=instance.pk).exists()
        else:
            exists = Customer.objects.filter(
                company=self.company, 
                phone=phone
            ).exists()
        
        if exists:
            raise forms.ValidationError(
                "Já existe um cliente com este telefone. Por favor, use um número diferente ou deixe o campo em branco."
            )
        
        return phone
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:  # Se o email estiver vazio, não precisa validar
            return email
        
        # Verificar se existe outro cliente com este email na mesma empresa
        # Excluir o cliente atual no caso de edição
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            exists = Customer.objects.filter(
                company=self.company, 
                email=email
            ).exclude(pk=instance.pk).exists()
        else:
            exists = Customer.objects.filter(
                company=self.company, 
                email=email
            ).exists()
        
        if exists:
            raise forms.ValidationError(
                "Já existe um cliente com este e-mail. Por favor, use um e-mail diferente ou deixe o campo em branco."
            )
        
        return email 