import csv
from pathlib import Path

from bs4 import BeautifulSoup

TARGET_YEAR = '23'


def load_page(page_num: int) -> str:
    data_path = Path(__file__).parent / 'data'
    if not data_path.exists():
        data_path.mkdir()
    file_path = data_path / f'{page_num}.html'

    # TODO: Run headless Chrome to fetch page from https://secure.sensornetworkonline.com/SSIWeb/
    assert file_path.exists()

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
        for page_num in range(7):
            print(f'Loading page {page_num}.')
            page_text = load_page(page_num)
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
                if year < TARGET_YEAR:
                    print(f'Finished on page {page_num} at date {out_row["datetime"]}')
                    return
                if TARGET_YEAR < year:
                    continue
                writer.writerow(out_row)


main()
