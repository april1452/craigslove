import os
import sys
import csv
import json
import re
import nltk
import time
import argparse
import pandas as pd
import numpy as np

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
from sklearn.externals import joblib
from nltk.stem.snowball import SnowballStemmer

reload(sys)
sys.setdefaultencoding("utf-8")
"""
first create data using format_data.py

cluster.py will output clusters in json format to the cluster_data/ directory
"""


# reference: http://brandonrose.org/clustering

# which words are not interesting?
stopwords = ['guy', 'guys', 'girl', 'girls', 'woman', 'women', 'man', 'men', 'pics', 'pic', 'send', 'reply', 'good', 'age']

stemmer = SnowballStemmer("english")

post_counts_city = {}
post_counts_city['chicago'] = 29665
post_counts_city['dallas'] = 51885
post_counts_city['denver'] = 36578
post_counts_city['jacksonville'] = 8978
post_counts_city['lasvegas'] = 18689
post_counts_city['losangeles'] = 35159
post_counts_city['miami'] = 37135
post_counts_city['minneapolis'] = 22753
post_counts_city['newyork'] = 81261
post_counts_city['oklahomacity'] = 6738
post_counts_city['providence'] = 8099
post_counts_city['seattle'] = 32058
post_counts_city['sfbay'] = 61415
post_counts_city['washingtondc'] = 46388

post_counts_type = {}

def cluster(data_file, num_clusters):
	# read posts from file
	texts = []
	cities = []
	categories = []
	category_types = []
	types = []
	with open(data_file, 'r') as f:
		csv_reader = csv.reader(f)
		for line in csv_reader:
			# line format [text, city, category, posttype]
			texts.append(line[0].decode('utf8'))
			cities.append(line[1])
			categories.append(line[2])
			types.append(line[3])
			category_types.append(line[2] + ' - ' + line[3])
	print 'read ' + str(len(texts)) + ' posts'

	#define vectorizer parameters
	t1 = time.clock()
	tfidf_vectorizer = TfidfVectorizer(max_df=0.8, max_features=200000,
									 min_df=0.1, #stop_words=stopwords,
									 use_idf=True, tokenizer=tokenize, ngram_range=(1,3))

	tfidf_matrix = tfidf_vectorizer.fit_transform(texts) #fit the vectorizer to texts
	t2 = time.clock()
	print("TfidfVectorizer fit_transform: {} seconds.\n".format(t2 - t1))
	print tfidf_matrix.shape

	terms = tfidf_vectorizer.get_feature_names() #a list of the features used in the tf-idf matrix
	
	print terms

	dist = 1 - cosine_similarity(tfidf_matrix) #TODO look at this
	print dist

	t3 = time.clock()
	km = KMeans(n_clusters=num_clusters)
	km.fit(tfidf_matrix)
	t4 = time.clock()
	print("KMeans fit: {} seconds.\n".format(t4 - t3))

	joblib.dump(km, 'doc_cluster.pkl')

	# save the km clusters so we dont recompute every time
	"""
	km = joblib.load('doc_cluster.pkl')
	"""
	clusters = km.labels_.tolist()


	posts = {'category': categories, 'type': types, 'category_type' : category_types, 'city': cities, 'text': texts, 'cluster': clusters }

	frame = pd.DataFrame(posts, index = [clusters] , columns = ['cluster', 'category', 'type', 'category_type', 'city', 'text'])

	order_centroids = km.cluster_centers_.argsort()[:, ::-1]


	# convert clusters to json objects

	clusters_as_json = {}

	NUM_TOP_TERMS = 20
	NUM_TOP_FIELDS = 8

	for i in range(num_clusters):
		cluster_json = {}

		# top terms
		cluster_json['terms'] = [ terms[j] for j in order_centroids[i, :NUM_TOP_TERMS]]
		
		# top types (ie m4m, m4w)
		cluster_types = frame.ix[i]['type'].values.tolist()
		#print cluster_types
		# NORMALIZE
		normalized_typecounts = []
		for t,count in pd.value_counts(cluster_types).iteritems():
			normalized_typecounts.append((t, count/float(post_counts_type[t])))
		cluster_json['types'] = sorted(normalized_typecounts, key=lambda tup: tup[1], reverse=True)[:NUM_TOP_FIELDS]
		#[x for x in pd.value_counts(cluster_types)[:NUM_TOP_FIELDS].iteritems()]

		# tope category-types
		cluster_category_types = frame.ix[i]['category_type'].values.tolist()
		cluster_json['category_type'] = [x for x in pd.value_counts(cluster_category_types)[:NUM_TOP_FIELDS].iteritems()]


		# top categories (msr or stp)
		cluster_categories = frame.ix[i]['category'].values.tolist()
		cluster_json['categories'] = [x for x in pd.value_counts(cluster_categories)[:NUM_TOP_FIELDS].iteritems()]

		# top cities
		cluster_cities = frame.ix[i]['city'].values.tolist()
		# NORMALIZE
		normalized_cities = []
		for t,count in pd.value_counts(cluster_cities).iteritems():
			normalized_cities.append((t, count/float(post_counts_city[t])))
		cluster_json['cities'] = sorted(normalized_cities, key=lambda tup: tup[1], reverse=True)[:NUM_TOP_FIELDS]

		#cluster_json['cities'] = [x for x in pd.value_counts(cluster_cities)[:NUM_TOP_FIELDS].iteritems()]

		clusters_as_json[str(i+1)] = cluster_json

	return clusters_as_json

def tokenize(text):
	# first tokenize by sentence, then by word
	tokens = [word.lower() for sent in nltk.sent_tokenize(text) for word in nltk.word_tokenize(sent)]
	filtered_tokens = []
	# filter out any tokens not containing letters (raw punctuation)
	for token in tokens:
		if re.search('[a-zA-Z0-9]', token):
			if token not in stopwords:
				filtered_tokens.append(stemmer.stem(token))
	return filtered_tokens

def get_cluster_filename_from_csv(csv_file_name):
	return 'cluster_data/' + csv_file_name.split('/')[-1:][0][:-4] + '_clusters.json'

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('-path', required=True, help='either a csv file OR a directory containing csv files')
	parser.add_argument('-c', required=True, help='number of clusters')
	opts = parser.parse_args()

	num_clusters = int(opts.c)

	# add english language stopwords from file
	with open('stopwords.txt') as f:
		stopwords.extend(f.read().splitlines())

	with open('post_count_by_type.csv', 'r') as in_file:
		reader = csv.reader(in_file)
		for row in reader:
			post_counts_type[row[0]] = row[1]


	# process entire directory of csv files
	if os.path.isdir(opts.path):
		for f in os.listdir(opts.path):
			if f.endswith('.csv'): 
				file_path = os.path.join(opts.path, f)
				clusters_obj = cluster(file_path, num_clusters)
				print 'Saving clusters from ' + file_path
				with open(get_cluster_filename_from_csv(file_path), 'w') as outfile:
					json.dump(clusters_obj, outfile)

	# process only one csv file
	elif os.path.isfile(opts.path) and opts.path.endswith('.csv'):
		clusters_obj = cluster(opts.path, num_clusters)
		with open(get_cluster_filename_from_csv(opts.path), 'w') as outfile:
			json.dump(clusters_obj, outfile)


	else:
		print 'error in ' + opts.path

if __name__ == '__main__':
	main()
