import pandas as pd
import numpy as np
from sklearn import cross_validation as cv
from sklearn.tree import DecisionTreeRegressor
import numpy as np
import time
from sklearn.externals import joblib
from sklearn.ensemble import RandomForestRegressor
import json as js
from geopy.distance import vincenty

global filename_prefix
global filename_tree


# filename_tree


def data_import(origin_location, data_type):
    data = pd.read_csv(origin_location)  #
    # Parse the datestrings to datetime-objects
    data['pickup_datetime'] = pd.to_datetime(data['pickup_datetime'], format='%Y-%m-%d %H:%M:%S')
    data['dropoff_datetime'] = pd.to_datetime(data['dropoff_datetime'], format='%Y-%m-%d %H:%M:%S')
    data['trip_time'] = data.dropoff_datetime - data.pickup_datetime
    return data


def data_import(dataRoot_import, data_type):
    data = pd.read_csv(dataRoot_import)  #
    # Parse the datestrings to datetime-objects

    if data_type == 'Bike':
        data = data.rename(columns={'starttime': 'pickup_datetime', 'stoptime': 'dropoff_datetime',
                                    'start station latitude': 'pickup_latitude',
                                    'start station longitude': 'pickup_longitude',
                                    'end station latitude': 'dropoff_latitude',
                                    'end station longitude': 'dropoff_longitude', 'tripduration': 'trip_time'})
        data['trip_dist'] = -1
        for i in range(0, (len(data) - 1)):
            pickup = (data.iloc[i]['pickup_latitude'], data.iloc[i]['pickup_longitude'])
            dropoff = (data.iloc[i]['dropoff_latitude'], data.iloc[i]['dropoff_longitude'])
            data.set_value(i, 'trip_distance', vincenty(pickup, dropoff).meters)

    data['pickup_datetime'] = pd.to_datetime(data['pickup_datetime'], format='%Y-%m-%d %H:%M:%S')
    data['dropoff_datetime'] = pd.to_datetime(data['dropoff_datetime'], format='%Y-%m-%d %H:%M:%S')

    if data_type == 'Taxi':
        data['trip_time'] = data.dropoff_datetime - data.pickup_datetime
    return data


def slice_data(dataFrame, save_output_in_csv, start_date, end_date):
    # Be aware: the end_date is not included in the dataFrame!
    # Initialize the filename_prefix
    filename_prefix = ('taxi_from_', start_date, 'to_', end_date)
    # data = pd.read_csv(dataRoot_data)
    # dataFrame['pickup_datetime'] = pd.to_datetime(dataFrame['pickup_datetime'], format='%Y-%m-%d %H:%M:%S')
    # dataFrame['dropoff_datetime'] = pd.to_datetime(dataFrame['dropoff_datetime'], format='%Y-%m-%d %H:%M:%S')
    start_date = pd.to_datetime(start_date)
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    mask = (dataFrame['pickup_datetime'] >= start_date) & (dataFrame['pickup_datetime'] < end_date)
    # sliceDF = pd.DataFrame()
    sliceDF = dataFrame[mask]
    sliceDF = sliceDF.sort_values('pickup_datetime')
    sliceDF.reset_index(drop=True, inplace=True)
    if save_output_in_csv:
        sliceDF.to_csv((filename_prefix, '.csv'))
    return sliceDF


def drop_overhead(data, list_drop):
    for x in list_drop:
        data = data.drop(str(x), axis=1)
    return data


def drop_anomaly(data):
    lower_bound = 0.5
    upper_bound = 2.5
    data['avg_amount_per_minute'] = (data.fare_amount - 2.5) / (data.trip_time / np.timedelta64(1, 'm'))
    data = data.replace(np.float64(0), np.nan)

    anomaly = data.loc[(data['dropoff_longitude'].isnull()) | (data['dropoff_latitude'].isnull()) | (
    data['pickup_longitude'].isnull()) | (data['pickup_latitude'].isnull()) | (data['trip_time'].isnull()) | (
                       data['trip_distance'].isnull())]
    anomaly = anomaly.append(
        data.loc[(data['avg_amount_per_minute'] > upper_bound) | (data['avg_amount_per_minute'] < lower_bound)])
    data = data.drop(anomaly.index)
    return data


