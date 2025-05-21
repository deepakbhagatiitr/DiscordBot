import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

def send_emailCustom(to_email, subject, body, resume_path, from_email=None):
    # Fallback to SMTP_EMAIL if from_email is not provided
    from_email = from_email or os.getenv('SMTP_EMAIL')

    if not from_email:
        raise ValueError("No sender email provided and SMTP_EMAIL not set in .env")

    msg = MIMEMultipart()
    msg['To'] = to_email
    msg['Subject'] = subject
    msg['From'] = from_email

    msg.attach(MIMEText(body, 'plain'))

    # Attach resume
    if not os.path.exists(resume_path):
        raise FileNotFoundError(f"Resume file not found: {resume_path}")
    
    with open(resume_path, 'rb') as attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f'attachment; filename={resume_path.split("/")[-1]}')
    msg.attach(part)

    # Send email
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            smtp_email = os.getenv('SMTP_EMAIL')
            smtp_password = os.getenv('SMTP_PASSWORD')
            if not smtp_email or not smtp_password:
                raise ValueError("SMTP_EMAIL or SMTP_PASSWORD not set in .env")
            server.login(smtp_email, smtp_password)
            server.send_message(msg)
            print(f"Email sent successfully to {to_email} from {from_email}")
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        raise