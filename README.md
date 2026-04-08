# 🚀 Autofill Quiz Automation

This project automates the process of filling out online quizzes using Playwright. It connects to an existing browser session, identifies the quiz content, and automatically selects answers based on a provided JSON database.

## 📋 Features

- **Browser Connection**: Connects to an existing browser instance (Chrome/Brave) via WebSocket.
- **Dynamic Routing**: Automatically detects the current test number and skill (Listening/Reading) from the page title.
- **Intelligent Answering**: Uses a JSON database to find the correct answer for each question.
- **Multi-Page Support**: Automatically navigates through all pages of the quiz.
- **Error Handling**: Robust error handling for missing files, navigation issues, and parsing errors.

## 🛠️ Prerequisites

- Python 3.13+
- Playwright installed (`pip install playwright`)
- Browser installed and running with remote debugging enabled:
  ```bash
  brave-browser --remote-debugging-port=9222
  # or
  google-chrome --remote-debugging-port=9222
  ```

## 📂 Project Structure

```
autofill/
├── core/
│   ├── browser.py      # Browser management (connect/disconnect)
│   └── quiz_actor.py   # Quiz logic (answering, navigation)
├── data/
│   └── tests/
│       ├── test_01/
│       │   ├── listening.json
│       │   └── reading.json
│       └── ...
├── main.py             # Entry point
└── README.md           # Project documentation
```

## 📦 Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd autofill
   ```

2. Install dependencies:
   ```bash
   pip install playwright
   playwright install chromium
   ```

## 📂 Database Structure

Answers are stored in JSON files organized by test number and skill.

**Example: `data/tests/test_01/listening.json`**

```json
{
    "TEST_01": [
        {
            "id": "q_1",
            "question_text": "[Audio - Question text not printed]",
            "correct_answer_text": "(C)"
        },
        {
            "id": "q_2",
            "question_text": "[Audio - Question text not printed]",
            "correct_answer_text": "(D)"
        }
    ]
}
```

## ⚙️ Configuration

No explicit configuration is required. The script automatically detects:
- Browser port (default: 9222)
- Quiz URL pattern (must contain `elearning.thanglong`)
- Test number and skill from page title

## 🏃 Usage

1. Start your browser with remote debugging enabled:
   ```bash
   brave-browser --remote-debugging-port=9222
   ```

2. Open the quiz page in the browser.

3. Run the script:
   ```bash
   python3 main.py
   ```

4. The script will:
   - Connect to the browser
   - Detect the test
   - Fill in all answers
   - Navigate through pages
   - Stop when the end is reached

## 🔍 How It Works

1. **Browser Connection** (`BrowserManager`):
   - Scans for running browser instances on port 9222.
   - Connects to the first available browser.

2. **Quiz Detection** (`QuizActor`):
   - Extracts the page title (e.g., "PRACTICE TEST 1 - LISTENING").
   - Parses the test number and skill.
   - Loads the corresponding JSON database.

3. **Answering Logic**:
   - Scans for all radio buttons on the page.
   - Groups them by question ID.
   - Looks up the correct answer in the JSON database.
   - Selects the matching radio button.

4. **Navigation**:
   - Checks for a "Next" button.
   - Clicks it to move to the next page.
   - Repeats until no more pages are found.

## 🧪 Testing

To test with a specific test file, you can modify `main.py`:

```python
# In main.py, change the dynamic loading to a specific file:
# db_path = os.path.join("data", "tests", f"test_{test_num}", f"{skill}.json")
db_path = "data/tests/test_01/listening.json"
```

## 📝 Troubleshooting

### Execution context was destroyed
**Cause**: The browser page was closed or navigated away from during script execution.
**Solution**: Ensure the browser tab with the quiz remains open and active.

### Could not find the test title
**Cause**: The page title doesn't match the expected format or the element is hidden.
**Solution**: Verify the page title is in the format "PRACTICE TEST X - SKILL" and is visible.

### Database file not found
**Cause**: The JSON file for the detected test is missing.
**Solution**: Create the corresponding JSON file in `data/tests/`.

## 🤝 Contributing

1. Create a new JSON file for each test in `data/tests/`.
2. Ensure the file follows the structure shown in the example.
3. Run the script and verify it works correctly.
4. Commit and push changes:
   ```bash
   git add .
   git commit -m "chore: add test_XX data"
   git push
   ```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📧 Contact

[Your Name] - [Your Email]

Project Link: [https://github.com/Luo-Zhii/autofill_quiz](https://github.com/Luo-Zhii/autofill_quiz)
