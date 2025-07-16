from typing import Optional
from bs4 import BeautifulSoup
import re
from imap_tools import AND 
from datetime import datetime, timedelta
from email.mime.application import MIMEApplication
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# Job-related keywords for filtering
JOB_KEYWORDS = [
    'job', 'position', 'opportunity', 'hiring', 'career', 'opening',
    'recruitment', 'apply', 'interview', 'hackathon', 'internship',
    'developer', 'engineer', 'coding challenge', 'programming contest'
]

# Keywords to exclude (LinkedIn spam, etc.)
EXCLUDE_KEYWORDS = [
    'liked your', 'viewed your profile', 'connection request',
    'endorsed you', 'work anniversary', 'network update',
    'people you may know', 'trending in your network', 'shared a post', 
    'conversation', 'invitations', 'newsletter', 'course', 'stories'
]

EXCLUDE_DOMAINS = [
    'noreply@', 'no-reply@', 'donotreply@', 'notifications@',
    'newsletter@', 'marketing@', 'promo@', 'offers@'
]

# Trusted job domains
TRUSTED_DOMAINS = [
    'naukri.com', 'indeed.com', 'glassdoor.com', 'linkedin.com/jobs',
    'unstop.com', 'internshala.com', 'devfolio.co', 'github.com'
]


def extract_text_from_html(html_content):
    """Extract clean text from HTML Content"""
    try:
        if not html_content or '<' not in html_content:
            return html_content.strip() if html_content else ""
        html_content = re.sub(r'<(script|style|head|meta|link|title)[^>]*>.*?</\1>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        html_content = re.sub(r'<!DOCTYPE[^>]*>', '', html_content, flags=re.IGNORECASE)
        
        # Remove XML declarations
        html_content = re.sub(r'<\?xml[^>]*\?>', '', html_content, flags=re.IGNORECASE)
        
        # Remove HTML comments
        html_content = re.sub(r'<!--.*?-->', '', html_content, flags=re.DOTALL)
        
        soup = BeautifulSoup(html_content, "html.parser")

        for element in soup(['script', 'style', 'head', 'meta', 'link', 'title', 'nonscript']):
            element.decompose()

        text = soup.get_text()

        lines = (line.strip() for line in text.splitlines())
        text = '\n'.join(line for line in lines if line)

        text = re.sub(r'\n\s*\n', '\n\n', text)  # Multiple newlines to double newlines
        text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces to single space
        text = re.sub(r'\n ', '\n', text)  # Remove space after newlines
        text = re.sub(r' \n', '\n', text)  # Remove space before newlines   
        
        return text.strip()
        
    except Exception as e:
        print(f"Error extracting text from email {e}")
        try:
            # Remove style and script content first
            html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            
            # Remove all HTML tags
            text = re.sub(r'<[^>]+>', '', html_content)
            
            # Clean whitespace
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'\n\s*\n', '\n\n', text)
            
            return text.strip()
        except:
            return html_content[:500] + "..." if len(html_content) > 500 else html_content


def get_email_content(msg):
    """Extract email content from email"""
    content = ""
    if msg.text and msg.text.strip():
        content = msg.text.strip()
    if msg.html and msg.html.strip():
        content = extract_text_from_html(msg.html)
        if content and len(content.strip()) > 10:
            # Additional check: if content still looks like HTML, it failed
            if not (content.startswith('<!DOCTYPE') or '<html' in content[:100]):
                return content
    if not content:
        content = str(msg).split('\n\n', 1)[-1] if '\n\n' in str(msg) else "No content available"
    
    return content


def is_job_related(subject, sender, content):
    """Check if email is job-related"""
    all_text = f"{subject}{sender}{content}".lower()

    for exclude_word in EXCLUDE_KEYWORDS:
        if exclude_word in all_text:
            return False
    
    for domain in TRUSTED_DOMAINS :
        if domain in sender.lower() and domain not in EXCLUDE_DOMAINS:
            return True
        
    job_keyword_count = sum(1 for keyword in JOB_KEYWORDS if keyword in all_text)
    return job_keyword_count >= 2

