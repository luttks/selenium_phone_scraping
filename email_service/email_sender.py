"""
Email service for sending search result links
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = os.getenv('SMTP_USER', '')
        self.smtp_pass = os.getenv('SMTP_PASS', '')
        self.from_email = os.getenv('FROM_EMAIL', self.smtp_user)
        self.frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:8000')

    def send_search_result_email(self, to_email: str, result_id: str, total_phones: int, source: str) -> bool:
        """
        Send email with link to search results
        """
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = f'Kết quả tìm kiếm điện thoại - {total_phones} sản phẩm từ {source}'

            # Email body
            result_url = f"{self.frontend_url}/{result_id}"
            body = f"""
            <html>
            <body>
                <h2>Kết quả tìm kiếm điện thoại của bạn</h2>
                <p>Chúng tôi đã tìm thấy <strong>{total_phones}</strong> sản phẩm từ <strong>{source}</strong>.</p>
                <p>Click vào link dưới đây để xem chi tiết kết quả:</p>
                <p><a href="{result_url}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Xem kết quả</a></p>
                <p>Link này sẽ hết hạn sau 24 giờ.</p>
                <br>
                <p>Trân trọng,<br>Phone Scraper Team</p>
            </body>
            </html>
            """

            msg.attach(MIMEText(body, 'html'))

            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_user, self.smtp_pass)
            text = msg.as_string()
            server.sendmail(self.from_email, to_email, text)
            server.quit()

            logger.info(f"Email sent successfully to {to_email} for result {result_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

# Global instance
email_service = EmailService()
