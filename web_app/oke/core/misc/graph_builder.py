from more_itertools import unique_everseen

import re
import networkx as nx



def get_betweenness_centrality(edge_list):
	# Betweenness centrality quantifies the number of times a node acts as a bridge along the shortest path between two other nodes.
	di_graph = nx.DiGraph()
	di_graph.add_edges_from(map(lambda x: (x[0],x[-1]), edge_list))
	return nx.betweenness_centrality(di_graph)

def get_concept_description_dict(graph, label_predicate, valid_concept_filter_fn=None):
	if valid_concept_filter_fn:
		concept_set = get_concept_set(filter(valid_concept_filter_fn, graph))
		graph = filter(lambda x: x[0] in concept_set, graph)
	# print('Unique concepts:', len(concept_set))
	uri_dict = {} # concept_description_dict
	for uri,_,label in filter(lambda x: x[1] == label_predicate, graph):
		if uri not in uri_dict:
			uri_dict[uri] = []
		uri_dict[uri].append(label)
	return uri_dict

def get_tuple_element_set(tuple_list, element_idx):
	tuple_element_set = set()
	element_iter = map(lambda x: x[element_idx], tuple_list)
	for element in element_iter:
		if isinstance(element, (list,tuple)):
			for e in element:
				tuple_element_set.add(e)
		else:
			tuple_element_set.add(element)
	return tuple_element_set

def get_subject_set(edge_list):
	return get_tuple_element_set(edge_list, 0)

def get_predicate_set(edge_list):
	return get_tuple_element_set(edge_list, 1)

def get_object_set(edge_list):
	return get_tuple_element_set(edge_list, -1)

def get_concept_set(edge_list):
	edge_list = list(edge_list)
	return get_subject_set(edge_list).union(get_object_set(edge_list))

def get_root_set(edge_list):
	edge_list = list(edge_list)
	return get_subject_set(edge_list).difference(get_object_set(edge_list))

def get_leaf_set(edge_list):
	edge_list = list(edge_list)
	return get_object_set(edge_list).difference(get_subject_set(edge_list))

def reverse_order(edge_list):
	return map(lambda edge: (edge[-1],edge[-2],edge[-3]), edge_list)

def get_ancestors(node, edge_list):
	return get_object_set(filter_graph_by_root_set(list(reverse_order(edge_list)), [node]))

def tuplefy(edge_list):
	def to_tuple(x):
		if type(x) is dict:
			return tuple(x.values())
		if type(x) is list:
			return tuple(x)
		return x
	return [
		tuple(map(to_tuple, edge))
		for edge in edge_list
	]

def build_edge_dict(edge_list, key_fn=lambda x: x):
	edge_dict = {}
	for edge in edge_list:
		for subj in get_subject_set([edge]):
			subj_key = key_fn(subj)
			if subj_key not in edge_dict:
				edge_dict[subj_key] = []
			edge_dict[subj_key].append(edge)
	return edge_dict

def extract_rooted_edge_list(root, edge_dict):
	valid_edge_list = []
	if root not in edge_dict:
		return valid_edge_list
	valid_edge_list += edge_dict[root]
	obj_to_explore = get_object_set(edge_dict[root])
	del edge_dict[root]
	while len(obj_to_explore) > 0:
		obj = obj_to_explore.pop()
		if obj in edge_dict:
			valid_edge_list += edge_dict[obj]
			obj_to_explore |= get_object_set(edge_dict[obj])
			del edge_dict[obj]
	valid_edge_list = list(unique_everseen(valid_edge_list))
	return valid_edge_list

def filter_graph_by_root_set(edge_list, root_set):
	edge_dict = build_edge_dict(edge_list)
	rooted_edge_list_iter = (extract_rooted_edge_list(root, edge_dict) for root in root_set)
	rooted_edge_list = sum(rooted_edge_list_iter, [])
	return rooted_edge_list

def remove_leaves(edge_list, edge_to_remove_fn=lambda x:x):
	edge_list = list(edge_list)
	leaf_to_exclude_set = get_leaf_set(edge_list).intersection(get_object_set(filter(edge_to_remove_fn, edge_list)))
	edge_to_exclude_iter = filter(lambda x: len(get_object_set([x]).intersection(leaf_to_exclude_set))==0, edge_list)
	return list(edge_to_exclude_iter)

def get_connected_graph_list(edge_list):
	edge_list = list(edge_list)
	edge_dict = build_edge_dict(edge_list)
	graph_list = [
		extract_rooted_edge_list(root, edge_dict)
		for root in get_subject_set(edge_list)
	]
	graph_list.sort(key=lambda x: len(x), reverse=True)

	for i,graph in enumerate(graph_list):
		if len(graph)==0:
			continue
		graph_concept_set = get_concept_set(graph)
		for j,other_graph in enumerate(graph_list):
			if i==j:
				continue
			if len(other_graph)==0:
				continue
			other_graph_concept_set = get_concept_set(other_graph)
			if len(graph_concept_set.intersection(other_graph_concept_set)) > 0:
				graph.extend(other_graph)
				graph_concept_set |= other_graph_concept_set
				other_graph.clear()
	graph_list = [
		list(unique_everseen(graph))
		for graph in filter(lambda x: len(x)>0, graph_list)
	]
	return graph_list

def get_biggest_connected_graph(edge_list):
	return max(get_connected_graph_list(edge_list), key=lambda x: len(x))



MAX_LABEL_LENGTH = 128

