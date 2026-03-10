"""
Email service for sending verification and notification emails via Brevo SMTP.

Handles:
- Email verification links
- Async email sending
- HTML email templates
"""

import asyncio
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from config import settings


async def send_verification_email(
    email: str,
    verification_token: str,
    full_name: Optional[str] = None
) -> bool:
    """
    Send email verification link to user.

    Args:
        email: Recipient email address
        verification_token: JWT verification token
        full_name: User's full name for personalization

    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        # Build verification URL
        verification_url = (
            f"{settings.API_BASE_URL}/auth/verify-email?token={verification_token}"
        )

        # Prepare email content
        subject = "Verify Your Email - PDF Conversion Platform"
        recipient_name = full_name.split()[0] if full_name else "User"

        html_content = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #1f2937; color: white; padding: 20px; border-radius: 5px 5px 0 0; }}
                    .content {{ background-color: #f9fafb; padding: 20px; border: 1px solid #e5e7eb; border-radius: 0 0 5px 5px; }}
                    .button {{ display: inline-block; background-color: #3b82f6; color: white; padding: 12px 20px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                    .footer {{ color: #6b7280; font-size: 12px; margin-top: 20px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Email Verification</h1>
                    </div>
                    <div class="content">
                        <p>Hello {recipient_name},</p>
                        <p>Thank you for signing up for PDF Conversion Platform! To complete your registration, please verify your email address by clicking the button below:</p>
                        <a href="{verification_url}" class="button">Verify Email</a>
                        <p>This link will expire in 24 hours.</p>
                        <p>If you didn't create this account, you can safely ignore this email.</p>
                        <p>Best regards,<br>PDF Conversion Platform Team</p>
                        <div class="footer">
                            <p>This is an automated email. Please do not reply to this message.</p>
                        </div>
                    </div>
                </div>
            </body>
        </html>
        """

        # Send email asynchronously
        await asyncio.to_thread(
            _send_smtp_email,
            email,
            subject,
            html_content
        )
        return True

    except Exception as e:
        print(f"Error sending verification email to {email}: {str(e)}")
        return False


async def send_password_reset_email(
    email: str,
    reset_token: str,
    full_name: Optional[str] = None
) -> bool:
    """
    Send password reset link to user.

    Args:
        email: Recipient email address
        reset_token: JWT reset token
        full_name: User's full name for personalization

    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        # Build reset URL
        reset_url = (
            f"{settings.API_BASE_URL}/auth/reset-password?token={reset_token}"
        )

        subject = "Reset Your Password - PDF Conversion Platform"
        recipient_name = full_name.split()[0] if full_name else "User"

        html_content = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #1f2937; color: white; padding: 20px; border-radius: 5px 5px 0 0; }}
                    .content {{ background-color: #f9fafb; padding: 20px; border: 1px solid #e5e7eb; border-radius: 0 0 5px 5px; }}
                    .button {{ display: inline-block; background-color: #ef4444; color: white; padding: 12px 20px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                    .footer {{ color: #6b7280; font-size: 12px; margin-top: 20px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Password Reset Request</h1>
                    </div>
                    <div class="content">
                        <p>Hello {recipient_name},</p>
                        <p>We received a request to reset your password. Click the button below to create a new password:</p>
                        <a href="{reset_url}" class="button">Reset Password</a>
                        <p>This link will expire in 1 hour.</p>
                        <p>If you didn't request this, you can safely ignore this email.</p>
                        <p>Best regards,<br>PDF Conversion Platform Team</p>
                        <div class="footer">
                            <p>This is an automated email. Please do not reply to this message.</p>
                        </div>
                    </div>
                </div>
            </body>
        </html>
        """

        # Send email asynchronously
        await asyncio.to_thread(
            _send_smtp_email,
            email,
            subject,
            html_content
        )
        return True

    except Exception as e:
        print(f"Error sending password reset email to {email}: {str(e)}")
        return False


def _send_smtp_email(recipient_email: str, subject: str, html_content: str) -> None:
    """
    Internal helper to send email via Brevo SMTP.

    Args:
        recipient_email: Recipient email address
        subject: Email subject
        html_content: HTML email body
    """
    try:
        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{settings.BREVO_FROM_NAME} <{settings.BREVO_FROM_EMAIL}>"
        msg["To"] = recipient_email

        # Attach HTML content
        msg.attach(MIMEText(html_content, "html"))

        # Connect to Brevo SMTP and send
        with smtplib.SMTP(settings.BREVO_SMTP_HOST, settings.BREVO_SMTP_PORT) as server:
            server.starttls()
            server.login(settings.BREVO_SMTP_USER, settings.BREVO_SMTP_PASSWORD)
            server.send_message(msg)

        print(f"Email sent successfully to {recipient_email}")

    except smtplib.SMTPException as e:
        print(f"SMTP error sending email to {recipient_email}: {str(e)}")
        raise
    except Exception as e:
        print(f"Error sending email to {recipient_email}: {str(e)}")
        raise
