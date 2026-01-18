from django.shortcuts import render
from django.contrib.auth.views import PasswordResetView
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.http import HttpResponseRedirect
import logging

#logger = logging.getLogger(__name__)
#logger.error(f" 🔥🔥🔥 EMAIL_BACKEND REAL = {settings.EMAIL_BACKEND}")

class CustomPasswordResetView(PasswordResetView):    
    template_name = 'registration/password_reset_form.html'
    email_template_name = 'registration/password_reset_email.txt'
    html_email_template_name = 'registration/password_reset_email.html'
    subject_template_name = 'registration/password_reset_subject.txt'



