import sys
import os
import re
import csv
import requests
from dotenv import dotenv_values
from requests import Response
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from typing import Optional
from bcolors import bcolors


class NoNumberInLinkTextException(Exception):
    pass


class NoElementsException(Exception):
    pass


def load_env(filename) -> Optional[dict[str, str | None]]:
    config = dotenv_values(filename)

    config_keys = ('LINE_TOKEN', 'CSV')

    if all(key in config for key in config_keys):
        return config
    return None


def get_latest_ep(manga_url: str, xpath: str, render_seconds: int = 3) -> Optional[float]:
    # Run Chrome in headless mode as Neko-post is Client-side rendering
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument('--headless=new')
    options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager(
        latest_release_url='https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json',
        driver_version='116.0.5845.96').install()), options=options)
    # driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

    driver.get(manga_url)

    title = driver.title
    print(f"{bcolors.HEADER}{title}{bcolors.ENDC}")

    # Wait for page to render
    print(f'Waiting for {render_seconds} seconds to render the page.')
    driver.implicitly_wait(render_seconds)

    try:
        elements = driver.find_elements(By.XPATH, xpath)
        if len(elements) == 0:
            driver.close()
            raise NoElementsException
    except NoSuchElementException:
        driver.close()
        raise

    # need to find both first and last because the order is either ASC or DSC depends on website
    link_text1 = elements[0].get_attribute('innerText')
    link_text2 = elements[-1].get_attribute('innerText')
    # print(link_text1)
    # print(link_text2)
    driver.close()

    # Use a regular expression to extract only the number
    match1 = re.search(r'\d+(\.\d+)?', link_text1)
    match2 = re.search(r'\d+(\.\d+)?', link_text2)
    if match1 or match2:
        latest_ep = max(float(match1.group()), float(match2.group()))
        return latest_ep
    else:
        raise NoNumberInLinkTextException


def read_csv(csv_name: str) -> list[list[str]]:
    # Open the CSV file for reading
    with open(os.path.join(sys.path[0], csv_name), 'r', newline='') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        data = [row for row in csv_reader]
    return data


def write_csv(csv_name: str, data):
    with open(os.path.join(sys.path[0], csv_name), 'w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerows(data)


def float_to_str(num: float) -> str:
    int_num = int(num)
    if num == int_num:
        return str(int_num)
    return str(num)


def send_line_notification(token: str, current_ep: str, latest_ep: str, manga_name: str, manga_url: str) -> Response:
    print("Sending Line notification")
    payload = {
        'message': f'{manga_name} newer ep.{latest_ep} is out! '
                   f'Last read Ep.{current_ep} at {manga_url}'}
    response = requests.post('https://notify-api.line.me/api/notify',
                             headers={f'Authorization': f'Bearer {token}'}, params=payload)

    return response


def main():
    config = load_env(os.path.join(sys.path[0], '.env'))
    if not config:
        print(f'{bcolors.WARNING}.env file is invalid. Aborted!{bcolors.ENDC}')
        exit()

    csv_name = config['CSV']
    new_ep_list = []

    try:
        data = read_csv(csv_name)
        if not data:
            print(f'\n{bcolors.WARNING}No Data In CSV. Abort.{bcolors.ENDC}')
            exit()
    except Exception as e:
        print(f"An error occurred while writing to the CSV file: {e}")
        raise

    for i in range(1, len(data)):
        manga_name = data[i][0]
        manga_url = data[i][1]
        xpath = data[i][2]
        current_ep = float(data[i][3])

        print(f'\n{manga_name} is at {manga_url} with current Ep.{float_to_str(current_ep)} in DB.')
        try:
            latest_ep = get_latest_ep(manga_url=manga_url, xpath=xpath)
            print(f'Ep.{float_to_str(latest_ep)} is the latest Ep on the web.')
        except NoSuchElementException:
            print(f'{bcolors.WARNING}An element of new ep not found{bcolors.ENDC}')
            continue
        except NoNumberInLinkTextException:
            print(f'{bcolors.WARNING}Error: No number found in link text{bcolors.ENDC}')
            continue
        except NoElementsException:
            print(f'{bcolors.WARNING}Error: Elements are empty. Need to check page or XPATH{bcolors.ENDC}')
            continue

        if latest_ep > current_ep:
            new_ep_list.append((manga_name, manga_url, current_ep, latest_ep))
            print(f'{bcolors.OKGREEN}New ep!{bcolors.ENDC}')
            data[i][3] = str(latest_ep)

            response = send_line_notification(config["LINE_TOKEN"], float_to_str(current_ep), float_to_str(latest_ep),
                                              manga_name, manga_url)
            print(f'{response.status_code}: {response.text}')
        else:
            print(f'{bcolors.OKBLUE}No new ep{bcolors.ENDC}')

    if len(new_ep_list) == 0:
        print(f'\n{bcolors.OKBLUE}No update to DB.{bcolors.ENDC}')
        exit()

    # Open the same CSV file for writing if there is a new ep
    try:
        write_csv(csv_name, data)
        print(f"\n{bcolors.OKGREEN}DB updated{bcolors.ENDC}")
    except Exception as e:
        print(f"An error occurred while reading the CSV file: {e}")
        raise

    for i in range(0, len(new_ep_list)):
        manga_name = new_ep_list[i][0]
        manga_url = new_ep_list[i][1]
        current_ep = float_to_str(new_ep_list[i][2])
        latest_ep = float_to_str(new_ep_list[i][3])

        print(
            f'{bcolors.OKBLUE}{manga_name}{bcolors.ENDC} is at {manga_url}, last read at Ep. {current_ep}, latest Ep. at {latest_ep}')


if __name__ == '__main__':
    main()
