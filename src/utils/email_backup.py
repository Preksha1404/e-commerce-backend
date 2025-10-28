def send_reset_email(email: str, token: str):
    reset_link = f"http://localhost:8000/reset-password?token={token}"
    print(f"Password reset link for {email}: {reset_link}")

