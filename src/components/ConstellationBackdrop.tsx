import { useEffect, useRef } from 'react';

type Particle = {
  x: number;
  y: number;
  vx: number;
  vy: number;
  r: number;
  alpha: number;
};

const GOLD = '196, 165, 116';
const HIGHLIGHT = '232, 213, 181';
const LINK_DIST = 140;
const MAX_LINKS_PER_FRAME = 180;

function prefersReducedMotion(): boolean {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

function createParticles(width: number, height: number, count: number): Particle[] {
  const cx = width * 0.5;
  const cy = height * 0.48;
  const particles: Particle[] = [];

  for (let i = 0; i < count; i++) {
    // Start tight so the outward drift reads as expansion, not collapse
    const angle = Math.random() * Math.PI * 2;
    const radius = Math.pow(Math.random(), 0.85) * Math.min(width, height) * 0.16;
    const x = cx + Math.cos(angle) * radius + (Math.random() - 0.5) * 18;
    const y = cy + Math.sin(angle) * radius * 0.72 + (Math.random() - 0.5) * 18;
    const dx = x - cx;
    const dy = y - cy;
    const dist = Math.hypot(dx, dy) || 1;
    const outward = 0.06 + Math.random() * 0.12;
    particles.push({
      x,
      y,
      vx: (dx / dist) * outward + (Math.random() - 0.5) * 0.06,
      vy: (dy / dist) * outward + (Math.random() - 0.5) * 0.06,
      r: 0.6 + Math.random() * 1.8,
      alpha: 0.25 + Math.random() * 0.55,
    });
  }
  return particles;
}

function drawStaticField(
  ctx: CanvasRenderingContext2D,
  width: number,
  height: number,
  particles: Particle[]
) {
  ctx.clearRect(0, 0, width, height);
  // A few fixed links for a calm constellation
  for (let i = 0; i < particles.length; i++) {
    for (let j = i + 1; j < particles.length; j++) {
      const a = particles[i];
      const b = particles[j];
      const dx = a.x - b.x;
      const dy = a.y - b.y;
      const dist = Math.hypot(dx, dy);
      if (dist < LINK_DIST * 0.75 && (i + j) % 7 === 0) {
        const t = 1 - dist / (LINK_DIST * 0.75);
        ctx.strokeStyle = `rgba(${GOLD}, ${0.08 + t * 0.12})`;
        ctx.lineWidth = 0.6;
        ctx.beginPath();
        ctx.moveTo(a.x, a.y);
        ctx.lineTo(b.x, b.y);
        ctx.stroke();
      }
    }
  }
  for (const p of particles) {
    ctx.fillStyle = `rgba(${HIGHLIGHT}, ${p.alpha * 0.7})`;
    ctx.beginPath();
    ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
    ctx.fill();
  }
}

export function ConstellationBackdrop() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let particles: Particle[] = [];
    let raf = 0;
    let width = 0;
    let height = 0;
    let running = true;
    const reduced = prefersReducedMotion();

    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      width = window.innerWidth;
      height = window.innerHeight;
      canvas.width = Math.floor(width * dpr);
      canvas.height = Math.floor(height * dpr);
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

      const count = width < 640 ? 42 : width < 1024 ? 64 : 80;
      particles = createParticles(width, height, count);
      if (reduced) {
        drawStaticField(ctx, width, height, particles);
      }
    };

    const step = () => {
      if (!running || reduced) return;

      ctx.clearRect(0, 0, width, height);

      const cx = width * 0.5;
      const cy = height * 0.48;

      const maxRadius = Math.min(width, height) * 0.52;

      for (const p of particles) {
        const dx = p.x - cx;
        const dy = p.y - cy;
        const dist = Math.hypot(dx, dy) || 1;

        // Gentle outward push — galaxy expands instead of collapsing
        p.vx += (dx / dist) * 0.0009;
        p.vy += (dy / dist) * 0.0009;
        // Soft drift noise
        p.vx += (Math.random() - 0.5) * 0.003;
        p.vy += (Math.random() - 0.5) * 0.003;
        // Light damp so motion stays slow and readable
        p.vx *= 0.997;
        p.vy *= 0.997;
        // Clamp speed
        const speed = Math.hypot(p.vx, p.vy);
        if (speed > 0.42) {
          p.vx = (p.vx / speed) * 0.42;
          p.vy = (p.vy / speed) * 0.42;
        }

        p.x += p.vx;
        p.y += p.vy;

        // Past the outer halo: reseed near center with fresh outward velocity
        // so expansion continues without emptying the field
        if (dist > maxRadius) {
          const angle = Math.random() * Math.PI * 2;
          const radius = Math.random() * Math.min(width, height) * 0.08;
          p.x = cx + Math.cos(angle) * radius;
          p.y = cy + Math.sin(angle) * radius * 0.72;
          const outward = 0.08 + Math.random() * 0.1;
          p.vx = Math.cos(angle) * outward + (Math.random() - 0.5) * 0.04;
          p.vy = Math.sin(angle) * outward + (Math.random() - 0.5) * 0.04;
        }
      }

      let links = 0;
      for (let i = 0; i < particles.length && links < MAX_LINKS_PER_FRAME; i++) {
        for (let j = i + 1; j < particles.length && links < MAX_LINKS_PER_FRAME; j++) {
          const a = particles[i];
          const b = particles[j];
          const dx = a.x - b.x;
          const dy = a.y - b.y;
          const dist = Math.hypot(dx, dy);
          if (dist >= LINK_DIST) continue;

          const t = 1 - dist / LINK_DIST;
          ctx.strokeStyle = `rgba(${GOLD}, ${0.04 + t * 0.22})`;
          ctx.lineWidth = 0.5 + t * 0.6;
          ctx.beginPath();
          ctx.moveTo(a.x, a.y);
          ctx.lineTo(b.x, b.y);
          ctx.stroke();
          links += 1;
        }
      }

      for (const p of particles) {
        const glow = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.r * 4);
        glow.addColorStop(0, `rgba(${HIGHLIGHT}, ${p.alpha * 0.35})`);
        glow.addColorStop(1, `rgba(${GOLD}, 0)`);
        ctx.fillStyle = glow;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r * 4, 0, Math.PI * 2);
        ctx.fill();

        ctx.fillStyle = `rgba(${GOLD}, ${p.alpha})`;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fill();
      }

      raf = requestAnimationFrame(step);
    };

    const onVisibility = () => {
      if (document.hidden) {
        running = false;
        cancelAnimationFrame(raf);
      } else if (!reduced) {
        running = true;
        raf = requestAnimationFrame(step);
      }
    };

    resize();
    window.addEventListener('resize', resize);
    document.addEventListener('visibilitychange', onVisibility);

    if (!reduced) {
      raf = requestAnimationFrame(step);
    }

    return () => {
      running = false;
      cancelAnimationFrame(raf);
      window.removeEventListener('resize', resize);
      document.removeEventListener('visibilitychange', onVisibility);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden
      className="pointer-events-none absolute inset-0 z-0 h-full w-full"
    />
  );
}
