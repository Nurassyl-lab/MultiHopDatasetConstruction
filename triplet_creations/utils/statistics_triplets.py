# -*- coding: utf-8 -*-
"""
Created on Mon Oct 14 20:18:05 2024

@author: Eduin Hernandez

Summary:
The `TripletsStats` module provides a comprehensive toolkit for analyzing triplet data in knowledge graphs. It defines the `TripletsStats` class, which is used to load, process, and visualize various aspects of knowledge graphs, specifically focusing on nodes (entities) and relationships (edges). 

Key functionalities:
- **Loading Data**: Load entity, relationship, and triplet data from various sources.
- **Getters**: Retrieve loaded data, including triplets, nodes, and relationships.
- **Statistics Calculation**: Calculate key graph metrics like degree distribution, clustering coefficients, graph density, and eigenvector centrality.
- **Graph Analysis**: Identify isolated nodes, calculate the frequency of relationships, and explore relationship diversity.
- **Plotting**: Visualize relationship frequencies, node diversity, eigenvector centrality, and other graph properties using bar plots.
"""

import pandas as pd
import matplotlib.pyplot as plt

from tqdm import tqdm

import networkx as nx

from utils.basic import load_pandas, load_to_set, load_triplets

class TripletsStats():
    """
    A class for loading and analyzing triplet data, including entities (nodes) and relationships (edges),
    along with various statistics and visualizations.
    """
    #--------------------------------------------------------------------------
    'Loading and Getters'
    
    def __init__(self, 
                 entity_list_path:str,
                 entity_data_path: str, 
                 relationship_data_path: str,
                 triplets_data_path: str) -> None:
        """
        Initialize the class by loading triplet, entity, and relationship data.
        
        Args:
            entity_list_path (str): Path to the entity list file.
            entity_data_path (str): Path to the entity data file.
            relationship_data_path (str): Path to the relationship data file.
            triplets_data_path (str): Path to the triplet data file.
        """
        plt.close('all')
        
        self._triplets = load_triplets(triplets_data_path)
        if entity_list_path:
            self._nodes = load_to_set(entity_list_path)
            self._node_data = load_pandas(entity_data_path)
        else:
            self._nodes = set(self._triplets['head']) | set(self._triplets['tail'])
            self._node_data = pd.DataFrame([[rdf, ''] for rdf in self._nodes], columns=['RDF', 'Title'])
        
        self._rels = set(self._triplets['relation'].tolist())
        relation_map = load_pandas(relationship_data_path)
        self._relation_data = relation_map[relation_map['Property'].isin(self._rels)]
    

    def triplets(self) -> pd.DataFrame:
        """Returns the triplets DataFrame."""
        return self._triplets
    
    def nodes(self) -> set:
        """Returns the set of nodes."""
        return self._nodes
    
    def node_data(self) -> pd.DataFrame:
        """Returns the DataFrame with node data."""
        return self._node_data
    
    def relation(self) -> set:
        """Returns the set of rels."""
        return self._rels
    
    def relation_data(self) -> pd.DataFrame:
        """Returns the DataFrame with relationship data."""
        return self._relation_data  

    #--------------------------------------------------------------------------
    'Statistics'
    def basic_stats(self, verbose: bool = True) -> tuple:
        """
        Print and return basic statistics on the triplet data, including the number of triplets, nodes, and relationship types.
        
        Args:
            verbose (bool): Whether to print the statistics. Defaults to True.
        
        Returns:
            tuple: A tuple containing the number of triplets, nodes, and relationship types.
        """
        if verbose:
            print(f'Number of Triplets:             {len(self._triplets):>15}')
            print(f'Number of Entities (Nodes):     {len(self._nodes):>15}')
            print(f'Number of Relationship Types:   {len(self._rels):>15}')
        return len(self._triplets), len(self._nodes), len(self._rels)
    
     
    def calculate_triplet_frequency(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Calculate frequency statistics for nodes and relationships in the triplet data.

        Returns:
            tuple: A tuple containing two DataFrames:
                - Node frequency statistics as heads and tails.
                - Relationship frequency statistics.
        """

        # Frequency of nodes as head
        head_freq = self._triplets['head'].value_counts().reset_index()
        head_freq.columns = ['node', 'head_count']

        # Frequency of nodes as tail
        tail_freq = self._triplets['tail'].value_counts().reset_index()
        tail_freq.columns = ['node', 'tail_count']

        # Combine head and tail frequencies
        combined_freq = pd.merge(head_freq, tail_freq, on='node', how='outer').fillna(0)
        combined_freq['total_count'] = combined_freq['head_count'] + combined_freq['tail_count']

        # Frequency of relationships
        relation_freq = self._triplets['relation'].value_counts().reset_index()
        relation_freq.columns = ['relation', 'relation_count']

        return combined_freq, relation_freq

    def count_relationships_per_node(self) -> pd.DataFrame:
        """
        Create a table that counts the number of relationships each node is involved in as either head or tail.

        Returns:
            pd.DataFrame: A pivot table with nodes as rows and relationships as columns, showing the count of each relationship type per node.
        """
    
        # Consider both head and tail roles
        head_df = self._triplets.merge(self._node_data[['RDF']], left_on='head', right_on='RDF', how='left')\
                            .merge(self._relation_data[['Property']], left_on='relation', right_on='Property', how='left')
        
        tail_df = self._triplets.merge(self._node_data[['RDF']], left_on='tail', right_on='RDF', how='left')\
                            .merge(self._relation_data[['Property']], left_on='relation', right_on='Property', how='left')
    
        # Combine the head and tail dataframes
        combined_df = pd.concat([head_df[['RDF', 'Property']], tail_df[['RDF', 'Property']]])
    
        # Group by RDF and Property and count occurrences
        counts_df = combined_df.groupby(['RDF', 'Property']).size().unstack(fill_value=0)
    
        return counts_df
    
    def calculate_node_degree(self) -> pd.DataFrame:
        """
        Calculate the degree (number of edges) for each node in the triplet data.

        Returns:
            pd.DataFrame: A DataFrame with node RDFs and their respective degree (total number of connections).
        """
        # Calculate the degree of each node as a head
        head_degree = self._triplets['head'].value_counts().reset_index()
        head_degree.columns = ['node', 'head_degree']

        # Calculate the degree of each node as a tail
        tail_degree = self._triplets['tail'].value_counts().reset_index()
        tail_degree.columns = ['node', 'tail_degree']

        # Combine the degrees for head and tail
        degree_df = pd.merge(head_degree, tail_degree, on='node', how='outer').fillna(0)
        degree_df['total_degree'] = degree_df['head_degree'] + degree_df['tail_degree']

        return degree_df
    
    def calculate_degree_distribution(self, verbose: bool = True) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Calculate the average, median, mode, maximum, and minimum degree per node in the triplet data.
    
        Args:
            verbose (bool): Whether to print detailed degree statistics. Defaults to True.
    
        Returns:
            tuple: A tuple containing the degrees for out and in degrees.
        """
        out_degree_df = self.calculate_node_degree()['head_degree']
        in_degree_df = self.calculate_node_degree()['tail_degree']

        if verbose:
            print(f'Node Degree Mean:               {out_degree_df.mean():>15.4f}')
            print(f'Node Out-Degree Median:         {out_degree_df.median():>15.0f}')
            print(f'Node Out-Degree Mode:           {out_degree_df.mode()[0]:>15.0f}')
            print(f'Node Out-Degree Max:            {out_degree_df.max():>15.0f}')
            print(f'Node Out-Degree Min:            {out_degree_df.min():>15.0f}')
            print(f'Node In-Degree Median:          {in_degree_df.median():>15.0f}')
            print(f'Node In-Degree Mode:            {in_degree_df.mode()[0]:>15.0f}')
            print(f'Node In-Degree Max:             {in_degree_df.max():>15.0f}')
            print(f'Node In-Degree Min:             {in_degree_df.min():>15.0f}')

        return out_degree_df, in_degree_df

    def calculate_graph_density(self, verbose: bool = True) -> float:
        """
        Calculate the density of the knowledge graph.
    
        Args:
            verbose (bool): Whether to print the graph density. Defaults to True.
        Returns:
            float: The density of the graph.
        """
        num_nodes = len(self._nodes)
        num_edges = len(self._triplets)
        
        # Density calculation
        density = (2 * num_edges) / (num_nodes * (num_nodes - 1))
        
        if verbose: print(f'Graph Density:                  {density:>15.3E}')
        return density

    def calculate_eigenvector_centrality(self) -> pd.DataFrame:
        """
        Calculate the eigenvector centrality for each node in the knowledge graph.
    
        Returns:
            pd.DataFrame: A DataFrame containing nodes and their eigenvector centrality scores.
        """
        # Create a graph from the triplet data
        G = nx.from_pandas_edgelist(self._triplets, 'head', 'tail')
        
        # Calculate eigenvector centrality
        eigenvector_centrality = nx.eigenvector_centrality(G, max_iter=1000)
        
        # Convert the dictionary to a pandas DataFrame
        eigenvector_df = pd.DataFrame(list(eigenvector_centrality.items()), columns=['RDF', 'eigenvector_centrality'])
        
        # Combine with node data
        combined_df = pd.merge(self._node_data, eigenvector_df, on='RDF', how='left')
        
        return combined_df

    def calculate_clustering_coefficient(self, verbose: bool) -> tuple[dict, float]:
        """
        Calculate the local and gloabl clustering coefficient for each node in the knowledge graph.
    
        Returns:
            dict: A dictionary with nodes as keys and their clustering coefficients as values.
        """
        G = nx.from_pandas_edgelist(self._triplets, 'head', 'tail')
        
        clustering_coeffs = nx.clustering(G)
        avg_clustering = nx.average_clustering(G)
        
        if verbose: print(f'Global Clustering Coefficient:  {avg_clustering:>15.3E}')
        return clustering_coeffs, avg_clustering


    def find_isolated_nodes(self, verbose = True) -> list:
        """
        Find all isolated nodes in the knowledge graph, i.e., nodes with no edges.
    
        Returns:
            list: A list of isolated nodes.
        """
        all_nodes = set(self._nodes)
        connected_nodes = set(self._triplets['head']).union(set(self._triplets['tail']))
        isolated_nodes = list(all_nodes - connected_nodes)
        
        if verbose: print(f'Number of Isolated Nodes:       {len(isolated_nodes):>15}')            
        return isolated_nodes
    
    def calculate_categories(self, verbose = True) -> tuple[set, pd.DataFrame]:
        """
        Calculate the categories for each entity in the knowledge graph and return them as a DataFrame.
        
        Args:
            verbose (bool): Whether to print the number of categories. Defaults to True.
        
        Returns:
            tuple: A set of unique categories and a DataFrame containing the category mapping for each entity.
        """
        # Filter category and subclass triplets
        category_df = self._triplets[self._triplets['relation'] == 'P31']
        subclass_df = self._triplets[self._triplets['relation'] == 'P279']
        

        # Create a set of categories from both category and subclass triplets
        categories = set(category_df['tail']) | set(subclass_df['head']) | set(subclass_df['tail'])
    
        # Create a dictionary to quickly map heads to their respective categories (tails)
        category_dict = category_df.groupby('head')['tail'].apply(list).to_dict()
    
        # Create a copy of node data and map categories using vectorized operations
        node_data_copy = pd.DataFrame(self._nodes, columns=['RDF'])
        node_data_copy['Categories'] = node_data_copy['RDF'].map(category_dict)
        node_data_copy['Categories'] = node_data_copy['Categories'].apply(lambda x: x if isinstance(x, list) else [])
    
        # Compute additional columns for category analysis
        node_data_copy['is_category'] = node_data_copy['RDF'].isin(categories)
        node_data_copy['has_category'] = node_data_copy['Categories'].apply(bool)
        node_data_copy['not_classified'] = ~node_data_copy['is_category'] & ~node_data_copy['has_category']
    
        # Prepare the result DataFrame
        category_map_df = node_data_copy[['RDF', 'Categories', 'is_category', 'has_category', 'not_classified']]
    
        # Print verbose information if requested
        if verbose:
            num_unclassified = category_map_df['not_classified'].sum()
            print(f'Number of Categories:           {len(categories):>15}')
            print(f'Number of Nodes w/o Categories: {num_unclassified:>15}')
        return categories, category_map_df

    def calculate_category_statistics(self, categories: set, category_map_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate statistics for each category in the knowledge graph based on the given categories and category map.
    
        Args:
            categories (set): A set of unique categories in the knowledge graph.
            category_map_df (pd.DataFrame): A DataFrame containing the category mapping for each entity.
    
        Returns:
            pd.DataFrame: A DataFrame containing the relation counts for each category.
        """
        # Prepare a dictionary to store relation counts for each category
        relation_list = list(self._rels)
        category_statistics = {category: [0] * len(relation_list) for category in categories}
        
        # Convert category_map_df to a dictionary for faster lookup
        category_map_dict = category_map_df.set_index('RDF').to_dict(orient='index')
    
        # Iterate through each triplet and update counts for each category
        for _, triplet in tqdm(self._triplets.iterrows(), total=len(self._triplets), desc="Processing Triplets"):
            head = triplet['head']
            relation = triplet['relation']
    
            # Only process if the head exists in the category map
            if head in category_map_dict:
                node_info = category_map_dict[head]
                if node_info['has_category'] and not node_info['is_category']:
                    relation_idx = relation_list.index(relation)
                    for category in node_info['Categories']:
                        category_statistics[category][relation_idx] += 1
    
        # Convert the category statistics dictionary to a DataFrame
        category_stats_df = pd.DataFrame.from_dict(category_statistics, orient='index', columns=relation_list)
        category_stats_df.index.name = 'Category'
        category_stats_df.columns.name = 'Relation'
    
        return category_stats_df

    def classify_relations(self, category_stats_df: pd.DataFrame, category_map_df: pd.DataFrame) -> dict:
        """
        Classify relationships for each category as either unique to the category or shared among multiple categories.
    
        Args:
            category_stats_df (pd.DataFrame): A DataFrame containing relation counts for each category.
            category_map_df (pd.DataFrame): A DataFrame containing the category mapping for each entity.
    
        Returns:
            dict: A dictionary where each category contains:
                  - 'unique_relations': A list of relations considered unique to the category.
                  - 'shared_relations': A list of relations shared with other categories.
        """
        # Initialize dictionaries to track unique and shared relations
        category_relation_classification = {}
    
        # Calculate total count of each relation across all categories
        total_relation_counts = category_stats_df.sum(axis=0)
    
        for category in category_stats_df.index:
            category_relations = category_stats_df.loc[category]
            
            # Relations that have non-zero counts for this specific category
            category_non_zero_rels = category_relations[category_relations > 0].index
    
            # Classify relations as unique or shared based on presence across other categories
            unique_relations = []
            shared_relations = []
    
            for relation in category_non_zero_rels:
                if category_stats_df[relation].sum() == category_relations[relation]:
                    unique_relations.append(relation)
                else:
                    shared_relations.append(relation)
    
            # Store classification results
            category_relation_classification[category] = {
                'unique_relations': unique_relations,
                'shared_relations': shared_relations
            }
    
        return category_relation_classification


    def convert_category_stats_to_dict(self, category_stats_df: pd.DataFrame) -> tuple[dict, dict]:
        """
        Convert the category statistics DataFrame into a dictionary where the key is the RDF and the value is a dictionary of relations with non-zero counts.
        Also create a dictionary containing the total count for each category.

        Args:
            category_stats_df (pd.DataFrame): A DataFrame containing relation counts for each category.

        Returns:
            tuple: A tuple containing two dictionaries:
                - A dictionary where keys are RDFs and values are dictionaries of relations with non-zero counts.
                - A dictionary where keys are RDFs and values are the total counts of relations.
        """
        category_stats_dict = {}
        category_total_count_dict = {}

        for category, row in category_stats_df.iterrows():
            non_zero_relations = row[row > 0].to_dict()
            if non_zero_relations:
                category_stats_dict[category] = non_zero_relations
            category_total_count_dict[category] = row.sum()
            
        return category_stats_dict, category_total_count_dict
    
    #------------------------------------------------------------------------------
    'Plotting Functions'
    def plot_relationship_statistics(self, relation_stats: pd.DataFrame, start_idx: int = None, end_idx: int = None) -> None:
        """
        Plot the frequency statistics for relationships.

        Args:
            relation_stats (pd.DataFrame): DataFrame containing relationship frequency statistics.
            start_idx (int, optional): Starting index for the relationships to display. Defaults to None.
            end_idx (int, optional): Ending index for the relationships to display. Defaults to None.
        """
    
        # Map relationship properties to their titles
        relation_stats = relation_stats.merge(self._relation_data[['Property', 'Title']], left_on='relation', right_on='Property', how='left')
        relation_stats.drop(columns=['Property'], inplace=True)
    
        # Sort by total_count in descending order
        relation_stats = relation_stats.sort_values(by='relation_count', ascending=False)
    
        # Plot for relationships with titles and flipped axes
        plt.figure(figsize=(10, 12))
        plt.barh(relation_stats['Title'][start_idx:end_idx], relation_stats['relation_count'][start_idx:end_idx], color='lightgreen')
        plt.ylabel('Relationship Title')
        plt.xlabel('Frequency')
        plt.title('Relationship Frequency')
        plt.gca().invert_yaxis()  # Invert the y-axis
        plt.tight_layout()
        plt.grid(True)
        plt.show()
    
    def plot_node_statistics(self, node_stats: pd.DataFrame, start_idx: int = None, end_idx: int = None) -> None:
        """
        Plot the frequency statistics for nodes.

        Args:
            node_stats (pd.DataFrame): DataFrame containing node frequency statistics.
            start_idx (int, optional): Starting index for the nodes to display. Defaults to None.
            end_idx (int, optional): Ending index for the nodes to display. Defaults to None.
        """
    
        # Map node RDF to their titles
        node_stats = node_stats.merge(self._node_data[['RDF', 'Title']], left_on='node', right_on='RDF', how='left')
        node_stats.drop(columns=['RDF'], inplace=True)
    
        # Sort by total_count in descending order
        node_stats = node_stats.sort_values(by='total_count', ascending=False)
    
        # Plot for nodes with titles
        plt.figure(figsize=(10, 12))
        plt.barh(node_stats['Title'][start_idx:end_idx], node_stats['total_count'][start_idx:end_idx], color='skyblue')
        plt.ylabel('Node Title')
        plt.xlabel('Frequency')
        plt.title('Node Frequency')
        plt.gca().invert_yaxis()  # Invert the y-axis
        plt.tight_layout()
        plt.grid(True)
        plt.show()
        
    def plot_node_diversity(self, mat: pd.DataFrame, start_idx: int = None, end_idx: int = None) -> None:
        """
        Plot the diversity of nodes by showing the number of distinct relationship types (edges) each node is involved in.
    
        Args:
            mat (pd.DataFrame): DataFrame where rows represent nodes and columns represent relationship properties.
            start_idx (int, optional): Starting index for nodes to display. Defaults to None.
            end_idx (int, optional): Ending index for nodes to display. Defaults to None.
        """
        unique_relationships = (mat > 0).astype(int)
        
        # Sum along the rows (columns) to get the number of distinct nodes per relationship
        distinct_rel_counts = unique_relationships.sum(axis=1)
        
        # Convert the Series to a DataFrame and reset the index to turn it into a column
        distinct_rel_counts_df = distinct_rel_counts.reset_index()
        distinct_rel_counts_df.columns = ['RDF', 'count']
        node_df = distinct_rel_counts_df.merge(self._node_data[['RDF', 'Title']], on='RDF', how='left')
        
        # Sort by total_count in descending order
        node_df = node_df.sort_values(by='count', ascending=False)
        
        # Plot for nodes with titles
        plt.figure(figsize=(10, 12))
        plt.barh(node_df['Title'][start_idx:end_idx], node_df['count'][start_idx:end_idx], color='skyblue')
        plt.ylabel('Node Title')
        plt.xlabel('Number of Edge Types')
        plt.title('Node Diversity')
        plt.gca().invert_yaxis()  # Invert the y-axis
        plt.tight_layout()
        plt.grid(True)
        plt.show()

    def plot_relationship_diversity(self, mat: pd.DataFrame, start_idx: int = None, end_idx: int = None) -> None:
        """
        Plot the diversity of relationships by showing the number of distinct nodes each relationship is connected to.
    
        Args:
            mat (pd.DataFrame): DataFrame where rows represent nodes and columns represent relationship properties.
            start_idx (int, optional): Starting index for relationships to display. Defaults to None.
            end_idx (int, optional): Ending index for relationships to display. Defaults to None.
        """
        unique_relationships = (mat > 0).astype(int)
        
        # Sum along the rows (columns) to get the number of distinct nodes per relationship
        distinct_node_counts = unique_relationships.sum(axis=0)
        
        distinct_node_count_df = distinct_node_counts.reset_index()
        distinct_node_count_df.columns = ['Property', 'count']
        rels_df = distinct_node_count_df.merge(self._relation_data[['Property', 'Title']], on='Property', how='left')
        
        # Sort by total_count in descending order
        rels_df = rels_df.sort_values(by='count', ascending=False)
        
        # Plot for nodes with titles
        plt.figure(figsize=(10, 12))
        plt.barh(rels_df['Title'][start_idx:end_idx], rels_df['count'][start_idx:end_idx], color='lightgreen')
        plt.ylabel('Relationship Title')
        plt.xlabel('Number of Node Types')
        plt.title('Relationship Diversity')
        plt.gca().invert_yaxis()  # Invert the y-axis
        plt.tight_layout()
        plt.grid(True)
        plt.show()
        
    def plot_eigenvector_centrality(self, eigenvector_stats: pd.DataFrame, start_idx: int = None, end_idx: int = None) -> None:
        """
        Plot the eigenvector centrality statistics for nodes.
    
        Args:
            eigenvector_stats (pd.DataFrame): DataFrame containing nodes and their eigenvector centrality scores.
            start_idx (int, optional): Starting index for the nodes to display. Defaults to None.
            end_idx (int, optional): Ending index for the nodes to display. Defaults to None.
        """
        # # Map node RDF to their titles
        # eigenvector_stats = eigenvector_stats.merge(self._node_data[['RDF', 'Title']], left_on='RDF', right_on='RDF', how='left')
        # eigenvector_stats.drop(columns=['RDF'], inplace=True)
        
        # Sort by eigenvector_centrality in descending order
        eigenvector_stats = eigenvector_stats.sort_values(by='eigenvector_centrality', ascending=False)
        
        # Plot for nodes with titles
        plt.figure(figsize=(10, 12))
        plt.barh(eigenvector_stats['Title'][start_idx:end_idx], eigenvector_stats['eigenvector_centrality'][start_idx:end_idx], color='lightcoral')
        plt.ylabel('Node Title')
        plt.xlabel('Eigenvector Centrality')
        plt.title('Eigenvector Centrality of Nodes')
        plt.gca().invert_yaxis()  # Invert the y-axis
        plt.tight_layout()
        plt.grid(True)
        plt.show()