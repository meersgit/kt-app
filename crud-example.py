from dotenv import load_dotenv
load_dotenv()
import os
from supabase import create_client
from collections import defaultdict

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

supabase = create_client(url, key)
print("✅ Supabase client connected successfully!\n")

# Store emails of users who have logged in (initialize outside try block)
logged_in_emails = set()

# Fetch user logins
print("=" * 60)
print("📊 USER LOGINS")
print("=" * 60)
try:
    logins = supabase.table("user_logins").select("*").order("login_time", desc=True).execute()
    
    if logins.data:
        # Group by email to show unique users (each email should only have one record now)
        unique_users = {}
        for login in logins.data:
            email = login.get('email')
            if email:
                logged_in_emails.add(email)  # Add to set for quick lookup
                # Since we update login_time for existing users, each email should have only one record
                unique_users[email] = login.get('login_time')
        
        print(f"\nTotal unique users who logged in: {len(unique_users)}\n")
        for i, (email, login_time) in enumerate(unique_users.items(), 1):
            print(f"{i}. Email: {email}")
            print(f"   Latest login: {login_time}\n")
    else:
        print("No user logins found.\n")
except Exception as e:
    print(f"❌ Error fetching user logins: {e}\n")

# Fetch file uploads
print("=" * 60)
print("📁 FILE UPLOADS")
print("=" * 60)
try:
    uploads = supabase.table("file_uploads").select("*").order("upload_time", desc=True).execute()
    
    if uploads.data:
        # Group files by user email
        files_by_user = defaultdict(list)
        for upload in uploads.data:
            email = upload.get('email')
            filename = upload.get('filename')
            upload_time = upload.get('upload_time')
            if email and filename:
                files_by_user[email].append({
                    'filename': filename,
                    'upload_time': upload_time
                })
        
        print(f"\nTotal files uploaded: {len(uploads.data)}\n")
        for email, files in files_by_user.items():
            # Check if this email has a corresponding user login
            has_login = email in logged_in_emails
            login_status = "Has login" if has_login else " No login found"
            
            print(f"👤 User: {email} [{login_status}]")
            print(f"   Files uploaded: {len(files)}")
            for file_info in files:
                print(f"   - {file_info['filename']} (uploaded at: {file_info['upload_time']})")
            print()
        
        # Summary
        emails_with_login = [email for email in files_by_user.keys() if email in logged_in_emails]
        emails_without_login = [email for email in files_by_user.keys() if email not in logged_in_emails]
        
        print(f"\n📈 Summary:")
        print(f"   Users with login: {len(emails_with_login)}")
        if emails_with_login:
            for email in emails_with_login:
                print(f"      - {email}")
        print(f"   Users without login: {len(emails_without_login)}")
        if emails_without_login:
            print(f"      ⚠️  These users uploaded files but never logged in:")
            for email in emails_without_login:
                print(f"      - {email}")
    else:
        print("No file uploads found.\n")
except Exception as e:
    print(f" Error fetching file uploads: {e}\n")

print("=" * 60)