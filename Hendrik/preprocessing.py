import pandas as pd
import numpy as np
from sklearn import cross_validation as cv
from sklearn.tree import DecisionTreeRegressor
import numpy as np
import matplotlib.pyplot as plt
import time
from sklearn.externals import joblib
from sklearn.ensemble import RandomForestRegressor


    def data_import(self, dataRoot_import):
        data = pd.read_csv(dataRoot_import)
        data['pickup_datetime'] = pd.to_datetime(data['pickup_datetime'], format = '%Y-%m-%d %H:%M:%S')
        data['dropoff_datetime'] = pd.to_datetime(data['dropoff_datetime'], format ='%Y-%m-%d %H:%M:%S')
        data['trip_time'] = data.dropoff_datetime - data.pickup_datetime
        return data

    def slice_data(self, dataRoot_data, dataRoot_week, start_date, end_date):
        data = pd.read_csv(dataRoot_data)
        data['pickup_datetime'] = pd.to_datetime(data['pickup_datetime'], format='%Y-%m-%d %H:%M:%S')
        data['dropoff_datetime'] = pd.to_datetime(data['dropoff_datetime'], format='%Y-%m-%d %H:%M:%S')
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)
        mask = (data['pickup_datetime'] >= start_date) & (data['pickup_datetime'] < end_date)
        week = pd.DataFrame()
        week = data[mask]
        week = week.sort_values('pickup_datetime')
        week.reset_index(drop=True, inplace=True)
        week.to_csv(dataRoot_week)
        data = week
        return data

    def drop_overhead(self,data,list_drop):
        for x in list_drop:
            data = data.drop(str(x), axis=1)
        return data

    def drop_anomaly(self , data):
        lower_bound = 0.5
        upper_bound = 2.5
        data['avg_amount_per_minute'] = (data.fare_amount - 2.5) / (data.trip_time / np.timedelta64(1, 'm'))
        data = data.replace(np.float64(0), np.nan)

        anomaly = data.loc[(data['dropoff_longitude'].isnull()) | (data['dropoff_latitude'].isnull()) | (data['pickup_longitude'].isnull()) | (data['pickup_latitude'].isnull()) | (data['trip_time'].isnull()) | (data['trip_distance'].isnull())]
        anomaly = anomaly.append(data.loc[(data['avg_amount_per_minute'] > upper_bound) | (data['avg_amount_per_minute'] < lower_bound)])
        data = data.drop(anomaly.index)
        return data

    def bounding_box(self , data):
        #Gesamt-Rahmen in dem die Application stattfinden soll ( Breitengrad / Längengrad lat/long )
        #Zeile 57  Parameter: upperleft , lower_right Koordinaten
        jfk_geodata = (40.641547, -73.778118) #lowerright (lat/long)
        ridgefield_geodata = (40.856406, -74.020642) #upperleft (lat/long)
        data = data.loc[(data['dropoff_latitude'] > jfk_geodata[0]) &
                               (data['dropoff_longitude'] < jfk_geodata[1]) &
                               (data['dropoff_latitude'] < ridgefield_geodata[0]) &
                               (data['dropoff_longitude'] > ridgefield_geodata[1]) &
                               (data['pickup_latitude'] > jfk_geodata[0]) &
                               (data['pickup_longitude'] < jfk_geodata[1]) &
                               (data['pickup_latitude'] < ridgefield_geodata[0]) &
                               (data['pickup_longitude'] > ridgefield_geodata[1])
                               ]
        return data


    def train_decision_tree(self, time_regression_df, test_size, random_state, max_depth, export_testset):

        y = time_regression_df["trip_time_in_mins"]
        X = time_regression_df.ix[:, 0:6]
        X_train, X_test, y_train, y_test = cv.train_test_split(X, y, test_size=test_size, random_state=random_state)

        if bool(export_testset) is True:
            Xy_test = pd.concat([X_test, y_test], axis=1)
            Xy_test.to_csv('taxi_tree_test_Xy_20130506-12.csv')

        t = time.time()

        regtree = DecisionTreeRegressor(min_samples_split=3, random_state=random_state, max_depth=max_depth)
        regtree.fit(X_train, y_train)

        return regtree

    def export_meta_data(self, tree_model , training_duration ):
        # Export Meta-File
        elapsed = time.time() - t

    def train_random_forest(self, time_regression_df, test_size, random_state, max_depth, export_testset):
        y = time_regression_df["trip_time_in_mins"]
        X = time_regression_df.ix[:, 0:6]
        X_train, X_test, y_train, y_test = cv.train_test_split(X, y, test_size=test_size, random_state=random_state)

        if bool(export_testset) is True:
            Xy_test = pd.concat([X_test, y_test], axis=1)
            Xy_test.to_csv('taxi_forest_test_Xy_20130506-12.csv')

        rd_regtree = RandomForestRegressor(n_estimators=20, n_jobs=6, min_samples_split=3, random_state=random_state, max_depth=max_depth)
        rd_regtree.fit(X_train, y_train)

        return rd_regtree

def create_tree_dataframe(self, data):
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

    def dump_tree(self, decision_model , dataRoot_tree_model):
        joblib.dump(decision_model , str(dataRoot_tree_model), protocol=2)

