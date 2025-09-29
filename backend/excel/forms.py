from django import forms


class UploadExcelForm(forms.Form):
    nombre_proyecto = forms.CharField(
        label='Nombre del proyecto',
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    archivo = forms.FileField(
        label='Archivo Excel',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.xlsx,.xls'})
    )