# BREAD FINDER - Job Search Agent

An AI-powered assistant that helps automate job search tasks by connecting to your Gmail account to find and organize job-related emails.

## Features

- Connect to Gmail accounts securely
- Extract and filter job-related emails from your inbox
- Process resumes from desktop (PDF and text formats)
- Draft and send emails
- Save organized job information to text files
- Interactive conversational interface

## Prerequisites

- Python 3.12+
- Gmail account with app-specific password enabled
- OpenAI API key

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd bread-finder
```

2. Install required dependencies:
```bash
pip install langchain-openai langchain-core langgraph imap-tools PyPDF2
```

3. Set up your OpenAI API key as an environment variable:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

## Gmail Setup

To use this application with your Gmail account:

1. Enable 2-factor authentication on your Google account
2. Generate an app-specific password:
   - Go to Google Account settings
   - Select Security
   - Under "Signing in to Google," select App passwords
   - Generate a new app password for this application
3. Use your Gmail address and the app password (not your regular password)

## Usage

Run the application:
```bash
python app.py
```

The agent will guide you through:
1. Connecting to your Gmail account
2. Searching for job-related emails
3. Processing and organizing the results
4. Drafting responses or follow-up emails

## Available Tools

- `connect_to_gmail`: Connect to Gmail using credentials
- `disconnect_from_gmail`: Safely disconnect from Gmail
- `search_emails`: Extract job-related emails from specified timeframe
- `draft_email`: Create email drafts
- `send_email`: Send emails through your Gmail account
- `save_email`: Save content to text files
- `process_resume_from_desktop`: Read resume files from desktop


## Configuration

- Default email search timeframe: 10 days
- Supported resume formats: PDF, TXT
- Default desktop path: `C:\Users\Ankita\OneDrive\Desktop`

## Security Notes

- Credentials are stored temporarily in memory only
- Use app-specific passwords, never your main Gmail password
- The application only accesses your own Gmail account
- No data is transmitted to external servers except OpenAI API

## Dependencies

- `langchain-openai`: OpenAI integration
- `langchain-core`: Core LangChain functionality
- `langgraph`: Graph-based workflow management
- `imap-tools`: Gmail IMAP operations
- `PyPDF2`: PDF file processing

## Troubleshooting

### Common Issues

1. **Gmail connection failed**: 
   - Ensure you're using an app-specific password
   - Check that IMAP is enabled in Gmail settings

2. **Resume processing errors**:
   - Verify file exists on desktop
   - Ensure file format is PDF or TXT

3. **Email sending issues**:
   - Confirm Gmail connection is active
   - Check recipient email format

## License

This project is for personal use. Ensure compliance with Gmail's terms of service and applicable privacy laws.

## Contributing

This is a personal project. Feel free to fork and modify for your own use.

## Disclaimer

This tool is designed to work with your own Gmail account. Always follow email service provider terms of service and respect privacy regulations when processing emails.
