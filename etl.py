import csv
import re
import psycopg2
import configparser


def stage_and_load(path, data, table):
    with open(path, 'w', newline='') as file:
        csv_writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        for d in data:
            csv_writer.writerow(d)

    parser = configparser.ConfigParser()
    parser.read('creds.txt')

    rds_conn = psycopg2.connect(
        dbname=parser.get('rds', 'db'),
        user=parser.get('rds', 'user'),
        host=parser.get('rds', 'host'),
        port=parser.get('rds', 'port'),
        password=parser.get('rds', 'password')
    )
    rds_cur = rds_conn.cursor()

    copy_sql = '''
        copy
            {}
        from
            stdout
        with
            csv
        header
    '''.format(table)

    with open(path, 'r') as file:
        rds_cur.copy_expert(copy_sql, file)

    rds_conn.commit()
    rds_conn.close()


chicago_inspections = []
chicago_violations = []

with open('data/chicago.csv', newline='') as file:
    reader = csv.DictReader(file)
    violation_regex = re.compile('([0-9])+\.(.*?)- Comments:(.*)')

    for row in reader:
        chicago_inspections.append([
            row['Inspection ID'],
            row['DBA Name'],
            row['AKA Name'],
            row['License #'],
            row['Facility Type'],
            row['Risk'],
            row['Address'],
            row['City'],
            row['State'],
            row['Zip'],
            row['Inspection Date'],
            row['Inspection Type'],
            row['Results'],
            row['Latitude'],
            row['Longitude'],
        ])

        for violation in row['Violations'].split('|'):
            violation = violation.strip()
            match = violation_regex.match(violation)

            if match:
                chicago_violations.append([row['Inspection ID']] + [g.strip() for g in match.groups()])

stage_and_load('data/stage_chicago_inspections.csv', chicago_inspections, 'chicago_inspections')
stage_and_load('data/stage_chicago_violations.csv', chicago_violations, 'chicago_violations')

nyc_inspections = {}
nyc_violations = []
current_id = -1

with open('data/new_york.csv', newline='', encoding='utf8') as file:
    reader = csv.DictReader(file)

    for row in reader:
        key_tuple = (row['CAMIS'], row['INSPECTION DATE'])

        if key_tuple not in nyc_inspections:
            current_id += 1

            nyc_inspections[key_tuple] = [
                current_id,
                row['CAMIS'],
                row['DBA'],
                row['BORO'],
                row['BUILDING'],
                row['STREET'],
                row['ZIPCODE'],
                row['PHONE'],
                row['CUISINE DESCRIPTION'],
                row['INSPECTION DATE'],
                row['ACTION'],
                row['SCORE'],
                row['GRADE'],
                row['GRADE DATE'],
                row['RECORD DATE'],
                row['INSPECTION TYPE'],
                row['Latitude'],
                row['Longitude']
            ]

        nyc_violations.append([
            current_id,
            row['VIOLATION CODE'],
            row['VIOLATION DESCRIPTION'],
            row['CRITICAL FLAG']
        ])

stage_and_load('data/stage_nyc_inspections.csv', nyc_inspections.values(), 'nyc_inspections')
stage_and_load('data/stage_nyc_violations.csv', nyc_violations, 'nyc_violations')
