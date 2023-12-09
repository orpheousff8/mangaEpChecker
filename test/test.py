import unittest
from unittest.mock import patch, MagicMock
import os
import csv
from selenium.common import NoSuchElementException
from selenium.webdriver import Chrome
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from bcolors import bcolors
from main import load_env, fetch_driver_version, get_latest_ep, read_csv, write_csv, send_line_notification,  main, \
    NoNumberInLinkTextException, NoElementsException


class MyTest(unittest.TestCase):
    CONFIG_KEYS = ('CSV', 'LATEST_RELEASE_URL', 'LINE_TOKEN')
    driver = None
    CSV_DATA = [['name', 'url', 'xpath', 'latest_ep'],
                ['Manga 1', 'http://manga.com', '//a', '1'],
                ['Manga 2', 'http://manga2.com', '//div', '2']]

    def test_load_env_valid_file(self):
        # Arrange
        env_file_path = os.path.join(os.path.dirname(__file__), 'valid_test.env')
        expected_result = {'LINE_TOKEN': 'abc123', 'CSV': 'my_csv.csv',
                           'LATEST_RELEASE_URL': 'https://example.com.json'}

        # Act
        result = load_env(filename=env_file_path, config_keys=self.CONFIG_KEYS)

        # Assert
        self.assertEqual(result, expected_result)

    def test_load_env_invalid_file(self):
        # Arrange
        env_file_path = os.path.join(os.path.dirname(__file__), 'invalid_test.env')
        expected_result = None
        # Act
        result = load_env(filename=env_file_path, config_keys=self.CONFIG_KEYS)

        # Assert
        self.assertEqual(result, expected_result)

    @patch('requests.get')
    def test_fetch_driver_version_success(self, mock_requests_get):
        # Arrange
        mock_response = mock_requests_get.return_value
        mock_response.status_code = 200
        mock_response.json.return_value = {'channels': {'Stable': {'version': '1.0.0'}}}  # Example JSON response

        latest_release_url = 'http://example.com/latest_release'

        # Act
        result = fetch_driver_version(latest_release_url)

        # Assert
        self.assertEqual(result, '1.0.0')

    @patch('requests.get')
    def test_fetch_driver_version_failure(self, mock_requests_get):
        # Arrange
        mock_response = mock_requests_get.return_value
        mock_response.status_code = 404  # Simulating a failed request

        latest_release_url = 'http://example.com/latest_release'

        # Act
        result = fetch_driver_version(latest_release_url)

        # Assert
        self.assertIsNone(result)

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

        response = send_line_notification(token='TOKEN', current_ep='1', latest_ep='2', manga_name='Manga',
                                          manga_url='http://manga.com')

        self.assertEqual(response, mock_response)

    @unittest.skip("skip create driver test")
    @patch('webdriver_manager.chrome.ChromeDriverManager.install')
    def test_create_chrome_driver(self, mock_install):
        config = {
            'LATEST_RELEASE_URL': 'https://example.com/latest_release'
        }
        options = Options()
        driver_version = '1.0'

        # Mock the ChromeDriverManager to avoid actual installation during tests

        mock_install.return_value = 'path_to_chromedriver'
        service = ChromeService(ChromeDriverManager(
            latest_release_url=config['LATEST_RELEASE_URL'],
            driver_version=driver_version).install())
        driver = Chrome(service=service, options=options)
        self.assertIsInstance(driver, Chrome)
        mock_install.assert_called_once_with()

    def test_valid_elements_asc_order(self):
        # Mocking the driver and its methods
        mock_driver = MagicMock(spec=Chrome)
        mock_driver.title = "Manga Title"
        mock_element1 = MagicMock(spec=WebElement)
        mock_element1.get_attribute.return_value = "Chapter 1.5"
        mock_element2 = MagicMock(spec=WebElement)
        mock_element2.get_attribute.return_value = "Chapter 2.0"
        mock_driver.find_elements.return_value = [mock_element1, mock_element2]

        get_latest_ep_parameters = {"manga_url": "https://example.com", "xpath": "//xpath", "driver": mock_driver}

        result = get_latest_ep(parameters_dict=get_latest_ep_parameters)
        self.assertEqual(result, 2.0)

    def test_valid_elements_desc_order(self):
        # Mocking the driver and its methods
        mock_driver = MagicMock(spec=Chrome)
        mock_driver.title = "Manga Title"
        mock_element1 = MagicMock(spec=WebElement)
        mock_element1.get_attribute.return_value = "Chapter 2.0"
        mock_element2 = MagicMock(spec=WebElement)
        mock_element2.get_attribute.return_value = "Chapter 1.5"
        mock_driver.find_elements.return_value = [mock_element1, mock_element2]

        get_latest_ep_parameters = {"manga_url": "https://example.com", "xpath": "//xpath", "driver": mock_driver}

        result = get_latest_ep(parameters_dict=get_latest_ep_parameters)
        self.assertEqual(result, 2.0)

    def test_no_elements(self):
        mock_driver = MagicMock(spec=Chrome)
        mock_driver.find_elements.return_value = []

        get_latest_ep_parameters = {"manga_url": "https://example.com", "xpath": "//xpath", "driver": mock_driver}

        with self.assertRaises(NoElementsException):
            get_latest_ep(parameters_dict=get_latest_ep_parameters)

    def test_no_number_in_link_text(self):
        mock_driver = MagicMock(spec=Chrome)
        mock_element = MagicMock(spec=WebElement)
        mock_element.get_attribute.return_value = "Chapter No Number"
        mock_driver.find_elements.return_value = [mock_element]

        get_latest_ep_parameters = {"manga_url": "https://example.com", "xpath": "//xpath", "driver": mock_driver}

        with self.assertRaises(NoNumberInLinkTextException):
            get_latest_ep(parameters_dict=get_latest_ep_parameters)

    def test_selenium_no_such_element_exception(self):
        mock_driver = MagicMock(spec=Chrome)
        mock_driver.find_elements.side_effect = NoSuchElementException

        get_latest_ep_parameters = {"manga_url": "https://example.com", "xpath": "//xpath", "driver": mock_driver}

        with self.assertRaises(NoSuchElementException):
            get_latest_ep(parameters_dict=get_latest_ep_parameters)

    @unittest.skip("skip test no new ep")
    @patch('main.write_csv')
    @patch('main.send_line_notification')
    @patch('main.get_latest_ep')
    @patch('main.read_csv')
    @patch('main.load_env')
    @patch('builtins.print')
    @patch('main.create_chrome_driver')
    @patch('main.fetch_driver_version')
    def test_no_new_ep(self, mock_write_csv, mock_send_line_notification,
                       mock_get_latest_ep, mock_read_csv, mock_load_env, mock_print, mock_create_driver,
                       mock_fetch_driver_version):
        # Arrange
        mock_load_env.return_value = {'CSV': 'test.csv', 'LATEST_RELEASE_URL': 'test_url', 'LINE_TOKEN': 'test_token'}
        mock_read_csv.return_value = [['Manga', 'http://example.com', '//a', '1']]
        mock_get_latest_ep.return_value = 1.0
        mock_fetch_driver_version.return_value = '1.0'
        mock_create_driver.return_value = MagicMock(spec=Chrome)

        # Act and Assert
        with self.assertRaises(SystemExit) as cm:
            main()

        self.assertEqual(cm.exception.code, None)
        mock_write_csv.assert_not_called()
        mock_send_line_notification.assert_not_called()
        mock_print.assert_called_with(f'\n{bcolors.OKBLUE}No update to DB.{bcolors.ENDC}')

    @unittest.skip("skip test new ep")
    @patch('main.write_csv')
    @patch('main.send_line_notification')
    @patch('main.get_latest_ep')
    @patch('main.read_csv')
    @patch('main.load_env')
    @patch('builtins.print')
    @patch('main.create_chrome_driver')
    @patch('main.fetch_driver_version')
    def test_new_ep(self, mock_write_csv, mock_send_line_notification,
                    mock_get_latest_ep, mock_read_csv, mock_load_env, mock_print, mock_create_driver,
                    mock_fetch_driver_version):
        # Arrange
        mock_load_env.return_value = {'CSV': 'test.csv', 'LATEST_RELEASE_URL': 'test_url', 'LINE_TOKEN': 'test_token'}
        mock_read_csv.return_value = [['name', 'url', 'xpath', 'latest_ep'],
                                      ['Manga', 'http://example.com', '//a', '1.0']]
        mock_fetch_driver_version.return_value = '1.0'
        mock_create_driver.return_value = MagicMock(spec=Chrome)
        mock_get_latest_ep.return_value = 2.0
        mock_send_line_notification.return_value.status_code = 200
        mock_send_line_notification.return_value.text = 'OK'

        # Act
        main()

        # Assert

        mock_fetch_driver_version.assert_called_once_with('test_url')

        # Get the calls made to the mocked print function
        calls = mock_print.mock_calls

        # Define the expected lines of output
        expected_output = [
            f'\nManga is at http://example.com, with current Ep.1 in DB',
            f'Ep.2 is the latest Ep on the web',
            f'{bcolors.OKGREEN}New ep!{bcolors.ENDC}',
            f'Line notification status: 200: OK',
            f'\n{bcolors.OKGREEN}DB updated{bcolors.ENDC}',
            f'{bcolors.OKBLUE}Manga{bcolors.ENDC} is at http://example.com, last read at Ep.1, latest at Ep.2'
        ]

        mock_write_csv.assert_called_with('test.csv', [['name', 'url', 'xpath', 'latest_ep'],
                                                       ['Manga', 'http://example.com', '//a', '2.0']])

        mock_send_line_notification.assert_called_with('test_token', '1', '2', 'Manga', 'http://example.com')

        # Assert that the printed lines match the expected output
        self.assertEqual(len(calls), len(expected_output), "Number of printed lines doesn't match")

        for call, expected_line in zip(calls, expected_output):
            _, args, _ = call
            printed_line = args[0]
            self.assertEqual(printed_line, expected_line)


if __name__ == '__main__':
    unittest.main()
