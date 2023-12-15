import re
import threading

from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from rest_framework.exceptions import ValidationError

email_regex = re.compile("[^@ \t\r\n]+@[^@ \t\r\n]+\.[^@ \t\r\n]+")
phone_regex = re.compile("^[\+]?[(]?[0-9]{2}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{2,5}[-\s\.]?[0-9]{2,5}$")
username_regex = re.compile(r"^[a-z0-9_-]{4,15}$")


def check_email_or_phone(data):
    if re.fullmatch(email_regex, data):
        data = 'email'
    elif re.fullmatch(phone_regex, data):
        data = 'phone'
    else:
        data = {
            'success': False,
            'message': 'Telefon yoki email xato'
        }
        raise ValidationError(data)
    return data


def check_auth_type(user_input):
    if re.fullmatch(email_regex, user_input):
        data = 'email'
    elif re.fullmatch(phone_regex, user_input):
        data = 'phone'
    elif re.fullmatch(username_regex, user_input):
        data = 'username'
    else:
        data = {
            'success': False,
            'message': 'Telefon yoki email xato'
        }
        raise ValidationError(data)
    return data


class EmailThread(threading.Thread):

    def __init__(self, email):
        self.email = email
        threading.Thread.__init__(self)

    def run(self) -> None:
        self.email.send()


class Email:
    @staticmethod
    def send_email(data):
        email = EmailMessage(
            subject=data['subject'],
            body=data['body'],
            to=[data['to_email']]
        )
        if data.get('content_type') == 'html':
            email.content_subtype = 'html'
        EmailThread(email).start()


def send_email(email, code):
    html_content = render_to_string(
        'email/authenticated/account_activate.html',
        {'code': code}
    )
    Email.send_email(
        {
            'subject': "Ro'yxatdan o'tish",
            'body': html_content,
            'to_email': email,
            'content_type': 'html'
        }
    )
