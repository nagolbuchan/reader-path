import React, { useEffect, useState, useMemo } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import neo4j from 'neo4j-driver';

// 1. Initialize the Neo4j Driver (Ideally, move credentials to .env)
const driver = neo4j.driver(
  process.env.REACT_APP_NEO4J_URI || 'neo4j+s://your-database-id.databases.neo4j.io',
  neo4j.auth.basic(
    process.env.REACT_APP_NEO4J_USER || 'neo4j',
    process.env.REACT_APP_NEO4J_PASSWORD || 'your-password'
  )
);

export default function Neo4jGraph() {
  const [rawData, setRawData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // 2. Fetch data from Neo4j on component mount
  useEffect(() => {
    async function fetchGraphData() {
      // Create a session to interact with the database
      const session = driver.session({ database: 'neo4j' });
      
      // Cypher query that returns paths, nodes, or relationships
      const cypherQuery = `
        MATCH path = (n)-[r]->(m) 
        RETURN path 
        LIMIT 50
      `;

      try {
        const result = await session.run(cypherQuery);
        setRawData(result.records);
        setLoading(false);
      } catch (err) {
        console.error('Neo4j Query Error:', err);
        setError(err.message);
        setLoading(false);
      } finally {
        await session.close();
      }
    }

    fetchGraphData();
    
    // Clean up driver connection when application unmounts
    return () => {}; 
  }, []);

  // 3. Parse Neo4j records into react-force-graph format
  const graphData = useMemo(() => {
    const nodesMap = new Map();
    const linksMap = new Map();

    rawData.forEach((record) => {
      // Extract the path object from the row
      const path = record.get('path');
      
      // Process all nodes in this path
      path.segments.forEach((segment) => {
        const startNode = segment.start;
        const endNode = segment.end;
        const relationship = segment.relationship;

        // Map Start Node
        // Note: Neo4j Node IDs can be integers or strings depending on version. 
        // stringifying `.identity` ensures stability.
        const startId = startNode.identity.toString();
        if (!nodesMap.has(startId)) {
          nodesMap.set(startId, {
            id: startId,
            label: startNode.labels[0] || 'Node',       // e.g., 'Person' or 'Movie'
            name: startNode.properties.name || startNode.properties.title || startId,
            ...startNode.properties
          });
        }

        // Map End Node
        const endId = endNode.identity.toString();
        if (!nodesMap.has(endId)) {
          nodesMap.set(endId, {
            id: endId,
            label: endNode.labels[0] || 'Node',
            name: endNode.properties.name || endNode.properties.title || endId,
            ...endNode.properties
          });
        }

        // Map Relationship (Link)
        const relId = relationship.identity.toString();
        if (!linksMap.has(relId)) {
          linksMap.set(relId, {
            id: relId,
            source: startId,   // Must match node ID string
            target: endId,     // Must match node ID string
            type: relationship.type, // e.g., 'ACTED_IN' or 'FRIEND_OF'
            ...relationship.properties
          });
        }
      });
    });

    return {
      nodes: Array.from(nodesMap.values()),
      links: Array.from(linksMap.values()),
    };
  }, [rawData]);

  // Handle Loading & Errors gracefully
  if (loading) return <div style={{ color: '#fff', padding: '20px' }}>Loading graph from Neo4j...</div>;
  if (error) return <div style={{ color: 'red', padding: '20px' }}>Error: {error}</div>;

  return (
    <div style={{ width: '100vw', height: '100vh', background: '#111' }}>
      <ForceGraph2D
        graphData={graphData}
        backgroundColor="#111111"
        
        // Node Customizations mapped from Neo4j properties
        nodeId="id"
        nodeLabel={(node) => `[${node.label}] ${node.name}`} 
        nodeAutoColorBy="label" // Colors nodes differently based on their Neo4j Label
        
        // Link Customizations mapped from Neo4j properties
        linkWidth={1.5}
        linkLabel={(link) => link.type} // Shows relationship type on hover
        linkDirectionalArrowLength={4}  // Visualizes graph directionality
        linkDirectionalArrowRelPos={1}  // Places arrow at the target node edge
      />
    </div>
  );
}
