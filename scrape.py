import csv
import os
from pathlib import Path

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, Browser

TARGET_YEAR = '23'
# Pass in login credentials through environment variables.
GATEWAY_MAC = os.environ['GATEWAY_MAC']
LOGIN = os.environ['LOGIN']
PASSWORD = os.environ['PASSWORD']


class Session:
    def __init__(self, browser: Browser):
        self.page = browser.new_page()
        self.page.set_default_timeout(1_000)  # in ms
        self.page_num = -1

    def fetch_page(self, page_num: int) -> str:
        page = self.page
        history_timeout = 30_000  # in ms
        if self.page_num < 0:
            page.goto('https://secure.sensornetworkonline.com/SSIWeb/')
            page.locator('[id="login:mac"]').fill(GATEWAY_MAC)
            page.locator('[id="login:loginName"]').fill(LOGIN)
            page.locator('[id="login:password"]').fill(PASSWORD)
            page.get_by_role('button', name='Login').click(timeout=5_000)
            page.goto('https://secure.sensornetworkonline.com/SSIWeb/app/haccp'
                      '/alarmHistPopup.faces?firstAlarmFetch=0&maxAlarmFetch=256',
                      timeout=history_timeout)
            self.page_num = 0
        while self.page_num < page_num:
            page.get_by_role('button', name="<< Prev Alarms").click(
                timeout=history_timeout)
            self.page_num += 1
        page.wait_for_load_state()
        return page.content()

    def load_page(self, page_num: int) -> str:
        data_path = Path(__file__).parent / 'data'
        if not data_path.exists():
            data_path.mkdir()
        file_path = data_path / f'{page_num}.html'

        if not file_path.exists():
            text = self.fetch_page(page_num)
            file_path.write_text(text)
            return text

        return file_path.read_text()


def main():
    report_path = Path(__file__).parent / 'summary.csv'
    with report_path.open('w') as f:
        writer = csv.DictWriter(f, fieldnames=['alarm',
                                               'datetime',
                                               'gateway',
                                               'pod',
                                               'sensor_name',
                                               'sensor_value',
                                               'action',
                                               'resolved_datetime'])
        writer.writeheader()
        earliest_date = ''
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            session = Session(browser)
            for page_num in range(100):
                if earliest_date:
                    print(f'Reached {earliest_date}. ', end='')
                print(f'Loading page {page_num}.')
                page_text = session.load_page(page_num)
                soup = BeautifulSoup(page_text, 'html.parser')
                for table in soup.find_all('table'):
                    first_cell = table.tr.td.text
                    if first_cell != 'Alarm Name:':
                        continue
                    rows = table.find_all('tr')
                    out_row = dict(alarm=rows[0].find_all('td')[1].text,
                                   datetime=rows[0].find_all('td')[2].text.strip(),
                                   gateway=rows[1].find_all('td')[1].text,
                                   pod=rows[2].find_all('td')[1].text,
                                   sensor_name=rows[3].find_all('td')[1].text,
                                   sensor_value=rows[3].find_all('td')[3].text,
                                   action=rows[5].text.strip(),
                                   resolved_datetime=rows[6].text.strip())
                    out_row['sensor_value'] = ' '.join(out_row['sensor_value'].split())
                    year = out_row['datetime'][6:8]
                    earliest_date = out_row['datetime']
                    if year < TARGET_YEAR:
                        print(f'Finished on page {page_num} at date {out_row["datetime"]}')
                        browser.close()
                        return
                    if TARGET_YEAR < year:
                        continue
                    writer.writerow(out_row)


main()
