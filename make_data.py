import pandas as pd
import networkx
import numpy as np


# read resident
people_df = pd.read_csv('https://raw.githubusercontent.com/myhjiang/Q5M2_dash_play/master/data/active_people.csv')

# read edge and build network
edge_df = pd.read_csv('https://raw.githubusercontent.com/myhjiang/Q5M2_dash_play/master/data/edges.csv', delimiter="\t", header=None)
edge_df.columns = ['user', 'friend']
G = nx.from_pandas_dataframe(edge_df, 'user', 'friend')
print('Graph made')

# centroid_df = pd.read_csv('https://raw.githubusercontent.com/myhjiang/Q5M2_dash_play/master/data/edges.csv', encoding='latin1')  # for later use (rotate on selection)


def make_data():
    country_df = people_df.groupby(['country']).count().reset_index()
    country_df.columns = ['country', 'user_count']

    userset = set(people_df.userid.tolist())
    flow_df = people_df.drop_duplicates(subset='userid')  # just in case, not needed actually
    user_country_dict = pd.Series(flow_df.country.values, index=flow_df.userid).to_dict()

    def make_friend_list(user):
        friends = set(G.neighbors(user))
        present_friends = list(friends.intersection(userset))
        return present_friends

    flow_df['friend_id'] = flow_df.userid.apply(make_friend_list)
    flow_df = pd.DataFrame({'userid': np.repeat(flow_df.userid.values, flow_df.friend_id.str.len()),
                            'country': np.repeat(flow_df.country.values, flow_df.friend_id.str.len()),
                            'friend_id': np.concatenate(flow_df.friend_id.values).astype(
                                int)})  # explode the list to multiple rows
    flow_df['country_dest'] = flow_df['friend_id'].map(user_country_dict)

    # aggregate edge count to country
    flow_df.drop(columns=['friend_id'], inplace=True)
    flow_country = flow_df.groupby(['country', 'country_dest']).count().reset_index()
    flow_country.columns = ['country_from', 'country_to', 'edge_count']
    # drop edges pointing to self and zip origin and destination
    flow_country = flow_country[flow_country['country_from'] != flow_country['country_to']]
    flow_country['zipped'] = tuple(zip(flow_country['country_from'], flow_country['country_to']))

    return country_df, flow_country

country_df, flow_df = make_data()
