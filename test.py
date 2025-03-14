import smtplib

server = smtplib.SMTP(
    "smtp.gmail.com", 587
)  # Use the correct server and port
server.starttls()
server.login("noreply@getrealfund.com", "okeckxzrxjtkpbkg")
print("Login successful!")
server.quit()