def filter_job_emails(mailbox, days_back = 10):
    """Filter and Extract job related emails"""
    try:
        since_date = datetime.now() - timedelta(days=days_back)
        since_date_only = since_date.date()
        messages = mailbox.fetch(AND(date_gte=since_date_only), reverse=True)

        job_emails = []
        processed_count = 0

        for msg in messages:
            processed_count += 1
            try:
                subject = msg.subject or ""
                sender = msg.from_ or ""
                date = msg.date.strftime("%Y-%m-%d %H:%M:%S") if msg.date else ""

                content = get_email_content(msg)

                if is_job_related(subject, sender, content):
                    job_emails.append({
                        'subject': subject,
                        'sender': sender,
                        'date': date,
                        'content': content[:2000]
                    })

                    print(f"Job email found {subject[:50]}")

                if processed_count % 50 == 0:
                    print(f"Processed {processed_count} emails...")
            except Exception as e:
                print("Error processing email: {e}")
                continue

        print(f"\n Found {len(job_emails)} job-related emails out of {processed_count} total emails")
        return job_emails
    
    except Exception as e:
        print(f"Error filtering email: {e}")
        return []   
    

def save_emails(job_emails, filename = "job_emails.txt"):
    """Save job emails to a text file with proper formatting"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            #Header
            f.write("JOB EMAILS EXTRACTED\n")
            f.write("=" * 60 + "\n")
            f.write(f"Total emails found: {len(job_emails)}\n")
            f.write(f"Extraction date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")

            #emails
            for i, email in enumerate(job_emails, 1):
                f.write(f"EMAIL {i}\n")
                f.write("-" * 40 + "\n")
                f.write(f"Subject: {email['subject']}\n")
                f.write(f"From: {email['sender']}\n")
                f.write(f"Date: {email['date']}\n")
                f.write(f"\nContent:\n{email['content']}\n")
                
                if len(email['content']) >= 2000:
                    f.write("\n[Content truncated to 2000 characters]\n")
                
                f.write("\n" + "=" * 60 + "\n\n")
        
        print(f"Job emails saved to {filename}")
        return True
    except Exception as e:
        print("Error saving to file: {e}")
        return False
    

def extract_job_emails(mailbox, days_back = 10, output_file = "job_emails.txt"):
    """Main function to extract job emails"""
    # mailbox = connect_to_gmail(username, password)
    if not mailbox:
        return []
    
    try:
        job_emails = filter_job_emails(mailbox, days_back)

        #Display results
        print(f"\n SUMMARY:")
        print(f"Total job emails found: {len(job_emails)}")
        print(f"Search period: Last {days_back} days")

        for i, email in enumerate(job_emails[:3], 1):
            print(f"\n ----EMAIL {i}----")
            print(f"Subject: {email['subject']}")
            print(f"From: {email['sender']}")
            print(f"Content Preview: {email['content'][:200]}...")
        
        if len(job_emails)>3:
            print(f"\n... and {len(job_emails)-3} emails more")
        
        if job_emails:
            save_emails(job_emails, output_file)
        return job_emails
    except Exception as e:
        return f"Error: {e}"
    

def attach_pdf(msg, pdf_path):
    try:
        with open(pdf_path, 'rb') as attachment:
            part = MIMEApplication(attachment.read(), _subtype='pdf')
            part.add_header('Content-Disposition', f'attachment; filename= {os.path.basename(pdf_path)}')
            msg.attach(part)
    except Exception as e:
        print(f"Error attaching PDF: {e}")


def send_mails(username: str, password: str, name: str, to: str, subject: str, pdf_path: Optional[str], document_content):
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()  # Enable TLS encryption
        server.ehlo() 
        server.login(username, password)

        msg = MIMEMultipart()
        msg['From'] = name
        msg['To'] = to
        msg['Subject'] = subject

        message = document_content
        msg.attach(MIMEText(message, 'plain'))
        
        if pdf_path and os.path.exists(pdf_path):
            attach_pdf(msg, pdf_path)
            print(f"PDF attachment added: {pdf_path}")
            text = msg.as_string()

            server.sendmail(username, to, text)
            
        elif pdf_path:
            print(f"Warning: PDF file not found at {pdf_path}")
            print("Mail not sent")
        server.quit()
        
    except Exception as e:
        raise RuntimeError(f"Failed to send email: {e}")
