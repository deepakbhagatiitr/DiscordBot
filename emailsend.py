import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

def send_emailCustom(to_email, subject, body, resume_path):
    msg = MIMEMultipart()
    msg['To'] = to_email
    msg['Subject'] = subject
    msg['From'] = os.getenv('SMTP_EMAIL')

    msg.attach(MIMEText(body, 'plain'))

    # Attach resume
    with open(resume_path, 'rb') as attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f'attachment; filename={resume_path.split("/")[-1]}')
    msg.attach(part)

    # Send email
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(os.getenv('SMTP_EMAIL'), os.getenv('SMTP_PASSWORD'))
        server.send_message(msg)
