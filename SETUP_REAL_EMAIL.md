# ⚙️ SETUP REAL EMAIL OTP - QUICK GUIDE

## Option 1: Using Gmail (Recommended)

### Step 1: Enable 2-Factor Authentication
1. Go to: https://myaccount.google.com/security
2. Scroll down to "2-Step Verification"
3. Click "Enable 2-Step Verification"
4. Follow the prompts to set it up

### Step 2: Generate App Password
1. After 2FA is enabled, go to: https://myaccount.google.com/apppasswords
2. Select **Mail** and **Windows Computer**
3. Click **Generate**
4. Google will show a 16-character password (e.g., `abcd efgh ijkl mnop`)

### Step 3: Update app.py
Edit app.py lines 13-18 with your credentials:

```python
EMAIL_SENDER = "your.email@gmail.com"              # Your Gmail address
EMAIL_PASSWORD = "abcd efgh ijkl mnop"             # The 16-char app password (remove spaces)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
DEBUG_MODE = False  # Real email mode
```

**Example:**
```python
EMAIL_SENDER = "john.doe@gmail.com"
EMAIL_PASSWORD = "abcdefghijklmnop"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
DEBUG_MODE = False
```

---

## Option 2: Using Outlook/Office365

```python
EMAIL_SENDER = "your.email@outlook.com"
EMAIL_PASSWORD = "your_password"
SMTP_SERVER = "smtp-mail.outlook.com"
SMTP_PORT = 587
DEBUG_MODE = False
```

---

## Option 3: Using Yahoo Mail

```python
EMAIL_SENDER = "your.email@yahoo.com"
EMAIL_PASSWORD = "your_app_password"  # Generate from Yahoo
SMTP_SERVER = "smtp.mail.yahoo.com"
SMTP_PORT = 587
DEBUG_MODE = False
```

---

## Testing the Setup

1. **Start the Flask app:**
   ```bash
   python app.py
   ```

2. **Go to client login:**
   - Open: http://127.0.0.1:5000/client-login

3. **Enter your email:**
   - Provide your real email address (same one as configured)

4. **Check email:**
   - Look in your inbox for the OTP email
   - Copy the 6-digit code

5. **Enter OTP:**
   - Paste the code on the verification page
   - Click "Verify OTP"

6. **Access dashboard:**
   - You should now be logged in to the client dashboard!

---

## Troubleshooting

### "Failed to send OTP" error

**For Gmail users:**
- ✓ Did you enable 2-Factor Authentication?
- ✓ Did you generate an App Password?
- ✓ Is it a 16-character password? (Remove any spaces)
- ✓ Is EMAIL_PASSWORD correct in app.py?

**For all users:**
- ✓ Check your internet connection
- ✓ Verify email address is correct
- ✓ Verify SMTP server and port are correct
- ✓ Try resending (sometimes network is slow)

### OTP not received

- Check **Spam/Junk** folder
- Wait 30 seconds (email can be delayed)
- Try clicking **Resend OTP** button
- Check that email address is spelled correctly

### "Email Not Configured" warning

- This means EMAIL_SENDER is still set to `"your_email@gmail.com"`
- Update it with your actual Gmail address

---

## DEBUG MODE (For Testing Only)

If you want to test without real email, set:
```python
DEBUG_MODE = True
```

Then OTP will display on the screen instead of being sent.

---

**💡 After configuring email, restart Flask and test!**
