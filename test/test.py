import unittest
from unittest.mock import patch, MagicMock
import os
import csv
from selenium.common import NoSuchElementException
from selenium.webdriver.remote.webelement import WebElement

from main import load_env, get_latest_ep, read_csv, write_csv, send_line_notification


class MyTest(unittest.TestCase):
    CSV_DATA = [['name', 'url', 'xpath', 'latest_ep'],
                ['Manga 1', 'http://manga.com', '//a', '1'],
                ['Manga 2', 'http://manga2.com', '//div', '2']]

    def test_load_env_valid_file(self):
        # Arrange
        env_file_path = os.path.join(os.path.dirname(__file__), 'valid_test.env')
        expected_result = {'LINE_TOKEN': 'abc123', 'CSV': 'my_csv.csv'}

        # Act
        result = load_env(env_file_path)

        # Assert
        self.assertEqual(result, expected_result)

    def test_load_env_invalid_file(self):
        # Arrange
        env_file_path = os.path.join(os.path.dirname(__file__), 'invalid_test.env')
        expected_result = None
        # Act
        result = load_env(env_file_path)

        # Assert
        self.assertEqual(result, expected_result)

    def test_read_csv(self):
        # Test read_csv function with a sample CSV file
        csv_file_path = os.path.join(os.path.dirname(__file__), 'test_read.csv')
        data = read_csv(csv_file_path)

        self.assertEqual(data, self.CSV_DATA)

    def test_write_csv(self):
        # Test write_csv function by writing a row to a sample CSV file
        csv_file_path = os.path.join(os.path.dirname(__file__), 'test_write.csv')
        data = self.CSV_DATA
        write_csv(csv_file_path, data)

        with open(csv_file_path, 'r', newline='') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            written_data = [row for row in csv_reader]

        self.assertEqual(written_data, data)

    @patch('main.requests.post')
    def test_send_line_notification(self, mock_post):
        # Test send_line_notification function with a mocked requests.post call
        mock_response = MagicMock(status_code=200, text='OK')
        mock_post.return_value = mock_response

        response = send_line_notification(token='TOKEN', current_ep=1, latest_ep=2, manga_name='Manga',
                                          manga_url='http://manga.com')

        self.assertEqual(response, mock_response)

    @patch('selenium.webdriver.Chrome')
    def test_returns_latest_ep_number(self, mock_driver):
        mock_element = MagicMock(spec=WebElement)
        mock_element.get_attribute.return_value = 'Episode 10'
        mock_driver().find_elements.return_value = [mock_element]

        result = get_latest_ep('https://example.com', '//xpath')
        self.assertEqual(result, 10)

    @patch('selenium.webdriver.Chrome')
    def test_returns_negative_one_when_no_number_found(self, mock_driver):
        mock_element = MagicMock(spec=WebElement)
        mock_element.get_attribute.return_value = 'Episode X'
        mock_driver().find_elements.return_value = [mock_element]

        result = get_latest_ep('https://example.com', '//xpath')
        self.assertEqual(result, -1)

    @patch('selenium.webdriver.Chrome')
    def test_closes_driver_when_exception_occurs(self, mock_driver):
        mock_driver().find_elements.side_effect = NoSuchElementException

        with self.assertRaises(NoSuchElementException):
            get_latest_ep('https://example.com', '//xpath')

        mock_driver().close.assert_called_once()


if __name__ == '__main__':
    unittest.main()
