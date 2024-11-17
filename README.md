# Conversational-Chatbot-Using-OpenAI-and-LLM

An AI-powered conversational interface that helps users build comprehensive professional profiles through natural dialogue.

## Features

- Interactive chat interface
- Real-time profile updates
- Profile completion tracking
- Multi-field profile support:
  - Basic Information
  - Education
  - Experience
  - Skills
  - Additional Information

## Prerequisites

- Python 3.9 or higher
- OpenAI API key

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd Chat_Bot
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root and add your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

## Running the Application

1. Make sure you're in the project directory:
```bash
cd Chat_Bot
```

2. Run the GUI:
```bash
python gui.py
```

## Using the Chatbot

1. The interface is split into three sections:
   - Left: Chat interface for interacting with the bot
   - Right Top: Profile details in tabbed view
   - Right Bottom: Profile completion progress

2. Start by entering your name when prompted
3. Continue the conversation naturally, providing information about:
   - Basic details (age, location)
   - Education (degree, institution, graduation year)
   - Professional experience
   - Skills and expertise

4. The profile sections will update automatically as you provide information
5. Track your progress with the completion meter

## Project Structure

- `gui.py`: Main GUI application
- `profile_manager.py`: Handles profile data and updates
- `session_manager.py`: Manages chat sessions
- `profile_summarizer.py`: Generates profile summaries
- `.env`: Configuration file for API keys

## Error Handling

- If you encounter any errors:
  1. Check your OpenAI API key in `.env`
  2. Ensure all required packages are installed
  3. Verify Python version (3.9+)

## Support

For issues or questions, please open an issue in the repository.
