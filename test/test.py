import unittest
from unittest.mock import patch, MagicMock
import os
import csv
from selenium.common import NoSuchElementException
from selenium.webdriver.remote.webelement import WebElement

from main import load_env, get_latest_ep, read_csv, write_csv, send_line_notification, main, NoNumberInLinkTextException


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

    @patch('requests.post')
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
    def test_raise_NoNumberInLinkTextException_when_no_number_found(self, mock_driver):
        # Arrange
        mock_element = MagicMock(spec=WebElement)
        mock_element.get_attribute.return_value = 'Episode X'
        mock_driver().find_elements.return_value = [mock_element]

        # Act and Assert
        with self.assertRaises(NoNumberInLinkTextException):
            get_latest_ep('https://example.com', '//xpath')

    @patch('selenium.webdriver.Chrome')
    def test_closes_driver_when_exception_occurs(self, mock_driver):
        mock_driver().find_elements.side_effect = NoSuchElementException

        with self.assertRaises(NoSuchElementException):
            get_latest_ep('https://example.com', '//xpath')

        mock_driver().close.assert_called_once()

    @patch('builtins.print')
    @patch('main.load_env')
    @patch('main.read_csv')
    @patch('main.get_latest_ep')
    @patch('main.send_line_notification')
    @patch('main.write_csv')
    def test_no_new_ep(self, mock_write_csv, mock_send_line_notification,
                       mock_get_latest_ep, mock_read_csv, mock_load_env, mock_print):
        # Arrange
        mock_load_env.return_value = {'CSV': 'test.csv', 'LINE_TOKEN': 'test_token'}
        mock_read_csv.return_value = [['Manga', 'http://example.com', '//a', '1']]
        mock_get_latest_ep.return_value = 1

        # Act and Assert
        with self.assertRaises(SystemExit) as cm:
            main()

        self.assertEqual(cm.exception.code, None)
        mock_write_csv.assert_not_called()
        mock_send_line_notification.assert_not_called()
        mock_print.assert_called_with('\nNo update to DB.')

    @patch('builtins.print')
    @patch('main.load_env')
    @patch('main.read_csv')
    @patch('main.get_latest_ep')
    @patch('main.send_line_notification')
    @patch('main.write_csv')
    def test_new_ep(self, mock_write_csv, mock_send_line_notification,
                    mock_get_latest_ep, mock_read_csv, mock_load_env, mock_print):
        # Arrange
        mock_load_env.return_value = {'CSV': 'test.csv', 'LINE_TOKEN': 'test_token'}
        mock_read_csv.return_value = [['name', 'url', 'xpath', 'latest_ep'],
                                      ['Manga', 'http://example.com', '//a', '1']]
        mock_get_latest_ep.return_value = 2
        mock_send_line_notification.return_value.status_code = 200
        mock_send_line_notification.return_value.text = 'OK'

        # Act
        main()

        # Assert
        mock_write_csv.assert_called_with('test.csv', [['name', 'url', 'xpath', 'latest_ep'],
                                                       ['Manga', 'http://example.com', '//a', '2']])
        mock_send_line_notification.assert_called_with('test_token', 1, 2, 'Manga', 'http://example.com')
        mock_print.assert_called_with('200: OK')


if __name__ == '__main__':
    unittest.main()
