import { useEffect, useState } from 'react';
import { 
  ReactFlow, 
  Background, 
  Controls, 
  MarkerType,
  useNodesState,
  useEdgesState,
  Position, 
  Handle,
  ReactFlowProvider,
  useReactFlow       
} from '@xyflow/react';
import type { Node, Edge } from '@xyflow/react';
import dagre from '@dagrejs/dagre';
import '@xyflow/react/dist/style.css';

const SimpleJourneyNode = ({ id, data }: { id: string; data: any }) => {
    const { type, name, expandedNodeIds = [] } = data;
    
    // 1. DETERMINE IF THIS NODE IS CURRENTLY ACTIVE/SELECTED
    const isActive = expandedNodeIds.includes(id);

    const headerThemes = {
      User: 'bg-rose-600 text-white border-rose-700',
      Book: 'bg-cyan-600 text-slate-950 border-cyan-700 font-semibold',
      Genre: 'bg-fuchsia-600 text-white border-fuchsia-700'
    }[type as 'User' | 'Book' | 'Genre'] || 'bg-slate-600 text-white';

    // 2. DYNAMIC ACTIVE GLOW CSS CONFIGURATIONS
    const glowColors = {
      User: { border: '#f43f5e', shadow: '0 0 16px rgba(244, 63, 94, 0.6)' },
      Book: { border: '#06b6d4', shadow: '0 0 16px rgba(6, 182, 212, 0.6)' },
      Genre: { border: '#d946ef', shadow: '0 0 16px rgba(217, 70, 239, 0.6)' }
    }[type as 'User' | 'Book' | 'Genre'] || { border: '#0ea5e9', shadow: '0 0 16px rgba(14, 165, 233, 0.5)' };

    return (
        <div 
          className="flex flex-col items-stretch select-none relative shadow-lg hover:shadow-xl transition-all duration-300 cursor-pointer overflow-hidden"
          style={{ 
            width: '150px', 
            maxWidth: '150px', 
            minHeight: '90px',
            backgroundColor: '#ffffff', 
            // Swaps out regular border/shadow layout configurations for glowing versions when active
            border: isActive ? `2px solid ${glowColors.border}` : '2px solid #cbd5e1', 
            borderRadius: '8px',         
            boxShadow: isActive ? glowColors.shadow : '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
            transform: isActive ? 'scale(1.02)' : 'scale(1)',
          }}
        >
        
        {type !== 'User' && (
            <Handle 
              type="target" 
              position={Position.Left} 
              style={{ 
                background: isActive ? glowColors.border : '#475569', 
                width: 8, 
                height: 8, 
                left: -5, 
                border: '1px solid #fff',
                boxShadow: isActive ? `0 0 8px ${glowColors.border}` : '0 1px 3px rgba(0,0,0,0.3)',
                transition: 'all 0.3s ease'
              }} 
            />
        )}

        <div className={`text-[9px] font-mono tracking-widest uppercase px-3 py-1.5 border-b border-slate-200 text-center ${headerThemes}`}>
            {type}
        </div>
        
        <div className="flex-1 flex items-center justify-center p-3" style={{ backgroundColor: '#f8fafc' }}>
            <div 
              className="text-xs font-semibold text-slate-800 text-center w-full break-words"
              style={{
                display: '-webkit-box',
                WebkitLineClamp: 3,
                WebkitBoxOrient: 'vertical',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                lineHeight: '1.15rem',
                maxHeight: '3.45rem'
              }}
            >
                {name || 'SYSTEM_NODE'}
            </div>
        </div>

        {type !== 'Genre' && (
            <Handle 
              type="source" 
              position={Position.Right} 
              style={{ 
                background: isActive ? glowColors.border : '#475569', 
                width: 8, 
                height: 8, 
                right: -5, 
                border: '1px solid #fff',
                boxShadow: isActive ? `0 0 8px ${glowColors.border}` : '0 1px 3px rgba(0,0,0,0.3)',
                transition: 'all 0.3s ease'
              }} 
            />
        )}
        </div>
    );
};

const nodeTypes = { journeyNode: SimpleJourneyNode };

const NODE_WIDTH = 150;
const NODE_HEIGHT = 90;

function FlowContent({ graphData }: { graphData: any }) {
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
          // 3. PASS THE TRACKING STATE INTO THE NODE COMPONENT DATA
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

export default function HomeGraph({ graphData }: { graphData: any }) {
  return (
    <div className="w-screen h-screen bg-[#0b0f19] flex items-center justify-center p-4 overflow-hidden relative">
        <div className="absolute w-[500px] h-[500px] rounded-full bg-cyan-500/5 blur-[120px] top-1/4 left-1/4 pointer-events-none" />
        <div className="absolute w-[400px] h-[400px] rounded-full bg-purple-500/5 blur-[100px] bottom-1/3 right-1/4 pointer-events-none" />

        <div 
          className="w-[1200px] h-[800px] max-w-full max-h-full border border-slate-800 rounded-2xl overflow-hidden bg-slate-950/20 backdrop-blur-xl shadow-2xl relative"
          style={{ width: '100vw', height: '100vh', maxWidth: '1200px', maxHeight: '800px' }}
        >
          <ReactFlowProvider>
            <FlowContent graphData={graphData} />
          </ReactFlowProvider>
      </div>
    </div>
  );
}
