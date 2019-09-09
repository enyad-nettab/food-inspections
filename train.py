import psycopg2.extras
import configparser
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn.metrics import confusion_matrix
import pickle

parser = configparser.ConfigParser()
parser.read('creds.txt')

rds_conn = psycopg2.connect(
    dbname=parser.get('rds', 'db'),
    user=parser.get('rds', 'user'),
    host=parser.get('rds', 'host'),
    port=parser.get('rds', 'port'),
    password=parser.get('rds', 'password')
)

rds_cur = rds_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

rds_cur.execute(
    '''
        select
            inspection_id,
            results
        from
            inspection_view
        where
            inspection_authority = 'Chicago'
            and results in ('Pass', 'Fail', 'Pass w/ Conditions')
    '''
)

inspections_raw = rds_cur.fetchall()

rds_cur.execute(
    '''
        select
            inspection_id,
            violation_code
        from
            violation_view
        where
            inspection_authority = 'Chicago'
    '''
)

violations_raw = rds_cur.fetchall()

y_categories = {}
y_category_index = 0
x_categories = {}
x_category_index = 0
inspections = {}

for i in inspections_raw:
    if i['results'] not in y_categories:
        y_categories[i['results']] = y_category_index
        y_category_index += 1

    inspections[i['inspection_id']] = {
        'result': y_categories[i['results']],
        'violations': []
    }

for v in violations_raw:
    if v['violation_code'] not in x_categories:
        x_categories[v['violation_code']] = x_category_index
        x_category_index += 1

    if v['inspection_id'] not in inspections:
        continue

    inspections[v['inspection_id']]['violations'].append(x_categories[v['violation_code']])

y = np.zeros((len(inspections), ))
x = np.zeros((len(inspections), len(x_categories)))

for index, i in enumerate(inspections.values()):
    y[index] = i['result']

    for v in i['violations']:
        x[index, v] = 1

x_train, x_test, y_train, y_test = train_test_split(x, y, train_size=5000 / len(inspections), random_state=42)

classifier = SVC(gamma='auto', probability=True, class_weight='balanced')
classifier.fit(x_train, y_train)

print(classifier.score(x_test, y_test))

pred_y = classifier.predict(x_test)

rev_y_cats = {v: k for k, v in y_categories.items()}

print(rev_y_cats)

cm = confusion_matrix(y_test, pred_y)
print(cm)

with open('data/chicago_model.pkl', 'wb') as pickle_file:
    pickle.dump(classifier, pickle_file)

with open('data/chicago_y_categories.pkl', 'wb') as y_file:
    pickle.dump(rev_y_cats, y_file)

with open('data/chicago_x_categories.pkl', 'wb') as x_file:
    pickle.dump(x_categories, x_file)
