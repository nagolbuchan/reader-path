import { useEffect, useState, useRef, useCallback } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { useQuery } from '@tanstack/react-query';
import { graphApi } from './lib/api';
import { api } from './lib/api'; // TODO
import { error } from 'three/src/Three.WebGPU.Nodes.js';

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
  const { data, isPending, error } = useQuery({
    queryKey: ['userGraph'],
    queryFn: () => {
      console.log('TESTING API CALL...');
      return graphApi.getUserGraph();
    },
    staleTime: 1000 * 60 * 5, // Cache data for 5 minutes
  });
  console.log('useQuery result:', { data, isPending });
  //When data is loaded, set it to state.
  useEffect(() => {
    console.log('useEffect triggered with data:', data);
    console.log('Graph data fetched:', data);
    if (data) {
      //Satisfy the shape of the data defined in the GraphData interface. 
      //TODO: Confirm the actual shape of the data returned by the API.
      setGraphData({
        nodes: data.nodes || [],
        links: data.relationships?.map((rel: any) => ({
          source: rel.startNodeId,
          target: rel.endNodeId,
          type: rel.type
        })) || []
      })
    }
  }, [data]);

  //How do you handle different node type click actions? 
  //Is this a situation for an event emitter or a context menu?

  const handleNodeClick = useCallback((node: GraphNode) => {
    setSelectedNode(node);

    if (graphRef.current) {
      //TODO: Coordinates are not part of the GraphNode interface.  How do you ge them?  
      //Does the graph library provide them on click, or do you need to calculate them based on the node's position in the graph?
      // graphRef.current.centerAt(node.x, node.y, 1000);
      // graphRef.current.zoom(4, 1000);
    }

  }, [])

  //This is just a starting point. 
  const getNodeColor = (node: GraphNode) => {
    switch (node.type) {
      case 'Topic': return 'lightblue';
      case 'Course': return 'lightgreen';
      case 'Module': return 'lightcoral';
      case 'Book': return 'lightgoldenrodyellow';
      case 'Author': return 'lightpink';
      default: return 'gray';
    }
  }
  // const renderTooltip = (node: GraphNode) => {
  //   return (
  //     <div style={{ padding: '5px', backgroundColor: 'rgba(0, 0, 0, 0.7)', color: '#fff', borderRadius: '5px' }}>
  //       <strong>{node.label}</strong><br />
  //       Type: {node.type}<br />
  //       {/* Render additional properties if available */}
  //       {node.properties && Object.entries(node.properties).map(([key, value]) => (
  //         <div key={key}>{key}: {value}</div>
  //       ))}
  //     </div>
  //   );
  // }

  if (isPending) {
    return <div className="flex h-screen items-center justify-center">Loading your learning graph...</div>;
  }

  if (error) {
    return <div>Error: {error.message}</div>;
  }

  return (
    <div className="flex h-screen flex-col">

      {/* TODO: add header */}

      <div className="flex-1 relative">
        <ForceGraph2D 
          ref={graphRef}
          graphData={graphData}
          nodeLabel="label"
          nodeColor={getNodeColor}
          nodeRelSize={6}           // Base node size
          nodeVal={(node) => (node.type === 'Book' ? 1.5 : 1)} // Bigger books
          linkWidth={1.5}
          linkDirectionalArrowLength={3}
          linkDirectionalArrowRelPos={1}
          onNodeClick={handleNodeClick}
          cooldownTicks={100}
          enableNodeDrag={true}
          backgroundColor="#0f172a"
        />
      </div>

      {/* TODO: add a sidebar or panel for displaying node details */}

      {/* TODO: add a prompt box and elements for toggling the box, such as an Add Course button */}

    </div>
  )
  
}