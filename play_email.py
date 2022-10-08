import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from secret import *

SENDER = EMAIL_ADDRESS
SMTP_SERVER = 'smtp.gmail.com'
USER_ACCOUNT = {'username':EMAIL_ADDRESS, 'password':PASSWORD}
SUBJECT = "Test Test"


def send_mail(receivers, text, sender=SENDER, user_account=USER_ACCOUNT, subject=SUBJECT):
    msg_root = MIMEMultipart()
    msg_root['Subject'] = subject
    msg_root['To'] = '; '.join(receivers)
    text = convert_to_html(text)
    msg_text = MIMEText(text, 'html', 'utf-8')
    msg_root.attach(msg_text)
    smtp = smtplib.SMTP('smtp.gmail.com:587')
    smtp.ehlo()
    smtp.starttls()
    smtp.login(user_account['username'], user_account['password'])
    smtp.sendmail(sender, receivers, msg_root.as_string())

def convert_to_html(text):
    html_text = text.replace('\n', '<br>')
    html = f"""\
            <html>
              <head></head>
              <body>
                <p>
                {html_text}
                </p>
              </body>
            </html>
            """
    return html