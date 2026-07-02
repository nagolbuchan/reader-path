import { useEffect, useState } from 'react';
import { 
  ReactFlow, 
  Background, 
  Controls, 
  MarkerType,
  useNodesState,
  useEdgesState,
  useReactFlow       
} from '@xyflow/react';
import type { Node, Edge } from '@xyflow/react';
import dagre from '@dagrejs/dagre';
import { SimpleJourneyNode } from './SimpleJourneyNode';

// IMPORTANT: Defined OUTSIDE the function to freeze memory reference addresses.
const nodeTypes = { journeyNode: SimpleJourneyNode };

const NODE_WIDTH = 150;
const NODE_HEIGHT = 90;

interface FlowContentProps {
  graphData: any;
}

export default function FlowContent({ graphData }: FlowContentProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [expandedNodeIds, setExpandedNodeIds] = useState<string[]>([]);
  const { fitBounds, fitView } = useReactFlow();

  useEffect(() => {
    if (!graphData?.nodes?.length || !graphData?.relationships) return;

    const visibleRelationships = graphData.relationships.filter((rel: any) => {
      const sourceNode = graphData.nodes.find((n: any) => n.id === rel.from);
      if (sourceNode?.type === 'User' || sourceNode?.type === 'Book') {
        return expandedNodeIds.includes(rel.from);
      }
      return false;
    });

    const visibleNodes = graphData.nodes.filter((node: any) => {
      if (node.type === 'User') return true;
      return visibleRelationships.some((rel: any) => rel.to === node.id);
    });

    const dagreGraph = new dagre.graphlib.Graph();
    dagreGraph.setDefaultEdgeLabel(() => ({}));
    dagreGraph.setGraph({ rankdir: 'LR', nodesep: 40, ranksep: 80 });

    visibleNodes.forEach((node: any) => {
      dagreGraph.setNode(node.id, { width: NODE_WIDTH, height: NODE_HEIGHT });
    });

    visibleRelationships.forEach((rel: any) => {
      dagreGraph.setEdge(rel.from, rel.to);
    });

    dagre.layout(dagreGraph);

    const rfNodes: Node[] = visibleNodes.map((node: any) => {
      const dagreNode = dagreGraph.node(node.id);
      return {
        id: node.id,
        type: 'journeyNode',
        data: { 
          type: node.type, 
          name: node.label,
          expandedNodeIds 
        },
        position: {
          x: dagreNode.x - NODE_WIDTH / 2,
          y: dagreNode.y - NODE_HEIGHT / 2,
        },
      };
    });

    const rfEdges: Edge[] = visibleRelationships.map((rel: any, i: number) => {
      const sourceNode = graphData.nodes.find((n: any) => n.id === rel.from);
      const edgeColor = sourceNode?.type === 'User' ? '#f43f5e' : '#c084fc';

      return {
        id: `e${i}`,
        source: rel.from,
        target: rel.to,
        type: 'smoothstep',
        animated: true, 
        style: { stroke: edgeColor, strokeWidth: 2, opacity: 0.9 },
        markerEnd: { type: MarkerType.ArrowClosed, color: edgeColor },
      };
    });

    setNodes(rfNodes);
    setEdges(rfEdges);

    setTimeout(() => {
      if (expandedNodeIds.length > 0) {
        const lastExpandedId = expandedNodeIds[expandedNodeIds.length - 1];
        const branchNodes = rfNodes.filter(n => 
          n.id === lastExpandedId || 
          visibleRelationships.some((r: any) => r.from === lastExpandedId && r.to === n.id)
        );
        
        if (branchNodes.length > 0) {
          const minX = Math.min(...branchNodes.map(n => n.position.x));
          const maxX = Math.max(...branchNodes.map(n => n.position.x)) + NODE_WIDTH;
          const minY = Math.min(...branchNodes.map(n => n.position.y));
          const maxY = Math.max(...branchNodes.map(n => n.position.y)) + NODE_HEIGHT;

          fitBounds(
            { x: minX, y: minY, width: maxX - minX, height: maxY - minY },
            { duration: 800, padding: 0.4 } 
          );
        }
      } else {
        fitView({ duration: 600 });
      }
    }, 50);

  }, [graphData, expandedNodeIds, setNodes, setEdges, fitBounds, fitView]);

  const handleNodeClick = (_: any, node: Node) => {
    const nodeId = node.id;
    const nodeType = node.data.type;

    if (nodeType === 'User' || nodeType === 'Book') {
      setExpandedNodeIds((prevIds) => {
        if (prevIds.includes(nodeId)) {
          if (nodeType === 'User') return [];
          return prevIds.filter(id => id !== nodeId);
        } else {
          if (nodeType === 'Book') {
            const userRootId = prevIds.find(id => {
              const n = graphData.nodes.find((gn: any) => gn.id === id);
              return n?.type === 'User';
            });
            return userRootId ? [userRootId, nodeId] : [nodeId];
          }
          return [...prevIds, nodeId];
        }
      });
    }
  };

  return (
    <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        onNodeClick={handleNodeClick}
        minZoom={0.3}
        maxZoom={2.5}
        >
        <Background color="#334155" gap={24} size={1} opacity={0.15} />
        <Controls position="bottom-right" className="!bg-white !border-slate-200 !text-slate-700 shadow-md" />
    </ReactFlow>
  );
}
