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
  useReactFlow,
} from '@xyflow/react';
import type { Node, Edge } from '@xyflow/react';
import dagre from '@dagrejs/dagre';
import '@xyflow/react/dist/style.css';
import type { GraphPayload } from '../lib/api';

const EXPANDABLE_TYPES = new Set(['User', 'Course', 'Module', 'Book']);

const headerThemes: Record<string, string> = {
  User: 'bg-rose-600 text-white border-rose-700',
  Course: 'bg-indigo-600 text-white border-indigo-700',
  Module: 'bg-violet-600 text-white border-violet-700',
  Book: 'bg-cyan-600 text-slate-950 border-cyan-700 font-semibold',
  Assignment: 'bg-amber-600 text-white border-amber-700',
  Topic: 'bg-emerald-600 text-white border-emerald-700',
  Author: 'bg-fuchsia-600 text-white border-fuchsia-700',
};

const glowColors: Record<string, { border: string; shadow: string }> = {
  User: { border: '#f43f5e', shadow: '0 0 16px rgba(244, 63, 94, 0.6)' },
  Course: { border: '#6366f1', shadow: '0 0 16px rgba(99, 102, 241, 0.6)' },
  Module: { border: '#8b5cf6', shadow: '0 0 16px rgba(139, 92, 246, 0.6)' },
  Book: { border: '#06b6d4', shadow: '0 0 16px rgba(6, 182, 212, 0.6)' },
  Assignment: { border: '#d97706', shadow: '0 0 16px rgba(217, 119, 6, 0.6)' },
  Topic: { border: '#059669', shadow: '0 0 16px rgba(5, 150, 105, 0.6)' },
  Author: { border: '#d946ef', shadow: '0 0 16px rgba(217, 70, 239, 0.6)' },
};

const SimpleJourneyNode = ({ id, data }: { id: string; data: any }) => {
  const { type, name, expandedNodeIds = [] } = data;
  const isActive = expandedNodeIds.includes(id);
  const theme = headerThemes[type] || 'bg-slate-600 text-white';
  const glow = glowColors[type] || {
    border: '#0ea5e9',
    shadow: '0 0 16px rgba(14, 165, 233, 0.5)',
  };

  return (
    <div
      className="flex flex-col items-stretch select-none relative shadow-lg hover:shadow-xl transition-all duration-300 cursor-pointer overflow-hidden"
      style={{
        width: '150px',
        maxWidth: '150px',
        minHeight: '90px',
        backgroundColor: '#ffffff',
        border: isActive ? `2px solid ${glow.border}` : '2px solid #cbd5e1',
        borderRadius: '8px',
        boxShadow: isActive
          ? glow.shadow
          : '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
        transform: isActive ? 'scale(1.02)' : 'scale(1)',
      }}
    >
      {type !== 'User' && (
        <Handle
          type="target"
          position={Position.Left}
          style={{
            background: isActive ? glow.border : '#475569',
            width: 8,
            height: 8,
            left: -5,
            border: '1px solid #fff',
          }}
        />
      )}

      <div
        className={`text-[9px] font-mono tracking-widest uppercase px-3 py-1.5 border-b border-slate-200 text-center ${theme}`}
      >
        {type}
      </div>

      <div
        className="flex-1 flex items-center justify-center p-3"
        style={{ backgroundColor: '#f8fafc' }}
      >
        <div
          className="text-xs font-semibold text-slate-800 text-center w-full break-words"
          style={{
            display: '-webkit-box',
            WebkitLineClamp: 3,
            WebkitBoxOrient: 'vertical',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            lineHeight: '1.15rem',
            maxHeight: '3.45rem',
          }}
        >
          {name || 'Node'}
        </div>
      </div>

      {EXPANDABLE_TYPES.has(type) && (
        <Handle
          type="source"
          position={Position.Right}
          style={{
            background: isActive ? glow.border : '#475569',
            width: 8,
            height: 8,
            right: -5,
            border: '1px solid #fff',
          }}
        />
      )}
    </div>
  );
};

const nodeTypes = { journeyNode: SimpleJourneyNode };

const NODE_WIDTH = 150;
const NODE_HEIGHT = 90;

