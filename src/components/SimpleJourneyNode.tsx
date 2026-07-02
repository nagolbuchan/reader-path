import { memo } from 'react';
import { Handle, Position } from '@xyflow/react';

interface SimpleJourneyNodeProps {
  id: string;
  data: {
    type: 'User' | 'Book' | 'Genre' | string;
    name: string;
    expandedNodeIds?: string[];
  };
}

export const SimpleJourneyNode = memo(({ id, data }: SimpleJourneyNodeProps) => {
    const { type, name, expandedNodeIds = [] } = data;
    const isActive = expandedNodeIds.includes(id);

    const headerThemes = {
      User: 'bg-rose-600 text-white border-rose-700',
      Book: 'bg-cyan-600 text-slate-950 border-cyan-700 font-semibold',
      Genre: 'bg-fuchsia-600 text-white border-fuchsia-700'
    }[type as 'User' | 'Book' | 'Genre'] || 'bg-slate-600 text-white';

    const glowColors = {
      User: { border: '#f43f5e', shadow: '0 0 16px rgba(244, 63, 94, 0.6)' },
      Book: { border: '#06b6d4', shadow: '0 0 16px rgba(6, 182, 212, 0.6)' },
      Genre: { border: '#d946ef', shadow: '0 0 16px rgba(217, 70, 239, 0.6)' }
    }[type as 'User' | 'Book' | 'Genre'] || { border: '#0ea5e9', shadow: '0 0 16px rgba(14, 165, 233, 0.5)' };

    return (
        <div 
          className="flex flex-col items-stretch select-none relative shadow-lg hover:shadow-xl transition-all duration-200 cursor-pointer overflow-hidden"
          style={{ 
            width: '150px', 
            maxWidth: '150px', 
            minHeight: '90px',
            backgroundColor: '#ffffff', 
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
});

SimpleJourneyNode.displayName = 'SimpleJourneyNode';
