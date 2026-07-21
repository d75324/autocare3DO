import re
from django.core.exceptions import ValidationError
from django.core.validators import validate_email as django_validate_email

def validate_name_field(value, field_name="Nombre"):
    """Función reutilizable para validar nombres y apellidos"""
    if not value:
        raise ValidationError(f'El {field_name} es obligatorio.')
    
    value = value.strip()
    
    # Validación de caracteres. Con ^ y $, match recorre toda la cadena, de principio a fin.
    if not re.match(r'^[A-Za-záéíóúÁÉÍÓÚñÑüÜ\s\-]+$', value):
        raise ValidationError(f'El {field_name} solo debe contener letras, espacios, ñ, tildes y guiones.')
    
    # Lista negra de patrones sospechosos
    suspicious_patterns = [
        r'https?://', r'www\.', r'\.com', r'\.org',
        r'<[^>]+>', r'[{}()\[\]]', r'[#@$%^&*+=]',
        r'código', r'codigo', r'descuento', r'promoción',
        r'bugs', r'seguridad'
    ]
    
    for pattern in suspicious_patterns:
        if re.search(pattern, value, re.IGNORECASE):
            raise ValidationError(f'El {field_name} contiene caracteres o palabras no permitidas.')
    
    if len(value) < 2 or len(value) > 25:
        raise ValidationError(f'El {field_name} debe tener entre 2 y 25 caracteres.')
    
    return value.title()

def validate_email_username(value):
    """Función para validar correos electrónicos cuando se usan como username"""
    if not value:
        raise ValidationError('El correo electrónico es obligatorio.')
    
    value = value.strip().lower() # correos siempre en minúsculas
    
    # 1. Validación de formato de email de Django
    try:
        django_validate_email(value)
    except ValidationError:
        raise ValidationError('El formato del correo electrónico no es válido.')
    
    # 2. lista negra de código sospechoso adaptada para correos (afuera .com, .org y caracteres válidos de emails)
    suspicious_patterns = [
        r'https?://', r'www\.', 
        r'<[^>]+>', r'[{}()\[\]]', r'[#$%^&*+=]',  # @ es obligatorio
        r'descuento', r'promoción', r'bugs', r'seguridad' # puede existir un mail @codigo...
    ]
    
    for pattern in suspicious_patterns:
        if re.search(pattern, value, re.IGNORECASE):
            raise ValidationError('El correo contiene palabras o patrones no permitidos.')
            
    return value