const graphDataMemo = useMemo(() => {
    const nodesMap = new Map();
    const linksMap = new Map();

    // Guard against missing api response
    if (!rawData || !Array.isArray(rawData)) return { nodes: [], links: [] };

    rawData.forEach((item) => {
      const pathArray = item.path;
      if (!pathArray || pathArray.length < 5) return;

      // 1. Destructure the exact array positions
      const userRaw = pathArray[0];
      const relRead = pathArray[1];
      const bookRaw = pathArray[2];
      const relGenre = pathArray[3];
      const genreRaw = pathArray[4];

      // 2. Build string keys to prevent ID collisions (e.g., if userId and bookId share an index)
      const userGraphId = `user_${userRaw.userId}`;
      const bookGraphId = `book_${bookRaw.bookId}`;
      const genreGraphId = `genre_${genreRaw.genre_id}`;

      // 3. Insert User Node
      if (!nodesMap.has(userGraphId)) {
        nodesMap.set(userGraphId, {
          id: userGraphId,
          type: 'User',
          name: `${userRaw.firstName} ${userRaw.lastName}`,
          val: 10, // Visually larger central hub node
          ...userRaw,
        });
      }

      // 4. Insert Book Node
      if (!nodesMap.has(bookGraphId)) {
        nodesMap.set(bookGraphId, {
          id: bookGraphId,
          type: 'Book',
          name: bookRaw.title,
          val: 6, // Medium node size
          ...bookRaw,
        });
      }

      // 5. Insert Genre Node
      if (!nodesMap.has(genreGraphId)) {
        nodesMap.set(genreGraphId, {
          id: genreGraphId,
          type: 'Genre',
          name: genreRaw.genre,
          val: 4, // Smaller outer leaf nodes
          ...genreRaw,
        });
      }

      // 6. Connect User -> Book (:READ link)
      const readLinkId = `${userGraphId}-${bookGraphId}`;
      if (!linksMap.has(readLinkId)) {
        linksMap.set(readLinkId, {
          id: readLinkId,
          source: userGraphId,
          target: bookGraphId,
          type: relRead,
        });
      }

      // 7. Connect Book -> Genre (:IN_GENRE link)
      const genreLinkId = `${bookGraphId}-${genreGraphId}`;
      if (!linksMap.has(genreLinkId)) {
        linksMap.set(genreLinkId, {
          id: genreLinkId,
          source: bookGraphId,
          target: genreGraphId,
          type: relGenre,
        });
      }
    });

    return {
      nodes: Array.from(nodesMap.values()),
      links: Array.from(linksMap.values()),
    };
}, [rawData]);

return (
    /* 
      TAILWIND CENTERING WRAPPER:
      - flex h-screen w-screen: Spans full screen viewport dimensions
      - items-center justify-center: Centers the child element vertically and horizontally
      - bg-neutral-950: Deep background color matching the canvas
    */
    <div className="flex h-screen w-screen items-center justify-center bg-neutral-950 p-4">
      
      {/* 
        GRAPH CONTAINER BOX:
        - w-full h-full max-w-5xl max-h-[80vh]: Centers a beautiful bounded container card
        - border border-neutral-800 rounded-xl: Elegant clean modern card frame boundaries
        - overflow-hidden shadow-2xl: Prevents canvas canvas bleeding and softens shadows
      */}
      <div 
        className="relative h-full w-full max-h-[85vh] max-w-6xl overflow-hidden rounded-xl border border-neutral-800 bg-[#111111] shadow-2xl"
      >
        <ForceGraph2D 
          ref={graphRef}
          graphData={graphDataMemo}
          backgroundColor="#111111"
          
          // CRITICAL: Feed dynamic layout numbers directly to canvas element engine
          width={800}
          height={600}

          // Node Customizations mapped from Neo4j properties
          nodeId="id"
          nodeLabel={(node) => `[${node.label}] ${node.name}`} 
          
          // 1. Core Custom Canvas Engine Logic for Visible Labels
          nodeCanvasObject={(node, ctx, globalScale) => {
            const label = node.name;
            const fontSize = 13 / globalScale; 
            
            const radius = Math.sqrt(node.val || 4) * 2; 

            // A. Draw Node Base Circle
            ctx.beginPath();
            ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI, false);
            
            if (node.type === 'User') ctx.fillStyle = '#EF4444';       
            else if (node.type === 'Book') ctx.fillStyle = '#10B981';  
            else if (node.type === 'Genre') ctx.fillStyle = '#3B82F6'; 
            else ctx.fillStyle = '#9CA3AF';                            
            ctx.fill();

            // B. Draw crisp border ring around the circle
            ctx.lineWidth = 1.5 / globalScale;
            ctx.strokeStyle = '#FFFFFF';
            ctx.stroke();

            // C. Text Context Parameters
            ctx.font = `${fontSize}px Sans-Serif`;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'top';

            // D. Drop Shadow Effect for Maximum Contrast against Background
            ctx.fillStyle = 'rgba(17, 17, 17, 0.85)'; 
            ctx.fillText(label, node.x + 1, node.y + radius + 4 + 1);
            ctx.fillText(label, node.x - 1, node.y + radius + 4 + 1);

            // E. Foreground Primary Label
            ctx.fillStyle = '#FFFFFF'; 
            ctx.fillText(label, node.x, node.y + radius + 4); 
          }}

          // 2. Click Boundary Map
          nodePointerAreaPaint={(node, color, ctx) => {
            const radius = Math.sqrt(node.val || 4) * 2;
            ctx.beginPath();
            ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI, false);
            ctx.fillStyle = color;
            ctx.fill();
          }}
          
          // Link Customizations mapped from Neo4j properties
          linkWidth={1.5}
          linkLabel={(link) => link.type} 
          linkDirectionalArrowLength={4}  
          linkDirectionalArrowRelPos={1}  
          linkColor={(link) => {
            if (link.type === 'READ') return '#10B981';     
            if (link.type === 'IN_GENRE') return '#3B82F6';  
            return '#9CA3AF';                                
          }}
          
          // Directional Particles
          linkDirectionalParticles={2}
          linkDirectionalParticleSpeed={0.005}
          linkDirectionalParticleColor={(link) => link.type === 'READ' ? '#A7F3D0' : '#93C5FD'} 
        />
      </div>
    </div>
  );