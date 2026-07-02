import { useEffect, useState, useRef, useCallback, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { graphApi } from './lib/api';
import HomeGraph from './components/HomeGraph';
// import { api } from './lib/api'; // TODO
// import { error } from 'three/src/Three.WebGPU.Nodes.js';

export default function App() {
  const [rawData, setRawData] = useState<any>(null); // Raw data from API
  // const [graphData, setGraphData] = useState<GraphData>({ nodes: [], links: [] });
  // const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  // const graphRef = useRef<any>(null);

  const { data, isPending, error } = useQuery({
    queryKey: ['userGraph'],
    queryFn: () => {
      return graphApi.getUserGraph();
    },
    staleTime: 1000 * 60 * 5, // Cache data for 5 minutes
  });
  console.log('useQuery result:', { data, isPending });

  useEffect(() => {
    if (data) {
      //Satisfy the shape of the data defined in the GraphData interface. 
      //TODO: Confirm the actual shape of the data returned by the API.
      setRawData(data);
    }
  }, [data]);

  if (isPending) {
    return <div className="flex h-screen items-center justify-center">Loading your learning graph...</div>;
  }

  if (error) {
    return <div>Error: {error.message}</div>;
  }
//Center the graph on the page and set a dark background color that matches the canvas. The padding ensures that the graph doesn't touch the edges of the screen, providing a better visual experience.
  return (
   <div className="flex justify-content w-screen h-screen items-center justify-center p-4">
      <HomeGraph graphData={rawData} />
    </div>
  );
}

