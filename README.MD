# Manga Episode Checker

This Python script checks for new episodes of manga and sends notifications using LINE API. It uses Selenium for web scraping and requests for sending notifications.

## Requirements

- Python 3.8
- Selenium 4.8.2
- python-dotenv
- requests
- webdriver_manager 3.8.5
- csv

## Installation

1. Clone this repository or download the script.
2. Install the required Python packages using pip:

```bash
pip install selenium
pip install dotenv
pip install requests
pip install webdriver_manager
```

3. Download and install ChromeDriver from here based on your operating system and Chrome version.
4. Create a .env file in the same directory as the script with the following contents:

```env
LINE_TOKEN=YOUR_LINE_TOKEN
CSV=YOUR_CSV_FILE_NAME.csv
```

Replace YOUR_LINE_TOKEN with your LINE API token, and YOUR_CSV_FILE_NAME.csv with the name of your CSV file containing manga information.

## Usage
Update your CSV file with the manga details, including manga name, manga URL, XPath for the new episode element, and current episode number.
Run the script using Python:

```bash
python manga_episode_checker.py
```

## Contributing
If you'd like to contribute to this project, feel free to fork the repository and submit a pull request.

## License
I don't care. Just do this for fun.