def bounding_box(data, upperleft, lowerright):
    data = data.loc[(data['dropoff_latitude'] > lowerright[0]) &
                    (data['dropoff_longitude'] < lowerright[1]) &
                    (data['dropoff_latitude'] < upperleft[0]) &
                    (data['dropoff_longitude'] > upperleft[1]) &
                    (data['pickup_latitude'] > lowerright[0]) &
                    (data['pickup_longitude'] < lowerright[1]) &
                    (data['pickup_latitude'] < upperleft[0]) &
                    (data['pickup_longitude'] > upperleft[1])
                    ]
    return data


def train_decision_tree(time_regression_df, test_size, random_state, max_depth, export_testset):
    y = time_regression_df["trip_time_in_mins"]
    X = time_regression_df.ix[:, 0:6]
    X_train, X_test, y_train, y_test = cv.train_test_split(X, y, test_size=test_size, random_state=random_state)

    if bool(export_testset) is True:
        Xy_test = pd.concat([X_test, y_test], axis=1)
        Xy_test.to_csv('taxi_tree_test_Xy_20130506-12.csv')

    t = time.time()

    regtree = DecisionTreeRegressor(min_samples_split=3, random_state=random_state, max_depth=max_depth)
    regtree.fit(X_train, y_train)
    elapsed = time.time() - t;
    export_meta_data(regtree, X_test, y_test, elapsed)

    return regtree


def export_meta_data(tree_model, X_test, y_test, training_duration):
    # Export Meta-File
    # Determine the tree error
    y_pred = tree_model.predict(X_test)
    np.linalg.norm(np.ceil(y_pred) - y_test)
    diff = (y_pred - y_test)
    # plt.figure(figsize=(12,10)) # not needed. set values globally
    plt.hist(diff.values, bins=40)
    error_distribution = ('Perzentile(%): ', [1, 5, 10, 15, 25, 50, 75, 90, 95, 99], '\n',
                          np.percentile(diff.values, [1, 5, 10, 15, 25, 50, 75, 85, 90, 95, 99]))
    absolute_deviation = ('Absolute time deviation (in 1k): ', sum(abs(diff)))
    mean_deviation = absolute_deviation / len(y_pred)
    plt.title('Simple Decision Tree Regressor')
    plt.xlabel('deviation in minutes')
    plt.ylabel('frequency')
    plt.savefig((filename_prefix, '_error_plot.png'))
    tree_meta_data = {'training_time': training_duration,
                      'absolute_time_deviation': absolute_deviation,
                      'mean_abs._deviation': mean_deviation,
                      'error_distribition': error_distribution,
                      'max_depth': tree_model.tree_.max_depth,
                      'leaves_number': 'Amount if leaves',
                      'split_distribution': 'Frequency of splits'}
    # dump the metadata dictionary as a JSON-File
    with open((filename_prefix, '_tree_metadata.json', 'w')) as fp:
        js.dump(tree_meta_data, fp)


def train_random_forest(time_regression_df, test_size, random_state, max_depth, export_testset):
    y = time_regression_df["trip_time_in_mins"]
    X = time_regression_df.ix[:, 0:6]
    X_train, X_test, y_train, y_test = cv.train_test_split(X, y, test_size=test_size, random_state=random_state)

    if bool(export_testset) is True:
        Xy_test = pd.concat([X_test, y_test], axis=1)
        Xy_test.to_csv('taxi_forest_test_Xy_20130506-12.csv')

    rd_regtree = RandomForestRegressor(n_estimators=20, n_jobs=6, min_samples_split=3, random_state=random_state,
                                       max_depth=max_depth)
    rd_regtree.fit(X_train, y_train)

    return rd_regtree


def create_tree_dataframe(data):
    # Baum DataFrame:
    time_regression_df = pd.DataFrame([
        data['pickup_datetime'].dt.dayofweek,
        data['pickup_datetime'].dt.hour,
        data['pickup_latitude'],
        data['pickup_longitude'],
        data['dropoff_latitude'],
        data['dropoff_longitude'],
        np.ceil(data['trip_time'] / np.timedelta64(1, 'm')),
    ]).T

    time_regression_df.columns = [
        'pickup_datetime_dayofweek', 'pickup_datetime_hour',
        'pickup_latitude', 'pickup_longitude', 'dropoff_latitude', 'dropoff_longitude',
        'trip_time_in_mins']

    return time_regression_df


def dump_tree(decision_model, dataRoot_tree_model):
    joblib.dump(decision_model, str(dataRoot_tree_model), protocol=2)