function FlowContent({ graphData }: { graphData: GraphPayload }) {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [expandedNodeIds, setExpandedNodeIds] = useState<string[]>([]);
  const { fitBounds, fitView } = useReactFlow();

  useEffect(() => {
    if (!graphData?.nodes?.length || !graphData?.relationships) return;

    const visibleRelationships = graphData.relationships.filter((rel) => {
      const sourceNode = graphData.nodes.find((n) => n.id === rel.from);
      if (!sourceNode) return false;
      if (sourceNode.type === 'User') {
        return expandedNodeIds.includes(rel.from);
      }
      if (EXPANDABLE_TYPES.has(sourceNode.type)) {
        return expandedNodeIds.includes(rel.from);
      }
      return false;
    });

    const visibleNodes = graphData.nodes.filter((node) => {
      if (node.type === 'User') return true;
      return visibleRelationships.some((rel) => rel.to === node.id);
    });

    const dagreGraph = new dagre.graphlib.Graph();
    dagreGraph.setDefaultEdgeLabel(() => ({}));
    dagreGraph.setGraph({ rankdir: 'LR', nodesep: 40, ranksep: 80 });

    visibleNodes.forEach((node) => {
      dagreGraph.setNode(node.id, { width: NODE_WIDTH, height: NODE_HEIGHT });
    });

    visibleRelationships.forEach((rel) => {
      dagreGraph.setEdge(rel.from, rel.to);
    });

    dagre.layout(dagreGraph);

    const rfNodes: Node[] = visibleNodes.map((node) => {
      const dagreNode = dagreGraph.node(node.id);
      return {
        id: node.id,
        type: 'journeyNode',
        data: {
          type: node.type,
          name: node.label,
          expandedNodeIds,
        },
        position: {
          x: dagreNode.x - NODE_WIDTH / 2,
          y: dagreNode.y - NODE_HEIGHT / 2,
        },
      };
    });

    const edgeColorByType: Record<string, string> = {
      User: '#f43f5e',
      Course: '#6366f1',
      Module: '#8b5cf6',
      Book: '#06b6d4',
    };

    const rfEdges: Edge[] = visibleRelationships.map((rel, i) => {
      const sourceNode = graphData.nodes.find((n) => n.id === rel.from);
      const edgeColor = edgeColorByType[sourceNode?.type || ''] || '#c084fc';

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
        const branchNodes = rfNodes.filter(
          (n) =>
            n.id === lastExpandedId ||
            visibleRelationships.some(
              (r) => r.from === lastExpandedId && r.to === n.id
            )
        );

        if (branchNodes.length > 0) {
          const minX = Math.min(...branchNodes.map((n) => n.position.x));
          const maxX =
            Math.max(...branchNodes.map((n) => n.position.x)) + NODE_WIDTH;
          const minY = Math.min(...branchNodes.map((n) => n.position.y));
          const maxY =
            Math.max(...branchNodes.map((n) => n.position.y)) + NODE_HEIGHT;

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

  const handleNodeClick = (_: unknown, node: Node) => {
    const nodeId = node.id;
    const nodeType = String(node.data.type);

    if (!EXPANDABLE_TYPES.has(nodeType)) return;

    setExpandedNodeIds((prevIds) => {
      if (prevIds.includes(nodeId)) {
        // Collapse this node and its descendants in the expansion chain
        const idx = prevIds.indexOf(nodeId);
        return prevIds.slice(0, idx);
      }

      // Keep ancestor chain: User -> Course -> Module -> Book
      const typeOrder = ['User', 'Course', 'Module', 'Book'];
      const order = typeOrder.indexOf(nodeType);
      const kept = prevIds.filter((id) => {
        const n = graphData.nodes.find((gn) => gn.id === id);
        if (!n) return false;
        const nOrder = typeOrder.indexOf(n.type);
        return nOrder >= 0 && nOrder < order;
      });
      return [...kept, nodeId];
    });
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
      <Background color="#334155" gap={24} size={1} />
      <Controls
        position="bottom-right"
        className="!bg-white !border-slate-200 !text-slate-700 shadow-md"
      />
    </ReactFlow>
  );
}

interface HomeGraphProps {
  graphData: GraphPayload;
  shareUrl?: string;
  onCreateCourse?: () => void;
  onLogout?: () => void;
  readOnly?: boolean;
}

export default function HomeGraph({
  graphData,
  shareUrl,
  onCreateCourse,
  onLogout,
  readOnly = false,
}: HomeGraphProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    if (!shareUrl) return;
    await navigator.clipboard.writeText(shareUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="w-screen h-screen bg-[#0b0f19] flex items-center justify-center p-4 overflow-hidden relative">
      <div className="absolute w-[500px] h-[500px] rounded-full bg-cyan-500/5 blur-[120px] top-1/4 left-1/4 pointer-events-none" />
      <div className="absolute w-[400px] h-[400px] rounded-full bg-purple-500/5 blur-[100px] bottom-1/3 right-1/4 pointer-events-none" />

      <div className="absolute top-6 left-6 right-6 z-20 flex items-center justify-between gap-3">
        <div className="text-white font-semibold tracking-tight">ReaderPath</div>
        <div className="flex items-center gap-2">
          {shareUrl && (
            <button
              onClick={handleCopy}
              className="px-3 py-2 text-xs rounded-xl bg-slate-800 text-slate-200 border border-slate-700 hover:bg-slate-700"
            >
              {copied ? 'Link copied' : 'Copy share link'}
            </button>
          )}
          {!readOnly && onCreateCourse && (
            <button
              onClick={onCreateCourse}
              className="px-3 py-2 text-xs rounded-xl bg-white text-black font-medium hover:bg-zinc-200"
            >
              New course
            </button>
          )}
          {!readOnly && onLogout && (
            <button
              onClick={onLogout}
              className="px-3 py-2 text-xs rounded-xl bg-slate-800 text-slate-200 border border-slate-700 hover:bg-slate-700"
            >
              Sign out
            </button>
          )}
        </div>
      </div>

      <div
        className="w-[1200px] h-[800px] max-w-full max-h-full border border-slate-800 rounded-2xl overflow-hidden bg-slate-950/20 backdrop-blur-xl shadow-2xl relative"
        style={{
          width: '100vw',
          height: '100vh',
          maxWidth: '1200px',
          maxHeight: '800px',
        }}
      >
        <ReactFlowProvider>
          <FlowContent graphData={graphData} />
        </ReactFlowProvider>
      </div>
    </div>
  );
}
