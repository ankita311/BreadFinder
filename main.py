from bs4 import BeautifulSoup
import requests
import pdfplumber
from openai import OpenAI
import re
from imap_tools import MailBox, AND 
from datetime import datetime, timedelta


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
    'people you may know', 'trending in your network'
]

# Trusted job domains
TRUSTED_DOMAINS = [
    'naukri.com', 'indeed.com', 'glassdoor.com', 'linkedin.com/jobs',
    'unstop.com', 'internshala.com', 'devfolio.co', 'github.com'
]



def extract_job_description(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    job_text = soup.get_text()

    return job_text.strip()


# url = "https://unstop.com/jobs/mendix-developer-birlasoft-1509147"        #Forbidden
# url = "https://southasiacareers.deloitte.com/job/Hyderabad-Associate-F&A-Operate-Procure-to-Pay-Hyderabad-Finance-Transformation/41184344/"  #worked

# print(job)

def extract_resume_text(pdf_path):
    doc = pdfplumber.open(pdf_path)
    text = ""
    for page in doc.pages:
        text += page.extract_text()
    return text

# path = "file:///C:/Users/Ankita/OneDrive/Desktop/Notes/Ankita%20CV.pdf"
path = r"C:\Users\Ankita\OneDrive\Desktop\Notes\AnkitaCV.pdf"

# print(resume)
client = OpenAI()
def score_resume(job_desc, resume_text):
    prompt = f"""
    Given the following job description and resume, rate how well the resume matches the job (0-100), explain why, and suggest improvements.

    Job Description:
    {job_desc}

    Resume:
    {resume_text}

    Respond in this format:
    Match Score: <score>/100
    Summary: <why it's a good/bad match>
    Suggestions: <what to improve>
    """
    
    response = client.chat.completions.create(
        model = 'gpt-4o-mini',
        messages= [{'role': 'user', 'content': prompt}],
        temperature= 0.4
    )
    return response.choices[0].message.content


# url = "https://southasiacareers.deloitte.com/job/Bengaluru-T&T-Engineering-EAD-QE-Automation-Python-Bangalore-Consultant/41851644/"
# job = extract_job_description(url)
# resume = extract_resume_text(path)
# result = score_resume(job, resume)
# print(result)

# def connect_email(username, app_pass):
#     imap = imaplib.IMAP4_SSL("imap.gmail.com")
#     imap.login(username, app_pass)
#     for i in imap.list()[1]:
#         l = i.decode().split('"/"')
#         print(l[0] + " = " + l[1])

    

# res = connect_email(USERNAME, PASSWORD)
# print(res)

def connect_to_gmail(username, password):
    """Function to connect to the gmail account"""
    try:
        mb = MailBox('imap.gmail.com').login(username, password)
        print("Connected to Gmail Successfully")
        return mb
    except Exception as e:
        print(f"Connection failed {e}")
        return None
    
def disconnect_from_gmail(mailbox):
    """Function to disconnect client from gmail"""
    if mailbox:
        mailbox.logout()
        print("Disconnected from Gmail")

def extract_text_from_html(html_content):
    """Extract clean text from HTML Content"""
    try:
        html_content = re.sub(r'<(script|style|head|meta|link|title)[^>]*>.*?</\1>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        soup = BeautifulSoup(html_content, "html.parser")

        for element in soup(['script', 'style', 'head', 'meta', 'link', 'title']):
            element.decompose()

        text = soup.get_text()

        lines = (line.strip() for line in text.splitlines())
        text = '\n'.join(line for line in lines if line)

        text = re.sub(r'\n\s*\n', '\n\n', text)  # Multiple newlines to double newlines
        text = re.sub(r' +', ' ', text)  # Multiple spaces to single space
        
        return text.strip()
        
    except Exception as e:
        print(f"Error extracting text from email {e}")
        # Fallback: simple regex HTML tag removal
        text = re.sub(r'<[^>]+>', '', html_content)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

def get_email_content(msg):
    """Extract email content from email"""
    content = ""
    if msg.text and msg.text.strip():
        content += msg.text.strip()
    elif msg.html and msg.html.strip():
        content += extract_text_from_html(msg.html)
        # If extraction failed or returned HTML, try a simpler approach
        if content.startswith('<!DOCTYPE') or '<html' in content[:100]:
            # Fallback: use regex to strip basic HTML tags
            content = re.sub(r'<[^>]+>', '', msg.html)
            content = re.sub(r'\s+', ' ', content)  # Clean up whitespace
            content = content.strip()
    
    # If still no content, try to get any available text
    if not content:
        content = str(msg).split('\n\n', 1)[-1] if '\n\n' in str(msg) else "No content available"
    
    return content


def is_job_related(subject, sender, content):
    """Check if email is job-related"""
    all_text = f"{subject}{sender}{content}".lower()

    for exclude_word in EXCLUDE_KEYWORDS:
        if exclude_word in all_text:
            return False
    
    for domain in TRUSTED_DOMAINS:
        if domain in sender.lower():
            return True
        
    job_keyword_count = sum(1 for keyword in JOB_KEYWORDS if keyword in all_text)
    return job_keyword_count >= 2

def filter_job_emails(mailbox, days_back = 10):
    """Filter and Extract job related emails"""
    try:
        since_date = datetime.now() - timedelta(days=days_back)
        since_date_only = since_date.date()
        messages = mailbox.fetch(AND(date_gte=since_date_only))

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

        print(f"\n📧 Found {len(job_emails)} job-related emails out of {processed_count} total emails")
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
        
        print(f"✓ Job emails saved to {filename}")
        return True
    except Exception as e:
        print("Error saving to file: {e}")
        return False
    

def extract_job_emails(username, password, days_back = 10, output_file = "job_emails.txt"):
    """Main function to extract job emails"""
    mailbox = connect_to_gmail(username, password)
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
    
    finally:
        disconnect_from_gmail(mailbox)

def main():
    """Main function to run the job email extractor"""
    
    # Get credentials
    username = input("Enter your Gmail address: ")
    password = input("Enter your App Password: ")
    
    # Extract job emails
    job_emails = extract_job_emails(
        username=username,
        password=password,
        days_back=10,
        output_file="job_emails.txt"
    )
    
    print(f"\n🎉 Extraction complete! Found {len(job_emails)} job-related emails.")
    
    # Optional: Show statistics
    if job_emails:
        domains = {}
        for email in job_emails:
            domain = email['sender'].split('@')[-1].split('>')[0] if '@' in email['sender'] else 'unknown'
            domains[domain] = domains.get(domain, 0) + 1
        
        print(f"\n📊 Top domains:")
        for domain, count in sorted(domains.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {domain}: {count} emails")


# def test_html_extraction():
#     """Test function to debug HTML extraction"""
#     sample_html = """
#     <!DOCTYPE html>
#     <html>
#     <head><title>Test</title>
#     <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />

#     <meta http-equiv="X-UA-Compatible" content="IE=edge" />

#     <title>General</title>

#     <meta name="author" content="" content="" />

#     <meta name="viewport" content="width=device-width, initial-scale=1.0" />

#     <meta name="x-apple-disable-message-reformatting">

#     <style type="text/css">

#         @import  url('https://fonts.googleapis.com/css2?family=Inter:wght@100..900&display=swap');



#         body {

#             width: auto;

#             background-color: #F6F8FA;

#             margin: 0 auto;

#             padding: 0;

#             font-size: 14px;

#             -webkit-text-size-adjust: 100% !important;

#             -ms-text-size-adjust: 100% !important;

#             -webkit-font-smoothing: antialiased;

#             font-family: "Inter", sans-serif;

#         }</head>
#     <body>
#         <h1>Adobe India Hackathon 2025</h1>
#         <p>Join us for an exciting hackathon!</p>
#         <p>Registration deadline: July 15, 2025</p>
#         <a href="https://example.com">Apply now</a>
#     </body>
#     </html>
#     """
    
#     extracted = extract_text_from_html(sample_html)
#     print("Extracted text:")
#     print(extracted)
#     return extracted


if __name__ == "__main__":
    # test_html_extraction()
    main()