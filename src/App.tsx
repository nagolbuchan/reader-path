import { useEffect, useState, useRef, useCallback } from 'react';
import { ForceGraph2D } from 'react-force-graph';
import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api'; // Your API client

interface GraphNode {
  id: string;
  label: string;
  type: 'Topic' | 'Course' | 'Module' | 'Book' | 'Author'; //Add worldview nodes, too.  
  val?: number; // Optional value for node size -- but based on what, though?
  color?: string; // Optional color for node
  properties?: Record<string, any>; // Additional properties for tooltip
}

interface GraphLink {
  source: string;
  target: string;
  type: string;
}

interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}

//You'll need to confirm what the shape of the data returned by the API actually is. 
//Then add it as the return type of you useQuery hook. useQuery<UserGraphResponse>(...) for example.
interface UserGraphResponse {
  graph: GraphData;
}

export default function App() {
  //First, set state variables for graph data and selected node.
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], links: [] });
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const graphRef = useRef<any>(null);

  //Next, need data.  Fetch the user's graph data.  
  const { data, isLoading, error } = useQuery<UserGraphResponse>(
    queryKey: ['userGraph'],
    queryFn: async () => {
      const response = await api.get('/user-graph'); //Adjust endpoint
      return response.data;
    }
}