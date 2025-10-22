#!/usr/bin/env python3
"""
Comprehensive Route Calculator with Dijkstra's Algorithm
Handles large road networks and provides detailed route analysis
"""

import pandas as pd
import numpy as np
import heapq
import json
from typing import List, Tuple, Dict, Optional
import matplotlib.pyplot as plt
import networkx as nx
from pathlib import Path
import random

class ComprehensiveFloodRiskRouter:
    def __init__(self, segments_file="segments_safe_min.csv", graph_file="segments_graph.csv"):
        """
        Initialize the comprehensive flood risk router
        """
        self.segments_file = segments_file
        # Use full graph for better connectivity, but we'll need to map indices to actual IDs
        full_graph_path = Path("segments_graph_full.csv")
        self.graph_file = str(full_graph_path) if full_graph_path.exists() else graph_file
        self.safety_data = None
        self.graph_data = None
        self.graph = None
        self.safety_weights = None
        self.connected_components = None
        self.largest_component = None
        self.segment_id_map = {}  # Map graph indices to actual segment IDs
        
    def load_data(self):
        """Load safety predictions and graph structure data"""
        print("=" * 60)
        print("LOADING ROUTING DATA")
        print("=" * 60)
        
        # Load safety predictions
        self.safety_data = pd.read_csv(self.segments_file)
        print(f"Loaded safety data: {len(self.safety_data)} segments")
        
        # Load graph structure
        self.graph_data = pd.read_csv(self.graph_file)
        print(f"Loaded graph data: {len(self.graph_data)} edges")
        
        # Create mapping from graph indices to actual segment IDs
        # If using segments_graph_full.csv, road_segment_id is just the row index
        # We need to map it to the actual HubName from safety_data
        if 'segments_graph_full' in self.graph_file:
            # Create mapping: index -> actual HubName
            # Convert to int first to avoid decimal point in string conversion
            for idx, row in self.safety_data.iterrows():
                self.segment_id_map[str(idx)] = str(int(row['HubName']))
            print(f"Created segment ID mapping for {len(self.segment_id_map)} segments")
        
        # Create safety weights mapping
        self.safety_weights = dict(zip(
            self.safety_data['HubName'].astype(str), 
            self.safety_data['pred_prob_safe']
        ))
        
        print(f"Created safety weights for {len(self.safety_weights)} segments")
        
        return self.safety_data, self.graph_data
    
    def analyze_network_structure(self):
        """Analyze the road network structure and connectivity"""
        print("\n" + "=" * 60)
        print("ANALYZING NETWORK STRUCTURE")
        print("=" * 60)
        
        # Create basic graph for analysis
        G = nx.Graph()
        
        for _, row in self.graph_data.iterrows():
            from_node = row['from']
            to_node = row['to']
            G.add_edge(from_node, to_node)
        
        # Find connected components
        self.connected_components = list(nx.connected_components(G))
        
        print(f"Number of connected components: {len(self.connected_components)}")
        
        # Analyze component sizes
        component_sizes = [len(comp) for comp in self.connected_components]
        component_sizes.sort(reverse=True)
        
        print(f"Component size distribution:")
        print(f"  Largest: {component_sizes[0] if component_sizes else 0}")
        print(f"  Top 5: {component_sizes[:5]}")
        print(f"  Components with 1 node: {sum(1 for size in component_sizes if size == 1)}")
        print(f"  Components with 2+ nodes: {sum(1 for size in component_sizes if size >= 2)}")
        
        # Find largest component
        if self.connected_components:
            self.largest_component = max(self.connected_components, key=len)
            print(f"Largest component: {len(self.largest_component)} nodes")
            
            # Sample nodes from largest component
            sample_nodes = list(self.largest_component)[:10]
            print(f"Sample nodes: {sample_nodes[:3]}...")
        
        return self.connected_components
    
    def create_enhanced_graph(self, cost_function='combined', min_component_size=2):
        """
        Create an enhanced graph with better connectivity
        """
        print(f"\nCreating enhanced graph with cost function: {cost_function}")
        
        # Initialize NetworkX graph
        self.graph = nx.Graph()
        
        # Filter components by minimum size
        valid_components = [comp for comp in self.connected_components if len(comp) >= min_component_size]
        
        if not valid_components:
            print("No components meet minimum size requirement")
            return self.graph
        
        # Use largest valid component
        largest_valid = max(valid_components, key=len)
        print(f"Using component with {len(largest_valid)} nodes")
        
        # Add edges with weights
        edges_added = 0
        for _, row in self.graph_data.iterrows():
            segment_id = str(row['road_segment_id'])
            from_node = row['from']
            to_node = row['to']
            distance = row['cost']
            
            # Skip if edge not in selected component
            if from_node not in largest_valid or to_node not in largest_valid:
                continue
            
            # Calculate edge weight based on cost function
            if cost_function == 'distance':
                weight = distance
            elif cost_function == 'safety':
                # Invert safety probability (higher safety = lower cost)
                safety_prob = self.safety_weights.get(segment_id, 0.5)
                weight = (1.0 - safety_prob) * 1000
            elif cost_function == 'combined':
                # Combine distance and safety
                safety_prob = self.safety_weights.get(segment_id, 0.5)
                safety_cost = (1.0 - safety_prob) * 1000
                weight = distance + safety_cost
            elif cost_function == 'flood_risk':
                # Use flood risk as primary cost
                safety_prob = self.safety_weights.get(segment_id, 0.5)
                flood_risk = 1.0 - safety_prob
                weight = flood_risk * 10000 + distance * 0.1
            else:
                weight = distance
            
            # Add edge to graph
            self.graph.add_edge(from_node, to_node, 
                              weight=weight, 
                              segment_id=segment_id,
                              distance=distance,
                              safety_prob=self.safety_weights.get(segment_id, 0.5))
            edges_added += 1
        
        print(f"Created graph with {self.graph.number_of_nodes()} nodes and {edges_added} edges")
        
        # Calculate graph metrics
        if self.graph.number_of_nodes() > 0:
            density = nx.density(self.graph)
            print(f"Graph density: {density:.4f}")
            
            # Check if graph is connected
            is_connected = nx.is_connected(self.graph)
            print(f"Graph is connected: {is_connected}")
        
        return self.graph
    
    def find_closest_nodes(self, target_coords: str, num_candidates: int = 10) -> List[Tuple[str, float]]:
        """Find the closest nodes to given coordinates"""
        target_x, target_y = map(float, target_coords.split(','))
        
        distances = []
        for node in self.graph.nodes():
            node_x, node_y = map(float, node.split(','))
            dist = np.sqrt((target_x - node_x)**2 + (target_y - node_y)**2)
            distances.append((node, dist))
        
        # Sort by distance and return closest nodes
        distances.sort(key=lambda x: x[1])
        return distances[:num_candidates]
    
    def dijkstra_shortest_path(self, start: str, end: str) -> Tuple[List[str], float, Dict]:
        """
        Find shortest path using Dijkstra's algorithm with enhanced error handling
        """
        print(f"\nFinding shortest path from {start} to {end}")
        
        if self.graph is None:
            raise ValueError("Graph not created. Call create_enhanced_graph() first.")
        
        # Check if nodes exist in graph
        if start not in self.graph:
            print(f"Start node {start} not found in graph")
            closest_start = self.find_closest_nodes(start, 1)[0]
            print(f"Using closest start node: {closest_start[0]} (distance: {closest_start[1]:.1f}m)")
            start = closest_start[0]
        
        if end not in self.graph:
            print(f"End node {end} not found in graph")
            closest_end = self.find_closest_nodes(end, 1)[0]
            print(f"Using closest end node: {closest_end[0]} (distance: {closest_end[1]:.1f}m)")
            end = closest_end[0]
        
        # Initialize distances and previous nodes
        distances = {node: float('inf') for node in self.graph.nodes()}
        previous = {node: None for node in self.graph.nodes()}
        distances[start] = 0
        
        # Priority queue: (distance, node)
        pq = [(0, start)]
        visited = set()
        nodes_explored = 0
        
        while pq:
            current_dist, current_node = heapq.heappop(pq)
            
            if current_node in visited:
                continue
                
            visited.add(current_node)
            nodes_explored += 1
            
            if current_node == end:
                break
            
            # Explore neighbors
            for neighbor in self.graph.neighbors(current_node):
                if neighbor in visited:
                    continue
                
                edge_data = self.graph[current_node][neighbor]
                edge_weight = edge_data['weight']
                new_dist = current_dist + edge_weight
                
                if new_dist < distances[neighbor]:
                    distances[neighbor] = new_dist
                    previous[neighbor] = current_node
                    heapq.heappush(pq, (new_dist, neighbor))
        
        print(f"Explored {nodes_explored} nodes")
        
        # Reconstruct path
        if distances[end] == float('inf'):
            return [], float('inf'), {}
        
        path = []
        current = end
        while current is not None:
            path.append(current)
            current = previous[current]
        path.reverse()
        
        # Get path details
        path_details = self._get_path_details(path)
        
        print(f"Found path with {len(path)} nodes, total cost: {distances[end]:.2f}")
        
        return path, distances[end], path_details
    
    def _get_path_details(self, path: List[str]) -> Dict:
        """Get detailed information about the path"""
        if len(path) < 2:
            return {'segments': [], 'total_distance': 0, 'avg_safety': 0}
        
        segments = []
        total_distance = 0
        safety_probs = []
        
        for i in range(len(path) - 1):
            current = path[i]
            next_node = path[i + 1]
            
            if self.graph.has_edge(current, next_node):
                edge_data = self.graph[current][next_node]
                # Map segment_id to actual HubName if using full graph
                segment_id = edge_data['segment_id']
                if segment_id in self.segment_id_map:
                    segment_id = self.segment_id_map[segment_id]
                
                segments.append({
                    'segment_id': segment_id,
                    'from': current,
                    'to': next_node,
                    'distance': edge_data['distance'],
                    'safety_prob': edge_data['safety_prob']
                })
                total_distance += edge_data['distance']
                safety_probs.append(edge_data['safety_prob'])
        
        return {
            'segments': segments,
            'total_distance': total_distance,
            'avg_safety': np.mean(safety_probs) if safety_probs else 0,
            'min_safety': min(safety_probs) if safety_probs else 0,
            'max_safety': max(safety_probs) if safety_probs else 0,
            'safety_std': np.std(safety_probs) if safety_probs else 0
        }
    
    def find_optimal_route(self, start: str, end: str, cost_function='combined') -> Dict:
        """
        Find optimal route considering different cost functions
        """
        print("=" * 60)
        print("FINDING OPTIMAL ROUTE")
        print("=" * 60)
        
        # Create enhanced graph with specified cost function
        self.create_enhanced_graph(cost_function)
        
        # Find shortest path
        path, total_cost, path_details = self.dijkstra_shortest_path(start, end)
        
        if not path:
            return {
                'success': False,
                'message': 'No path found between start and end points',
                'path': [],
                'total_cost': float('inf'),
                'path_details': {}
            }
        
        # Calculate route statistics
        route_stats = {
            'success': True,
            'path': path,
            'total_cost': total_cost,
            'path_details': path_details,
            'cost_function': cost_function,
            'num_segments': len(path_details['segments']),
            'total_distance': path_details['total_distance'],
            'avg_safety': path_details['avg_safety'],
            'min_safety': path_details['min_safety'],
            'max_safety': path_details['max_safety'],
            'safety_std': path_details['safety_std']
        }
        
        return route_stats
    
    def compare_routing_strategies(self, start: str, end: str) -> Dict:
        """Compare different routing strategies for the same start/end points"""
        print("\n" + "=" * 60)
        print("COMPARING ROUTING STRATEGIES")
        print("=" * 60)
        
        strategies = ['distance', 'safety', 'combined', 'flood_risk']
        results = {}
        
        for strategy in strategies:
            print(f"\nTesting {strategy} strategy...")
            try:
                route = self.find_optimal_route(start, end, strategy)
                if route['success']:
                    results[strategy] = route
                    print(f"  Distance: {route['total_distance']:.2f}m")
                    print(f"  Avg Safety: {route['avg_safety']:.3f}")
                    print(f"  Segments: {route['num_segments']}")
                    print(f"  Safety Std: {route['safety_std']:.3f}")
                else:
                    print(f"  Failed: {route['message']}")
            except Exception as e:
                print(f"  Error: {e}")
        
        return results
    
    def generate_sample_routes(self, num_routes: int = 5) -> List[Dict]:
        """Generate sample routes for demonstration"""
        print(f"\n" + "=" * 60)
        print(f"GENERATING {num_routes} SAMPLE ROUTES")
        print("=" * 60)
        
        if not self.largest_component or len(self.largest_component) < 2:
            print("Not enough nodes for sample routes")
            return []
        
        # Create graph for sampling
        self.create_enhanced_graph('combined')
        
        sample_routes = []
        nodes = list(self.graph.nodes())
        
        for i in range(num_routes):
            # Randomly select start and end points
            start, end = random.sample(nodes, 2)
            
            print(f"\nSample Route {i+1}:")
            print(f"  Start: {start}")
            print(f"  End: {end}")
            
            try:
                route = self.find_optimal_route(start, end, 'combined')
                if route['success']:
                    sample_routes.append(route)
                    print(f"  Distance: {route['total_distance']:.2f}m")
                    print(f"  Safety: {route['avg_safety']:.3f}")
                    print(f"  Segments: {route['num_segments']}")
                else:
                    print(f"  Failed: {route['message']}")
            except Exception as e:
                print(f"  Error: {e}")
        
        return sample_routes
    
    def visualize_route(self, route_stats: Dict, save_path: str = "optimal_route.png"):
        """Visualize the optimal route on a map"""
        print(f"\nVisualizing route: {save_path}")
        
        try:
            # Create a simple visualization
            fig, ax = plt.subplots(1, 1, figsize=(12, 8))
            
            # Extract coordinates
            path = route_stats['path']
            if len(path) < 2:
                print("Cannot visualize: path too short")
                return
            
            x_coords = []
            y_coords = []
            
            for node in path:
                coords = node.split(',')
                x_coords.append(float(coords[0]))
                y_coords.append(float(coords[1]))
            
            # Plot the route
            ax.plot(x_coords, y_coords, 'r-', linewidth=3, label='Optimal Route')
            ax.scatter(x_coords[0], y_coords[0], color='green', s=100, label='Start', zorder=5)
            ax.scatter(x_coords[-1], y_coords[-1], color='red', s=100, label='End', zorder=5)
            
            # Add segment safety information
            segments = route_stats['path_details']['segments']
            for i, segment in enumerate(segments):
                if i < len(x_coords) - 1:
                    mid_x = (x_coords[i] + x_coords[i+1]) / 2
                    mid_y = (y_coords[i] + y_coords[i+1]) / 2
                    safety = segment['safety_prob']
                    color = 'green' if safety > 0.7 else 'orange' if safety > 0.4 else 'red'
                    ax.scatter(mid_x, mid_y, color=color, s=20, alpha=0.7)
            
            ax.set_xlabel('X Coordinate (UTM)')
            ax.set_ylabel('Y Coordinate (UTM)')
            ax.set_title(f'Optimal Route - {route_stats["cost_function"].title()} Strategy')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Route visualization saved: {save_path}")
            
        except Exception as e:
            print(f"Error creating visualization: {e}")
    
    def export_route(self, route_stats: Dict, output_file: str = "optimal_route.json"):
        """Export route details to JSON file"""
        print(f"\nExporting route to: {output_file}")
        
        try:
            # Prepare export data
            export_data = {
                'route_info': {
                    'success': route_stats['success'],
                    'cost_function': route_stats['cost_function'],
                    'total_cost': route_stats['total_cost'],
                    'total_distance': route_stats['total_distance'],
                    'num_segments': route_stats['num_segments'],
                    'avg_safety': route_stats['avg_safety'],
                    'min_safety': route_stats['min_safety'],
                    'max_safety': route_stats['max_safety'],
                    'safety_std': route_stats.get('safety_std', 0)
                },
                'path': route_stats['path'],
                'segments': route_stats['path_details']['segments']
            }
            
            with open(output_file, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            print(f"Route exported successfully: {output_file}")
            
        except Exception as e:
            print(f"Error exporting route: {e}")

def demo_routing():
    """Demonstrate the comprehensive routing system"""
    print("=" * 80)
    print("COMPREHENSIVE FLOOD RISK ROUTING DEMONSTRATION")
    print("=" * 80)
    
    # Initialize router
    router = ComprehensiveFloodRiskRouter()
    
    # Load data
    router.load_data()
    
    # Analyze network structure
    router.analyze_network_structure()
    
    # Generate sample routes
    sample_routes = router.generate_sample_routes(3)
    
    if sample_routes:
        # Use the first successful route for detailed analysis
        best_route = sample_routes[0]
        
        print(f"\nDetailed Analysis of Best Route:")
        print(f"Strategy: {best_route['cost_function']}")
        print(f"Total distance: {best_route['total_distance']:.2f} meters")
        print(f"Average safety: {best_route['avg_safety']:.3f}")
        print(f"Safety range: {best_route['min_safety']:.3f} - {best_route['max_safety']:.3f}")
        print(f"Safety std dev: {best_route['safety_std']:.3f}")
        print(f"Number of segments: {best_route['num_segments']}")
        
        # Visualize route
        router.visualize_route(best_route, "comprehensive_route.png")
        
        # Export route
        router.export_route(best_route, "comprehensive_route.json")
        
        # Compare strategies for the same route
        if len(best_route['path']) >= 2:
            start = best_route['path'][0]
            end = best_route['path'][-1]
            comparison = router.compare_routing_strategies(start, end)
            
            print(f"\nStrategy Comparison for Same Route:")
            for strategy, result in comparison.items():
                if result['success']:
                    print(f"{strategy:12}: {result['total_distance']:8.1f}m, safety={result['avg_safety']:.3f}")

def main():
    """Main function for command-line usage"""
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python comprehensive_route_calculator.py <start_coords> <end_coords> [cost_function]")
        print("Example: python comprehensive_route_calculator.py '287086.577,1617689.878' '290215.438,1634156.957' combined")
        print("\nRunning demo instead...")
        demo_routing()
        return
    
    start = sys.argv[1]
    end = sys.argv[2]
    cost_function = sys.argv[3] if len(sys.argv) > 3 else 'combined'
    
    # Initialize router
    router = ComprehensiveFloodRiskRouter()
    router.load_data()
    router.analyze_network_structure()
    
    # Find route
    route = router.find_optimal_route(start, end, cost_function)
    
    if route['success']:
        print(f"\nOptimal Route Found!")
        print(f"Strategy: {route['cost_function']}")
        print(f"Total distance: {route['total_distance']:.2f} meters")
        print(f"Average safety: {route['avg_safety']:.3f}")
        print(f"Number of segments: {route['num_segments']}")
        
        # Export route
        router.export_route(route)
        
        # Visualize route
        router.visualize_route(route)
    else:
        print(f"Route not found: {route['message']}")

if __name__ == "__main__":
    main()
